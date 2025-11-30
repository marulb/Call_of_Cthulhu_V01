<template>
  <div class="active-turn">
    <div class="list-header">
      <h3>Scene - Active Turn</h3>
      <div class="header-actions">
        <button v-if="!showNewForm" @click="startNewAction" class="btn-add">+ New Action</button>
        <button @click="emit('close')" class="btn-close" title="Close">✕</button>
      </div>
    </div>

    <div class="actions-container">
      <!-- New Action Form (simplified - just pick character) -->
      <div v-if="showNewForm" class="action-form new-action-prompt">
        <div class="form-header">
          <h4>New Action</h4>
          <button @click="cancelNewAction" class="btn-icon btn-cancel" title="Cancel">✕</button>
        </div>
        <div class="form-field">
          <label>Select Character</label>
          <select v-model="newAction.character_id" @change="createEmptyAction">
            <option value="">Select character...</option>
            <option v-for="char in characters" :key="char.id" :value="char.id">
              {{ char.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Existing Action Drafts -->
      <div class="drafts-list">
        <div
          v-for="(draft, index) in sortedDrafts"
          :key="draft.id"
          class="draft-item"
          :class="{
            ready: draft.ready,
            editing: !draft.ready && draft.player_id === currentPlayerId,
            'is-mine': draft.player_id === currentPlayerId
          }"
          :draggable="canReorderDrafts && draft.player_id === currentPlayerId && draft.ready"
          @dragstart="handleDragStart(index)"
          @dragover.prevent
          @drop="handleDrop(index)"
        >
          <div class="draft-header">
            <div class="draft-character">
              {{ getCharacterName(draft.character_id) }}
              <span v-if="isCharacterAI(draft.character_id)" class="ai-badge" title="AI-controlled character">✦</span>
            </div>
            <div class="draft-controls" v-if="draft.player_id === currentPlayerId">
              <button 
                v-if="isCharacterAI(draft.character_id) && !draft.ready"
                @click="generateAIAction(draft)"
                class="btn-icon btn-ai-generate"
                :class="{ generating: generatingActionFor === draft.id }"
                :disabled="generatingActionFor !== null"
                title="Generate AI action"
              >
                {{ generatingActionFor === draft.id ? '⏳' : '⋆˙⟡' }}
              </button>
              <button 
                @click="toggleReady(draft)" 
                class="btn-icon btn-toggle-ready"
                :class="{ active: draft.ready }"
                :title="draft.ready ? 'Edit action' : 'Mark as ready'"
              >
                ✓
              </button>
              <button 
                @click="deleteDraft(draft)" 
                class="btn-icon btn-remove"
                title="Remove action"
              >
                ✕
              </button>
            </div>
            <div class="draft-meta" v-else>
              <span class="draft-player">{{ getPlayerName(draft.player_id) }}</span>
              <span v-if="draft.ready" class="ready-badge">✓ Ready</span>
            </div>
          </div>

          <!-- Editable content (when not ready and is mine) -->
          <div v-if="!draft.ready && draft.player_id === currentPlayerId" class="draft-content-editable">
            <div class="form-field">
              <label>Speak</label>
              <textarea
                :value="draft.speak"
                @input="updateDraftField(draft, 'speak', ($event.target as HTMLTextAreaElement).value)"
                placeholder="What your character says..."
                rows="2"
              ></textarea>
            </div>
            <div class="form-field">
              <label>Act</label>
              <textarea
                :value="draft.act"
                @input="updateDraftField(draft, 'act', ($event.target as HTMLTextAreaElement).value)"
                placeholder="What your character does..."
                rows="2"
              ></textarea>
            </div>
            <div class="form-field-row">
              <div class="form-field">
                <label>Demeanor</label>
                <input
                  :value="draft.appearance"
                  @input="updateDraftField(draft, 'appearance', ($event.target as HTMLInputElement).value)"
                  type="text"
                  placeholder="What others see (body language, expression)..."
                />
              </div>
              <div class="form-field">
                <label>Emotion</label>
                <input
                  :value="draft.emotion"
                  @input="updateDraftField(draft, 'emotion', ($event.target as HTMLInputElement).value)"
                  type="text"
                  placeholder="Emotional state..."
                />
              </div>
            </div>
            <div class="form-field">
              <label>OOC Note</label>
              <textarea
                :value="draft.ooc"
                @input="updateDraftField(draft, 'ooc', ($event.target as HTMLTextAreaElement).value)"
                placeholder="Notes for the Keeper..."
                rows="1"
              ></textarea>
            </div>
          </div>

          <!-- Read-only content (when ready or not mine) -->
          <div v-else class="draft-content">
            <div v-if="draft.speak" class="content-section">
              <strong>Speak:</strong> "{{ draft.speak }}"
            </div>
            <div v-if="draft.act" class="content-section">
              <strong>Act:</strong> {{ draft.act }}
            </div>
            <div v-if="draft.appearance" class="content-section small">
              <em>Demeanor:</em> {{ draft.appearance }}
            </div>
            <div v-if="draft.emotion" class="content-section small">
              <em>Emotion:</em> {{ draft.emotion }}
            </div>
            <div v-if="draft.ooc" class="content-section ooc">
              <em>OOC:</em> {{ draft.ooc }}
            </div>
            <!-- Show placeholder if no content yet -->
            <div v-if="!draft.speak && !draft.act && draft.player_id !== currentPlayerId" class="content-section empty">
              <em>Preparing action...</em>
            </div>
          </div>
        </div>

        <div v-if="sortedDrafts.length === 0 && !showNewForm" class="empty-state">
          <p>No actions yet. Click "+ New Action" to create one.</p>
        </div>
      </div>
    </div>

    <div v-if="sortedDrafts.length > 0" class="list-footer">
      <div class="action-summary">
        {{ readyCount }}/{{ sortedDrafts.length }} actions ready
      </div>
      <button
        v-if="allActionsReady && sortedDrafts.length > 0"
        @click="submitTurn"
        class="btn-submit"
      >
        Submit Turn
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ActionDraft } from '@/types/gameplay'
import { aiAPI } from '@/services/api'

