<template>
  <div class="players-list-horizontal">
    <div class="players-container">
      <div
        v-for="playerGroup in groupedPlayers"
        :key="playerGroup.playerId"
        class="player-group"
        :class="{
          offline: !playerGroup.online,
          'is-master': playerGroup.playerId === masterPlayerId
        }"
      >
        <div class="player-header">
          <span class="status-dot" :class="{ online: playerGroup.online }"></span>
          <span class="player-name">{{ playerGroup.playerName }}</span>
          <span v-if="playerGroup.playerId === masterPlayerId" class="master-badge">★</span>
          <span v-if="playerGroup.ready" class="ready-badge">✓</span>
        </div>
        <div class="characters-list">
          <span
            v-for="(char, index) in playerGroup.characters"
            :key="char.id"
            class="character-name"
          >
            {{ char.name }}<span v-if="index < playerGroup.characters.length - 1">, </span>
          </span>
          <span v-if="playerGroup.characters.length === 0" class="no-characters">
            (no characters)
          </span>
        </div>
      </div>

      <div v-if="groupedPlayers.length === 0" class="empty-state">
        No players online
      </div>
    </div>

    <div class="players-summary">
      <span class="summary-text">
        {{ onlineCount }} online • {{ readyCount }} ready
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Player {
  player_id: string
  player_name: string
  character_name?: string
  character_id?: string
  online: boolean
  ready?: boolean
}

const props = defineProps<{
  players: Player[]
  masterPlayerId?: string
}>()

// Group players by player_id and collect their characters
const groupedPlayers = computed(() => {
  const playerMap = new Map<string, {
    playerId: string
    playerName: string
    online: boolean
    ready: boolean
    characters: Array<{ id: string; name: string }>
  }>()

  props.players.forEach((player) => {
    if (!playerMap.has(player.player_id)) {
      playerMap.set(player.player_id, {
        playerId: player.player_id,
        playerName: player.player_name,
        online: player.online,
        ready: player.ready || false,
        characters: []
      })
    }

    const group = playerMap.get(player.player_id)!
    if (player.character_name && player.character_id) {
      // Check if character already added
      if (!group.characters.find(c => c.id === player.character_id)) {
        group.characters.push({
          id: player.character_id,
          name: player.character_name
        })
      }
    }
  })

  return Array.from(playerMap.values())
})

const onlineCount = computed(() => {
  return groupedPlayers.value.filter((p) => p.online).length
})

const readyCount = computed(() => {
  return groupedPlayers.value.filter((p) => p.online && p.ready).length
})
</script>

<style scoped>
.players-list-horizontal {
  display: flex;
  align-items: center;
  gap: 24px;
  width: 100%;
}

.players-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.player-group {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f8f8f8;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.player-group.is-master {
  border-color: #ffd700;
  background: #fffef0;
}

.player-group.offline {
  opacity: 0.5;
}

.player-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
  flex-shrink: 0;
}

.status-dot.online {
  background: #4caf50;
  box-shadow: 0 0 6px #4caf50;
}

.player-name {
  font-weight: 700;
  color: #333;
  font-size: 14px;
  white-space: nowrap;
}

.master-badge {
  background: #ffd700;
  color: #333;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.ready-badge {
  background: #4caf50;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.characters-list {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-left: 8px;
  border-left: 1px solid #ddd;
}

.character-name {
  font-size: 13px;
  color: #666;
}

.no-characters {
  font-size: 12px;
  color: #999;
  font-style: italic;
}

.empty-state {
  color: #999;
  font-size: 14px;
  padding: 8px;
}

.players-summary {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #6c63ff;
  color: white;
  border-radius: 8px;
  white-space: nowrap;
}

.summary-text {
  font-size: 13px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .players-list-horizontal {
    flex-direction: column;
    align-items: stretch;
  }

  .players-container {
    flex-direction: column;
    align-items: stretch;
  }

  .player-group {
    flex-direction: column;
    align-items: flex-start;
  }

  .characters-list {
    padding-left: 0;
    border-left: none;
    padding-top: 4px;
  }
}
</style>
