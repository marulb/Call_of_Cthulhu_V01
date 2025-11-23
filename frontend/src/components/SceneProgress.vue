<template>
  <div class="scene-progress">
    <div class="list-header">
      <h3>Scene Progress</h3>
      <span class="turn-count">{{ turns.length }} turns</span>
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
          <div class="reaction-content">
            <p>{{ turn.reaction.description }}</p>
          </div>
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

interface Character {
  id: string
  name: string
}

const props = defineProps<{
  turns: Turn[]
  characters: Character[]
}>()

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
.scene-progress {
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

.turn-count {
  background: #ff9800;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.turns-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.turn-item {
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  border-left: 4px solid #6c63ff;
}

.turn-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.turn-number {
  font-weight: 700;
  font-size: 15px;
  color: #333;
}

.turn-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.turn-status.completed {
  background: #4caf50;
  color: white;
}

.turn-status.processing {
  background: #ff9800;
  color: white;
}

.turn-status.ready_for_agents {
  background: #2196f3;
  color: white;
}

.turn-status.draft {
  background: #e0e0e0;
  color: #666;
}

.turn-actions h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.action-block {
  background: white;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  border-left: 3px solid #2196f3;
}

.action-actor {
  font-weight: 700;
  color: #333;
  margin-bottom: 6px;
  font-size: 14px;
}

.action-detail {
  margin-bottom: 4px;
  font-size: 13px;
  line-height: 1.4;
  color: #333;
}

.action-detail.minor {
  font-size: 12px;
  color: #666;
}

.turn-reaction {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 2px solid #ff9800;
}

.turn-reaction h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #ff9800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.reaction-content {
  background: #fff9f0;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.reaction-content p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
}

.reaction-summary {
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.turn-processing {
  margin-top: 12px;
  padding: 12px;
  background: #fff9f0;
  border-radius: 6px;
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ff9800;
  font-size: 13px;
  font-weight: 600;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #ffe0b2;
  border-top-color: #ff9800;
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
  color: #999;
}

.empty-state p {
  margin: 0;
}
</style>