interface Character {
  id: string
  name: string
  ai_controlled?: boolean
  ai_personality?: string
}

interface Player {
  player_id: string
  player_name: string
}

const props = defineProps<{
  drafts: ActionDraft[]
  // characters used for the creation dropdown (usually current player's selected characters)
  characters: Character[]
  // full list of characters in the realm (used to resolve names for actions from other players)
  allCharacters?: Character[]
  players: Player[]
  currentPlayerId: string
  sessionId: string
  sceneId?: string
  campaignId?: string
  turnId?: string
}>()

const emit = defineEmits<{
  createDraft: [draft: Partial<ActionDraft>]
  updateDraft: [draft: ActionDraft]
  deleteDraft: [draftId: string]
  reorderDrafts: [order: string[]]
  submitTurn: []
  dungeonmasterResponse: [response: any]
  close: []
}>()

const showNewForm = ref(false)
const newAction = ref({
  character_id: '',
  speak: '',
  act: '',
  appearance: '',
  emotion: '',
  ooc: ''
})

const draggedIndex = ref<number | null>(null)
const updateDebounceTimers = ref<Record<string, ReturnType<typeof setTimeout>>>({})

const sortedDrafts = computed(() => {
  return [...props.drafts].sort((a, b) => a.order - b.order)
})

const readyCount = computed(() => {
  return props.drafts.filter((d) => d.ready).length
})

const allActionsReady = computed(() => {
  return props.drafts.length > 0 && props.drafts.every((d) => d.ready)
})

const canReorderDrafts = computed(() => {
  return !allActionsReady.value
})

function getCharacterName(characterId: string) {
  // First try the local characters prop (used for the current player's selectable characters)
  const foundLocal = props.characters.find((c) => c.id === characterId)
  if (foundLocal) return foundLocal.name

  // If not found, fall back to the full list of realm characters passed via allCharacters
  if (props.allCharacters) {
    const found = props.allCharacters.find((c) => c.id === characterId)
    if (found) return found.name
  }

  // As a last fallback, return Unknown
  return 'Unknown'
}

function getPlayerName(playerId: string) {
  return props.players.find((p) => p.player_id === playerId)?.player_name || 'Unknown'
}

function isCharacterAI(characterId: string): boolean {
  // Check in allCharacters first (full data)
  if (props.allCharacters) {
    const found = props.allCharacters.find((c) => c.id === characterId)
    if (found) return !!found.ai_controlled
  }
  // Check in local characters
  const foundLocal = props.characters.find((c) => c.id === characterId)
  return !!foundLocal?.ai_controlled
}

const generatingActionFor = ref<string | null>(null)

async function generateAIAction(draft: ActionDraft) {
  if (generatingActionFor.value) return
  
  if (!props.sceneId || !props.sessionId) {
    alert('Scene or session not available. Please try again.')
    return
  }
  
  generatingActionFor.value = draft.id
  try {
    const result = await aiAPI.generateAction({
      character_id: draft.character_id,
      scene_id: props.sceneId,
      session_id: props.sessionId
    })
    
    // Update the draft with generated content
    emit('updateDraft', {
      ...draft,
      speak: result.speak || '',
      act: result.act || '',
      appearance: result.appearance || '',
      emotion: result.emotion || ''
    })
  } catch (error) {
    console.error('Failed to generate AI action:', error)
    alert('Failed to generate AI action. Please try again.')
  } finally {
    generatingActionFor.value = null
  }
}

