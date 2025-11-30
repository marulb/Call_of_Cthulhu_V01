<template>
  <div class="scene-progress">
    <div class="list-header">
      <h3>Scene Progress</h3>
      <div class="header-actions">
        <span class="turn-count">{{ turns.length }} turns</span>
        <button
          @click="toggleNarration"
          class="btn-speech"
          :class="{ speaking: isSpeaking }"
          :title="speechTooltip"
        >
          {{ isSpeaking ? '■' : '▶' }}
        </button>
        <button @click="emit('close')" class="btn-close" title="Close">✕</button>
      </div>
    </div>

  <div class="turns-container" ref="container">
      <div v-for="turn in sortedTurns" :key="turn.id" class="turn-item">
        <div class="turn-header">
          <span class="turn-number">Turn {{ turn.order }}</span>
          <span class="turn-status" :class="turn.status">{{ formatStatus(turn.status) }}</span>
        </div>

        <div class="turn-actions">
          <h4>Actions:</h4>
          <div v-for="(action, index) in turn.actions" :key="index" class="action-block">
            <div class="action-actor">
              {{ getCharacterName(action.actor_id) }}
            </div>
            <div v-if="action.speak" class="action-detail">
              <strong>Says:</strong> "{{ action.speak }}"
            </div>
            <div v-if="action.act" class="action-detail">
              <strong>Does:</strong> {{ action.act }}
            </div>
            <div v-if="action.appearance" class="action-detail minor">
              <em>Appearance:</em> {{ action.appearance }}
            </div>
            <div v-if="action.emotion" class="action-detail minor">
              <em>Emotion:</em> {{ action.emotion }}
            </div>
          </div>
        </div>

        <div v-if="turn.reaction" class="turn-reaction">
          <h4>Keeper's Response:</h4>
          <div class="reaction-content markdown-content" v-html="parseMarkdown(turn.reaction.description || '')"></div>
          <div v-if="turn.reaction.summary" class="reaction-summary">
            <strong>Summary:</strong> {{ turn.reaction.summary }}
          </div>
        </div>

        <div v-else-if="turn.status === 'processing'" class="turn-processing">
          <div class="processing-indicator">
            <span class="spinner"></span>
            <span>Keeper is processing...</span>
          </div>
        </div>
      </div>

      <div v-if="turns.length === 0" class="empty-state">
        <p>No turns yet. Submit your first action to begin!</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import type { Turn } from '@/types/gameplay'
import { parseMarkdown } from '@/composables/useMarkdown'
import { useSpeechSynthesis } from '@/composables/useSpeechSynthesis'

interface Character {
  id: string
  name: string
}

const props = defineProps<{
  turns: Turn[]
  characters: Character[]
}>()

const emit = defineEmits<{
  close: []
}>()

// Speech synthesis
const { isSpeaking, toggle, stop, getSelectionOffset, getTextContent } = useSpeechSynthesis()

const speechTooltip = 'Select text to start reading from that point, or click to read from beginning'

function toggleNarration() {
  if (isSpeaking.value) {
    stop()
    return
  }

  if (!container.value) return

  // Get all text from the turns container
  const fullText = getTextContent(container.value)
  if (!fullText) return

  // Check if user has selected text within the container
  const startOffset = getSelectionOffset(container.value)

  toggle(fullText, startOffset)
}

const sortedTurns = computed(() => {
  // Chronological order: oldest turns first, newest appended at the bottom
  return [...props.turns].sort((a, b) => a.order - b.order)
})

// Reference to the scrollable container so we can control scroll position
const container = ref<HTMLElement | null>(null)

// Watch for new turns being added and scroll the container so the newest turn
// (which is rendered at the bottom) appears at the top of the visible area.
watch(
  () => props.turns.length,
  async (newLen, oldLen) => {
    try {
      if ((oldLen ?? 0) === undefined) return
      if (newLen > (oldLen ?? 0)) {
        // wait for DOM to update
        await nextTick()

        if (!container.value) return
        const items = container.value.querySelectorAll('.turn-item')
        if (!items || items.length === 0) return
        const last = items[items.length - 1] as HTMLElement | undefined
        if (container.value) {
          // Always scroll to bottom so the newest turn (appended at bottom) is visible.
          // Use scrollHeight to ensure full content height is used.
          container.value.scrollTop = container.value.scrollHeight
        }
      }
    } catch (err) {
      // swallow any scrolling errors to avoid breaking UI
      console.warn('SceneProgress: scroll after new turn failed', err)
    }
  }
)

