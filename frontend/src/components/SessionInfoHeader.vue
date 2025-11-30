<template>
  <div class="session-header">
    <div class="session-main-info">
      <h1>{{ campaignName }}</h1>
      <span class="separator">•</span>
      <span class="realm-name">{{ realmName }}</span>
      <span class="separator">•</span>
      <span class="session-number">Session #{{ sessionNumber }}</span>
      <span v-if="currentChapter" class="separator">•</span>
      <span v-if="currentChapter" class="chapter-name">{{ currentChapter }}</span>
    </div>

    <div class="session-status">
      <div class="connection-status">
        <span class="status-dot" :class="{ connected: isConnected }"></span>
        <span class="status-text">{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
      </div>

      <div v-if="masterPlayerName" class="master-info">
        <span class="master-label">Master:</span>
        <span class="master-name">{{ masterPlayerName }}</span>
      </div>

      <div class="players-online">
        <span class="online-count">{{ playersOnlineCount }} online</span>
      </div>

      <button @click="emit('openSettings')" class="btn-settings" title="Settings">
        ⚙
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  campaignName: string
  realmName: string
  sessionNumber: number
  currentChapter?: string
  masterPlayerName?: string
  playersOnlineCount: number
  isConnected: boolean
}>()

const emit = defineEmits<{
  openSettings: []
}>()
</script>

<style scoped>
/* TODO: Consider adding to base.css semantic section:
   --color-accent-success (for connected/online states)
   --color-accent-warning (for chapter/alert highlighting)
   For now using existing palette colors with atmospheric Cthulhu theme
*/

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--vt-c-black-soft);
  color: var(--vt-c-text-dark-1);
  padding: 10px 24px;
  box-shadow: 0 2px 8px var(--vt-c-divider-dark-1);
}

.session-main-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  font-size: 13px;
  color: var(--vt-c-fog);
}

.session-main-info h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-heading);
}

.realm-name {
  color: var(--vt-c-ink-green-light);
  font-weight: 600;
}

.session-number {
  color: var(--vt-c-metallic-accent);
}

.chapter-name {
  color: var(--vt-c-metallic-accent);
  font-style: italic;
}

.separator {
  color: var(--vt-c-divider-dark-2);
}

.session-status {
  display: flex;
  align-items: center;
  gap: 24px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--vt-c-fog);
  transition: background 0.3s;
}

.status-dot.connected {
  background: var(--vt-c-ink-green-light);
  box-shadow: 0 0 8px var(--vt-c-ink-green-light);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.status-text {
  font-size: 14px;
  color: var(--vt-c-fog);
}

.master-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.master-label {
  color: var(--vt-c-fog);
}

.master-name {
  color: var(--vt-c-metallic-accent);
  font-weight: 600;
}

.players-online {
  font-size: 14px;
  color: var(--vt-c-fog);
}

.online-count {
  font-weight: 500;
}

.btn-settings {
  background: none;
  border: 1px solid var(--vt-c-fog);
  font-size: 16px;
  color: var(--vt-c-fog);
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.btn-settings:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--vt-c-white);
  border-color: var(--vt-c-white);
}
</style>