function startNewAction() {
  showNewForm.value = true
}

function createEmptyAction() {
  if (!newAction.value.character_id) return

  emit('createDraft', {
    session_id: props.sessionId,
    player_id: props.currentPlayerId,
    character_id: newAction.value.character_id,
    speak: '',
    act: '',
    appearance: '',
    emotion: '',
    ooc: '',
    order: props.drafts.length,
    ready: false
  })

  cancelNewAction()
}

function cancelNewAction() {
  showNewForm.value = false
  newAction.value = {
    character_id: '',
    speak: '',
    act: '',
    appearance: '',
    emotion: '',
    ooc: ''
  }
}

function updateDraftField(draft: ActionDraft, field: keyof ActionDraft, value: string) {
  // Debounce updates to avoid too many API calls
  const timerId = `${draft.id}-${field}`
  if (updateDebounceTimers.value[timerId]) {
    clearTimeout(updateDebounceTimers.value[timerId])
  }
  
  updateDebounceTimers.value[timerId] = setTimeout(() => {
    emit('updateDraft', { ...draft, [field]: value })
    delete updateDebounceTimers.value[timerId]
  }, 300)
}

function toggleReady(draft: ActionDraft) {
  emit('updateDraft', { ...draft, ready: !draft.ready })
}

function deleteDraft(draft: ActionDraft) {
  if (confirm('Remove this action?')) {
    emit('deleteDraft', draft.id)
  }
}

function handleDragStart(index: number) {
  draggedIndex.value = index
}

function handleDrop(dropIndex: number) {
  if (draggedIndex.value === null || draggedIndex.value === dropIndex) {
    draggedIndex.value = null
    return
  }

  const newOrder = [...sortedDrafts.value]
  const [draggedItem] = newOrder.splice(draggedIndex.value, 1)
  if (!draggedItem) {
    draggedIndex.value = null
    return
  }
  newOrder.splice(dropIndex, 0, draggedItem)

  emit('reorderDrafts', newOrder.map((d) => d.id))
  draggedIndex.value = null
}

function submitTurn() {
  // all are ready, then submit directly otherwise confirm
  if (!allActionsReady.value && !confirm('Not all players are ready. Do you want to end the turn anyways?')) {
    return
  }
  
  // Check for AI characters with empty actions
  const aiEmptyActions = props.drafts.filter(draft => {
    const isAI = isCharacterAI(draft.character_id)
    const isEmpty = !draft.speak && !draft.act && !draft.appearance && !draft.emotion
    return isAI && isEmpty
  })
  
  if (aiEmptyActions.length > 0) {
    const aiNames = aiEmptyActions.map(d => getCharacterName(d.character_id)).join(', ')
    if (!confirm(`AI characters (${aiNames}) have no actions. Generate actions before submitting?`)) {
      return
    }
  }

  // Emit event to parent - parent handles API calls
  emit('submitTurn')
}
</script>

<style scoped>
/* TODO: Consider adding to base.css:
   --color-accent-ready (for ready/success states)
   --color-accent-danger (for delete/error actions)
   --color-accent-ooc (for OOC notes background)
*/

.active-turn {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-background);
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--vt-c-divider-light-1);
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--vt-c-deep-sea);
  border-bottom: 1px solid var(--color-border);
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--vt-c-white);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-add {
  padding: 6px 12px;
  background: var(--vt-c-ink-green-light);
  color: var(--vt-c-white);
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-add:hover {
  background: var(--vt-c-ink-green);
}

.btn-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--vt-c-white);
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.actions-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* Scrollbar styles for the actions container */
.actions-container {
  scrollbar-color: var(--color-scrollbar-thumb) var(--color-scrollbar-track);
  scrollbar-width: thin;
}

.actions-container::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.actions-container::-webkit-scrollbar-track {
  background: var(--color-scrollbar-track);
}

.actions-container::-webkit-scrollbar-thumb {
  background: var(--color-scrollbar-thumb);
  border-radius: 8px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.actions-container::-webkit-scrollbar-thumb:hover {
  background: var(--color-scrollbar-thumb-hover);
}

.action-form {
  background: var(--color-background-soft);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 2px solid var(--vt-c-ink-green-light);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.form-header h4 {
  margin: 0;
  font-size: 15px;
  color: var(--color-heading);
}

.btn-cancel {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--vt-c-fog);
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-cancel:hover {
  color: var(--color-text);
}

.form-field {
  margin-bottom: 12px;
}

.form-field label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--vt-c-fog);
}

