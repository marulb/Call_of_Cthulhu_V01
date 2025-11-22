<template>
  <div class="session-header">
    <div class="session-main-info">
      <div class="session-title">
        <h1>{{ campaignName }}</h1>
        <div class="session-meta">
          <span class="realm-name">{{ realmName }}</span>
          <span class="separator">•</span>
          <span class="session-number">Session #{{ sessionNumber }}</span>
          <span v-if="currentChapter" class="separator">•</span>
          <span v-if="currentChapter" class="chapter-name">{{ currentChapter }}</span>
        </div>
      </div>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  campaignName: string
  realmName: string
  sessionNumber: number
  currentChapter?: string
  masterPlayerName?: string
  playersOnlineCount: number
  isConnected: boolean
}>()
</script>

<style scoped>
.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #1a1a2e;
  color: white;
  padding: 16px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.session-main-info {
  flex: 1;
}

.session-title h1 {
  margin: 0 0 6px 0;
  font-size: 24px;
  font-weight: 700;
  color: #f5f5f5;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #b0b0b0;
}

.realm-name {
  color: #6c63ff;
  font-weight: 600;
}

.session-number {
  color: #4caf50;
}

.chapter-name {
  color: #ff9800;
  font-style: italic;
}

.separator {
  color: #555;
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
  background: #888;
  transition: background 0.3s;
}

.status-dot.connected {
  background: #4caf50;
  box-shadow: 0 0 8px #4caf50;
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
  color: #b0b0b0;
}

.master-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.master-label {
  color: #888;
}

.master-name {
  color: #ffd700;
  font-weight: 600;
}

.players-online {
  font-size: 14px;
  color: #b0b0b0;
}

.online-count {
  font-weight: 500;
}
</style>
