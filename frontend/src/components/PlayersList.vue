<template>
  <div class="players-list">
    <div class="list-header">
      <h3>Players</h3>
      <span class="player-count">{{ players.length }}</span>
    </div>

    <div class="players-container">
      <div
        v-for="player in players"
        :key="player.player_id"
        class="player-item"
        :class="{
          offline: !player.online,
          ready: player.ready,
          'is-master': player.player_id === masterPlayerId
        }"
      >
        <div class="player-status">
          <span class="status-indicator" :class="{ online: player.online }"></span>
        </div>

        <div class="player-info">
          <div class="player-name">
            {{ player.player_name }}
            <span v-if="player.player_id === masterPlayerId" class="master-badge">Master</span>
          </div>
          <div v-if="player.character_name" class="character-name">
            {{ player.character_name }}
          </div>
        </div>

        <div v-if="player.online" class="ready-indicator">
          <span v-if="player.ready" class="ready-badge">Ready</span>
          <span v-else class="not-ready">...</span>
        </div>
      </div>

      <div v-if="players.length === 0" class="empty-state">
        <p>No players online</p>
      </div>
    </div>

    <div class="list-footer">
      <div class="ready-summary">
        <span class="ready-count">{{ readyCount }}/{{ onlineCount }} ready</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Player {
  player_id: string
  player_name: string
  character_name?: string
  online: boolean
  ready?: boolean
}

const props = defineProps<{
  players: Player[]
  masterPlayerId?: string
}>()

const onlineCount = computed(() => {
  return props.players.filter((p) => p.online).length
})

const readyCount = computed(() => {
  return props.players.filter((p) => p.online && p.ready).length
})
</script>

<style scoped>
.players-list {
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

.player-count {
  background: #6c63ff;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.players-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.player-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 4px;
  background: #fafafa;
  border-radius: 6px;
  border-left: 3px solid transparent;
  transition: all 0.2s;
}

.player-item.is-master {
  border-left-color: #ffd700;
  background: #fffef0;
}

.player-item.ready {
  border-left-color: #4caf50;
  background: #f1f8f4;
}

.player-item.offline {
  opacity: 0.5;
}

.player-status {
  display: flex;
  align-items: center;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ccc;
  transition: background 0.3s;
}

.status-indicator.online {
  background: #4caf50;
  box-shadow: 0 0 6px #4caf50;
}

.player-info {
  flex: 1;
  min-width: 0;
}

.player-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.master-badge {
  background: #ffd700;
  color: #333;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}

.character-name {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.ready-indicator {
  display: flex;
  align-items: center;
}

.ready-badge {
  background: #4caf50;
  color: white;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.not-ready {
  color: #999;
  font-size: 12px;
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
}

.ready-summary {
  text-align: center;
}

.ready-count {
  font-size: 13px;
  font-weight: 600;
  color: #666;
}
</style>