.form-field input,
.form-field textarea,
.form-field select {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  background: var(--color-background);
  color: var(--color-text);
}

.form-field input:focus,
.form-field textarea:focus,
.form-field select:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.btn-primary {
  flex: 1;
  padding: 10px;
  background: var(--vt-c-ink-green-light);
  color: var(--vt-c-white);
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--vt-c-ink-green);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 16px;
  background: var(--color-background-mute);
  color: var(--color-text);
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: var(--color-border);
}

.drafts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.draft-item {
  background: var(--color-background-soft);
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid var(--color-border);
  transition: all 0.2s;
}

.draft-item.ready {
  border-left-color: var(--vt-c-ink-green);
  background: var(--color-background-mute);
}

.draft-item.editing {
  border-left-color: var(--vt-c-ink-green-light);
  background: rgba(84, 138, 113, 0.1);
}

.draft-item.is-mine {
  border-left-color: var(--vt-c-ink-green-light);
}

.draft-item.is-mine.ready {
  border-left-color: var(--vt-c-ink-green);
  background: rgba(84, 138, 113, 0.15);
}

.draft-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.draft-character {
  font-weight: 700;
  color: var(--color-heading);
  font-size: 14px;
}

.draft-controls {
  display: flex;
  gap: 4px;
}

.btn-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-toggle-ready {
  background: var(--color-background-mute);
  color: var(--vt-c-fog);
}

.btn-toggle-ready:hover {
  background: var(--vt-c-ink-green-light);
  color: var(--vt-c-white);
}

.btn-toggle-ready.active {
  background: var(--vt-c-ink-green);
  color: var(--vt-c-white);
}

.btn-ai-generate {
  background: var(--color-background-mute);
  color: var(--vt-c-gold);
  font-size: 12px;
}

.btn-ai-generate:hover {
  background: var(--vt-c-gold);
  color: var(--vt-c-black);
}

.btn-ai-generate.generating {
  animation: pulse 1s infinite;
}

.btn-ai-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.ai-badge {
  margin-left: 4px;
  font-size: 10px;
  opacity: 0.5;
  color: inherit;
}

.btn-remove {
  background: var(--color-background-mute);
  color: var(--vt-c-fog);
}

.btn-remove:hover {
  background: var(--vt-c-metallic-accent);
  color: var(--vt-c-white);
}

.draft-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.draft-player {
  color: var(--vt-c-fog);
}

.ready-badge {
  background: var(--vt-c-ink-green);
  color: var(--vt-c-white);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.draft-content {
  margin-bottom: 8px;
}

.draft-content-editable {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.draft-content-editable .form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.draft-content-editable .form-field label {
  font-size: 11px;
  font-weight: 600;
  color: var(--vt-c-fog);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.draft-content-editable .form-field input,
.draft-content-editable .form-field textarea {
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 13px;
  background: var(--color-background);
  color: var(--color-text);
  resize: vertical;
}

.draft-content-editable .form-field input:focus,
.draft-content-editable .form-field textarea:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.form-field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.content-section {
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--color-text);
}

.content-section.small {
  font-size: 12px;
  color: var(--vt-c-fog);
}

.content-section.ooc {
  background: var(--color-background-mute);
  padding: 6px;
  border-radius: 4px;
  border-left: 2px solid var(--vt-c-metallic-accent);
}

.content-section.empty {
  color: var(--vt-c-fog);
  font-style: italic;
}

.new-action-prompt {
  background: var(--color-background-soft);
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}

.new-action-prompt .form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.new-action-prompt .form-field label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
}

.new-action-prompt .form-field select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  background: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
}

.new-action-prompt .form-field select:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

/* Remove old draft-actions since we use btn-icon now */
.draft-actions {
  display: none;
}

.btn-ready {
  flex: 1;
  padding: 6px 12px;
  background: var(--color-background-mute);
  color: var(--color-text);
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-ready.active {
  background: var(--vt-c-ink-green);
  color: var(--vt-c-white);
}

.btn-ready:hover {
  opacity: 0.8;
}

.btn-delete {
  padding: 6px 12px;
  background: var(--color-background-mute);
  color: var(--vt-c-metallic-accent);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: var(--color-border);
  border-color: var(--vt-c-metallic-accent);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--vt-c-fog);
}

.empty-state p {
  margin: 0;
}

.list-footer {
  padding: 12px 16px;
  background: var(--color-background-soft);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-summary {
  font-size: 13px;
  font-weight: 600;
  color: var(--vt-c-fog);
}

.btn-submit {
  padding: 8px 16px;
  background: var(--vt-c-ink-green);
  color: var(--vt-c-white);
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit:hover {
  background: var(--vt-c-deep-sea);
}
</style>