function getCharacterName(characterId: string) {
  return props.characters.find((c) => c.id === characterId)?.name || 'Unknown'
}

function formatStatus(status: string) {
  switch (status) {
    case 'draft':
      return 'Draft'
    case 'ready_for_agents':
      return 'Ready'
    case 'processing':
      return 'Processing...'
    case 'completed':
      return 'Completed'
    default:
      return status
  }
}
</script>

<style scoped>
/* TODO: Consider adding to base.css:
   --color-status-completed (for success states)
   --color-status-processing (for in-progress states)
   --color-status-ready (for ready states)
*/

.scene-progress {
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
  gap: 12px;
}

.turn-count {
  background: var(--vt-c-metallic-accent);
  color: var(--vt-c-white);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.btn-speech {
  background: none;
  border: 1px solid var(--vt-c-white);
  font-size: 14px;
  color: var(--vt-c-white);
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s, border-color 0.2s;
}

.btn-speech:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-speech.speaking {
  background: var(--vt-c-ink-green-light);
  border-color: var(--vt-c-ink-green-light);
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

.turns-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

/* Scrollbar styles: WebKit + Firefox friendly */
.turns-container {
  scrollbar-color: var(--color-scrollbar-thumb) var(--color-scrollbar-track);
  scrollbar-width: thin;
}

.turns-container::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.turns-container::-webkit-scrollbar-track {
  background: var(--color-scrollbar-track);
}

.turns-container::-webkit-scrollbar-thumb {
  background: var(--color-scrollbar-thumb);
  border-radius: 8px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.turns-container::-webkit-scrollbar-thumb:hover {
  background: var(--color-scrollbar-thumb-hover);
}

.turn-item {
  background: var(--color-background-soft);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  border-left: 4px solid var(--vt-c-ink-green-light);
}

.turn-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.turn-number {
  font-weight: 700;
  font-size: 15px;
  color: var(--color-heading);
}

.turn-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.turn-status.completed {
  background: var(--vt-c-ink-green);
  color: var(--vt-c-white);
}

.turn-status.processing {
  background: var(--vt-c-metallic-accent);
  color: var(--vt-c-white);
}

.turn-status.ready_for_agents {
  background: var(--vt-c-ink-green-light);
  color: var(--vt-c-white);
}

.turn-status.draft {
  background: var(--color-background-mute);
  color: var(--vt-c-fog);
}

.turn-actions h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: var(--vt-c-fog);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.action-block {
  background: var(--color-background);
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  border-left: 3px solid var(--vt-c-ink-green-light);
}

.action-actor {
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 6px;
  font-size: 14px;
}

.action-detail {
  margin-bottom: 4px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--color-text);
}

.action-detail.minor {
  font-size: 12px;
  color: var(--vt-c-fog);
}

.turn-reaction {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 2px solid var(--vt-c-metallic-accent);
}

.turn-reaction h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: var(--vt-c-metallic-accent);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.reaction-content {
  background: var(--color-background-mute);
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.reaction-content p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text);
  white-space: pre-wrap;
}

/* Markdown content styling */
.markdown-content {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text);
}

.markdown-content :deep(p) {
  margin: 0 0 0.75em 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(strong) {
  font-weight: 600;
  color: var(--color-heading);
}

.markdown-content :deep(em) {
  font-style: italic;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.markdown-content :deep(li) {
  margin: 0.25em 0;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4) {
  margin: 0.75em 0 0.5em 0;
  font-weight: 600;
  color: var(--color-heading);
}

.markdown-content :deep(h1) { font-size: 1.3em; }
.markdown-content :deep(h2) { font-size: 1.2em; }
.markdown-content :deep(h3) { font-size: 1.1em; }
.markdown-content :deep(h4) { font-size: 1em; }

.markdown-content :deep(blockquote) {
  margin: 0.5em 0;
  padding: 0.5em 1em;
  border-left: 3px solid var(--vt-c-metallic-accent);
  background: var(--color-background-soft);
  font-style: italic;
}

.markdown-content :deep(code) {
  background: var(--color-background-mute);
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.9em;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1em 0;
}

.reaction-summary {
  font-size: 12px;
  color: var(--vt-c-fog);
  font-style: italic;
}

.turn-processing {
  margin-top: 12px;
  padding: 12px;
  background: var(--color-background-mute);
  border-radius: 6px;
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--vt-c-metallic-accent);
  font-size: 13px;
  font-weight: 600;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border);
  border-top-color: var(--vt-c-metallic-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--vt-c-fog);
}

.empty-state p {
  margin: 0;
}
</style>
