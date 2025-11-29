<template>
  <div class="active-turn">
    <div class="list-header">
      <h3>Scene - Active Turn</h3>
      <div class="header-actions">
        <button v-if="!showNewForm" @click="showNewForm = true" class="btn-add">+ New Action</button>
        <button @click="emit('close')" class="btn-close" title="Close">✕</button>
      </div>
    </div>

    <div class="actions-container">
      <!-- New Action Form -->
      <div v-if="showNewForm" class="action-form">
        <div class="form-header">
          <h4>New Action</h4>
          <button @click="cancelNewAction" class="btn-cancel">✕</button>
        </div>

        <div class="form-field">
          <label>Character</label>
          <select v-model="newAction.character_id" required>
            <option value="">Select character...</option>
            <option v-for="char in characters" :key="char.id" :value="char.id">
              {{ char.name }}
            </option>
          </select>
        </div>

        <div class="form-field">
          <label>Speak</label>
          <textarea
            v-model="newAction.speak"
            placeholder="What your character says..."
            rows="2"
          ></textarea>
        </div>

        <div class="form-field">
          <label>Act</label>
          <textarea
            v-model="newAction.act"
            placeholder="What your character does..."
            rows="2"
          ></textarea>
        </div>

        <div class="form-field">
          <label>Appearance (optional)</label>
          <input
            v-model="newAction.appearance"
            type="text"
            placeholder="How they look, body language..."
          />
        </div>

        <div class="form-field">
          <label>Emotion (optional)</label>
          <input
            v-model="newAction.emotion"
            type="text"
            placeholder="Their emotional state..."
          />
        </div>

        <div class="form-field">
          <label>OOC Note (optional)</label>
          <textarea
            v-model="newAction.ooc"
            placeholder="Out of character notes for the Keeper..."
            rows="1"
          ></textarea>
        </div>

        <div class="form-actions">
          <button @click="createAction" class="btn-primary" :disabled="!canCreateAction">
            Create Action
          </button>
          <button @click="cancelNewAction" class="btn-secondary">Cancel</button>
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
            'is-mine': draft.player_id === currentPlayerId
          }"
          :draggable="canReorderDrafts && draft.player_id === currentPlayerId"
          @dragstart="handleDragStart(index)"
          @dragover.prevent
          @drop="handleDrop(index)"
        >
          <div class="draft-header">
            <div class="draft-character">
              {{ getCharacterName(draft.character_id) }}
            </div>
            <div class="draft-meta">
              <span class="draft-player">{{ getPlayerName(draft.player_id) }}</span>
              <span v-if="draft.ready" class="ready-badge">✓ Ready</span>
            </div>
          </div>

          <div class="draft-content">
            <div v-if="draft.speak" class="content-section">
              <strong>Speak:</strong> {{ draft.speak }}
            </div>
            <div v-if="draft.act" class="content-section">
              <strong>Act:</strong> {{ draft.act }}
            </div>
            <div v-if="draft.appearance" class="content-section small">
              <em>Appearance:</em> {{ draft.appearance }}
            </div>
            <div v-if="draft.emotion" class="content-section small">
              <em>Emotion:</em> {{ draft.emotion }}
            </div>
            <div v-if="draft.ooc" class="content-section ooc">
              <em>OOC:</em> {{ draft.ooc }}
            </div>
          </div>

          <div v-if="draft.player_id === currentPlayerId" class="draft-actions">
            <button @click="toggleReady(draft)" class="btn-ready" :class="{ active: draft.ready }">
              {{ draft.ready ? 'Unmark Ready' : 'Mark Ready' }}
            </button>
            <button @click="deleteDraft(draft)" class="btn-delete">Delete</button>
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

interface Character {
  id: string
  name: string
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

// n8n webhook for dungeonmaster (SceneActiveTurn actions)
const N8N_DUNGEONMASTER_WEBHOOK = import.meta.env.VITE_N8N_DUNGEONMASTER_WEBHOOK || 'http://localhost:5693/webhook/coc_dungeonmaster'

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

const sortedDrafts = computed(() => {
  return [...props.drafts].sort((a, b) => a.order - b.order)
})

const readyCount = computed(() => {
  return props.drafts.filter((d) => d.ready).length
})

const allActionsReady = computed(() => {
  return props.drafts.length > 0 && props.drafts.every((d) => d.ready)
})

const canCreateAction = computed(() => {
  return newAction.value.character_id && (newAction.value.speak || newAction.value.act)
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

function createAction() {
  if (!canCreateAction.value) return

  emit('createDraft', {
    session_id: props.sessionId,
    player_id: props.currentPlayerId,
    character_id: newAction.value.character_id,
    speak: newAction.value.speak || undefined,
    act: newAction.value.act || undefined,
    appearance: newAction.value.appearance || undefined,
    emotion: newAction.value.emotion || undefined,
    ooc: newAction.value.ooc || undefined,
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

function toggleReady(draft: ActionDraft) {
  emit('updateDraft', { ...draft, ready: !draft.ready })
}

function deleteDraft(draft: ActionDraft) {
  if (confirm('Delete this action?')) {
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

  // Build ordered actions payload from sorted drafts
  const actions = sortedDrafts.value.map((d) => ({
    actor_id: d.character_id,
    player_id: d.player_id,
    speak: d.speak,
    act: d.act,
    appearance: d.appearance,
    emotion: d.emotion,
    ooc: d.ooc,
    order: d.order
  }))

  // Send directly to n8n dungeonmaster webhook with ActiveTurn payload
  fetch(N8N_DUNGEONMASTER_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ActiveTurn: actions,
      session_id: props.sessionId,
      scene_id: props.sceneId || null,
      campaign_id: props.campaignId || null,
      turn_id: props.turnId || null
    })
  })
    .then((res) => res.json())
    .then((data) => {
      // Try to extract a description from returned payload
      let description = data?.output || data?.body || data?.text || data?.response || ''
      if (!description && typeof data === 'object') {
        // fallback: stringify
        description = JSON.stringify(data)
      }

      // Try to extract summary
      let summary = undefined
      if (description) {
        const sentences = description.split('. ')
        if (sentences.length > 1) summary = sentences[0] + '.'
        else if (description.length > 100) summary = description.slice(0, 97) + '...'
      }

      emit('dungeonmasterResponse', { description, summary, actions })
    })
    .catch((err) => {
      console.error('Error calling DungeonMaster webhook:', err)
      emit('dungeonmasterResponse', { error: err?.message || String(err), actions })
    })
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

.draft-item.is-mine {
  border-left-color: var(--vt-c-ink-green-light);
}

.draft-item.is-mine.ready {
  border-left-color: var(--vt-c-ink-green);
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

.draft-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
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
