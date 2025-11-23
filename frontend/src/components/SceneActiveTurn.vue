<template>
  <div class="active-turn">
    <div class="list-header">
      <h3>Scene - Active Turn</h3>
      <button v-if="!showNewForm" @click="showNewForm = true" class="btn-add">+ New Action</button>
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
  characters: Character[]
  players: Player[]
  currentPlayerId: string
  sessionId: string
}>()

const emit = defineEmits<{
  createDraft: [draft: Partial<ActionDraft>]
  updateDraft: [draft: ActionDraft]
  deleteDraft: [draftId: string]
  reorderDrafts: [order: string[]]
  submitTurn: []
  dungeonmasterResponse: [response: any]
}>()

// n8n webhook (frontend/dev-accessible). Prefer setting VITE_N8N_WEBHOOK in env for prod/dev.
const N8N_WEBHOOK = import.meta.env.VITE_N8N_WEBHOOK || 'http://localhost:5693/webhook/coc_orchestrator'

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
  return props.characters.find((c) => c.id === characterId)?.name || 'Unknown'
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

  // Send directly to n8n webhook with ActiveTurn payload
  fetch(N8N_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ActiveTurn: actions })
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
.active-turn {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f8f8;
  border-bottom: 1px solid #e0e0e0;
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.btn-add {
  padding: 6px 12px;
  background: #6c63ff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-add:hover {
  background: #5952d4;
}

.actions-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.action-form {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 2px solid #6c63ff;
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
  color: #333;
}

.btn-cancel {
  background: none;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-cancel:hover {
  color: #666;
}

.form-field {
  margin-bottom: 12px;
}

.form-field label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #555;
}

.form-field input,
.form-field textarea,
.form-field select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
}

.form-field input:focus,
.form-field textarea:focus,
.form-field select:focus {
  outline: none;
  border-color: #6c63ff;
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.btn-primary {
  flex: 1;
  padding: 10px;
  background: #6c63ff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #5952d4;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 16px;
  background: #e0e0e0;
  color: #333;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #d0d0d0;
}

.drafts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.draft-item {
  background: #fafafa;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #ddd;
  transition: all 0.2s;
}

.draft-item.ready {
  border-left-color: #4caf50;
  background: #f1f8f4;
}

.draft-item.is-mine {
  border-left-color: #6c63ff;
}

.draft-item.is-mine.ready {
  border-left-color: #4caf50;
}

.draft-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.draft-character {
  font-weight: 700;
  color: #333;
  font-size: 14px;
}

.draft-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.draft-player {
  color: #666;
}

.ready-badge {
  background: #4caf50;
  color: white;
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
  color: #333;
}

.content-section.small {
  font-size: 12px;
  color: #666;
}

.content-section.ooc {
  background: #fff9e6;
  padding: 6px;
  border-radius: 4px;
  border-left: 2px solid #ffb84d;
}

.draft-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.btn-ready {
  flex: 1;
  padding: 6px 12px;
  background: #e0e0e0;
  color: #333;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-ready.active {
  background: #4caf50;
  color: white;
}

.btn-ready:hover {
  opacity: 0.8;
}

.btn-delete {
  padding: 6px 12px;
  background: #ffebee;
  color: #d32f2f;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-delete:hover {
  background: #ffcdd2;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-state p {
  margin: 0;
}

.list-footer {
  padding: 12px 16px;
  background: #f8f8f8;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-summary {
  font-size: 13px;
  font-weight: 600;
  color: #666;
}

.btn-submit {
  padding: 8px 16px;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit:hover {
  background: #45a049;
}
</style>
