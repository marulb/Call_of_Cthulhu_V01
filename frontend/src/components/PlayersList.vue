<template>
  <div class="players-list-compact">
    <div class="players-header">
      <h4>Players</h4>
    </div>

    <div class="players-container">
      <!-- Each player section -->
      <div
        v-for="player in players"
        :key="player.player_id"
        class="player-section"
      >
        <!-- Player Header -->
        <div class="player-item" :class="getPlayerClass(player)" @click="togglePlayerCollapse(player.player_id)">
          <button
            v-if="isLocalPlayer(player)"
            class="ready-led"
            :class="{ ready: isPlayerReady(player) }"
            @click.stop="togglePlayerReady(player)"
            :title="isPlayerReady(player) ? 'Mark all as not ready' : 'Mark all as ready'"
          >
            <span class="led"></span>
          </button>
          <span class="toggle-arrow" :class="{ collapsed: isPlayerCollapsed(player.player_id) }">▼</span>
          <span class="player-name">{{ player.player_name }}</span>
          <span v-if="player.player_id === masterPlayerId" class="master-star">★</span>
        </div>

        <!-- Characters List -->
        <div v-show="!isPlayerCollapsed(player.player_id)" class="characters-list">
          <div
            v-for="char in player.characters"
            :key="char.id"
            class="character-item"
            :class="getCharacterClass(player, char)"
            @dblclick="handleCharacterDoubleClick(char.id)"
            :title="'Double-click to edit'"
          >
            <button
              v-if="isLocalPlayer(player)"
              class="ready-led"
              :class="{ ready: char.ready }"
              @click.stop="toggleCharacterReady(player.player_id, char.id)"
              :title="char.ready ? 'Mark not ready' : 'Mark ready'"
            >
              <span class="led"></span>
            </button>
            <span class="character-name">{{ char.name }}</span>
          </div>
          <div v-if="player.characters.length === 0" class="no-characters">
            No characters
          </div>
        </div>
      </div>

      <div v-if="players.length === 0" class="empty-state">
        No players
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Character {
  id: string
  name: string
  ready: boolean
}

interface Player {
  player_id: string
  player_name: string
  online: boolean
  characters: Character[]
}

const props = defineProps<{
  players: Player[]
  currentPlayerId: string
  masterPlayerId?: string
}>()

const emit = defineEmits<{
  toggleReady: [playerId: string, characterId: string]
  characterDoubleClick: [characterId: string]
}>()

// Track which players are collapsed
const collapsedPlayers = ref<Set<string>>(new Set())

// Check if player is collapsed
const isPlayerCollapsed = (playerId: string) => {
  return collapsedPlayers.value.has(playerId)
}

// Toggle player collapse state
const togglePlayerCollapse = (playerId: string) => {
  if (collapsedPlayers.value.has(playerId)) {
    collapsedPlayers.value.delete(playerId)
  } else {
    collapsedPlayers.value.add(playerId)
  }
  // Trigger reactivity
  collapsedPlayers.value = new Set(collapsedPlayers.value)
}

// Check if player is local (current user)
const isLocalPlayer = (player: Player) => player.player_id === props.currentPlayerId

// Check if all player's characters are ready (player ready = all characters ready)
const isPlayerReady = (player: Player) => {
  if (player.characters.length === 0) return false
  return player.characters.every(c => c.ready)
}

// Get CSS class for player based on ready state and local/remote
const getPlayerClass = (player: Player) => {
  const isLocal = isLocalPlayer(player)
  const ready = isPlayerReady(player)
  
  return {
    'is-local': isLocal,
    'is-remote': !isLocal,
    'is-ready': ready,
    'is-not-ready': !ready
  }
}

// Get CSS class for character based on ready state and ownership
const getCharacterClass = (player: Player, char: Character) => {
  const isLocal = isLocalPlayer(player)
  
  return {
    'is-local': isLocal,
    'is-remote': !isLocal,
    'is-ready': char.ready,
    'is-not-ready': !char.ready
  }
}

// Toggle ready state for all player's characters
const togglePlayerReady = (player: Player) => {
  const currentlyAllReady = isPlayerReady(player)
  const newReadyState = !currentlyAllReady
  
  // Toggle all characters to the new state
  player.characters.forEach(char => {
    if (char.ready !== newReadyState) {
      emit('toggleReady', player.player_id, char.id)
    }
  })
}

// Toggle ready state for a single character
const toggleCharacterReady = (playerId: string, characterId: string) => {
  emit('toggleReady', playerId, characterId)
}

// Handle character double-click to open character sheet
const handleCharacterDoubleClick = (characterId: string) => {
  emit('characterDoubleClick', characterId)
}

const onlineCount = computed(() => {
  return props.players.filter(p => p.online).length
})

const totalCharacters = computed(() => {
  return props.players.reduce((sum, p) => sum + p.characters.length, 0)
})

const readyCount = computed(() => {
  let count = 0
  props.players.forEach(p => {
    p.characters.forEach(c => {
      if (c.ready) count++
    })
  })
  return count
})
</script>

<style scoped>
.players-list-compact {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.players-header {
  padding: 8px 12px;
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.players-header h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-heading);
}

.players-container {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}

.player-section {
  margin-bottom: 8px;
}

.player-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  border-radius: 4px;
  border: 1px solid;
  margin-bottom: 2px;
  transition: all 0.2s;
  cursor: pointer;
  user-select: none;
}

.player-item:hover {
  opacity: 0.85;
}

/* Local player/character states */
.player-item.is-local.is-not-ready {
  background-color: var(--color-background-mute);
  border-color: var(--vt-c-metallic-accent);
}

.player-item.is-local.is-ready {
  background-color: var(--color-background-mute);
  border-color: var(--vt-c-ink-green);
}

/* Remote player/character states */
.player-item.is-remote.is-not-ready {
  background-color: var(--color-background-soft);
  border-color: var(--vt-c-fog);
}

.player-item.is-remote.is-ready {
  background-color: var(--color-background-mute);
  border-color: var(--vt-c-ink-green);
}

.toggle-arrow {
  font-size: 10px;
  color: var(--color-text);
  transition: transform 0.2s;
  flex-shrink: 0;
  width: 12px;
  text-align: center;
}

.toggle-arrow.collapsed {
  transform: rotate(-90deg);
}

.player-name {
  flex: 1;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text);
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.2;
}

.master-star {
  font-size: 10px;
  color: var(--vt-c-metallic-accent);
  flex-shrink: 0;
}

.characters-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-left: 8px;
}

.character-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 4px;
  border-radius: 3px;
  border: 1px solid;
  transition: all 0.2s;
  cursor: pointer;
}

.character-item.is-local.is-not-ready {
  background-color: var(--color-background-mute);
  border-color: var(--vt-c-metallic-accent);
}

.character-item.is-local.is-ready {
  background-color: var(--color-background-mute);
  border-color: var(--vt-c-ink-green);
}

.character-item.is-remote.is-not-ready {
  background-color: var(--color-background-soft);
  border-color: var(--vt-c-fog);
}

.character-item.is-remote.is-ready {
  background-color: var(--color-background-mute);
  border-color: var(--vt-c-ink-green);
}

.character-item:hover {
  opacity: 0.8;
}

.character-name {
  flex: 1;
  font-size: 10px;
  font-weight: 500;
  color: var(--vt-c-fog);
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.2;
}

/* Ready LED Button */
.ready-led {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 12px;
  height: 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  transition: all 0.2s;
  flex-shrink: 0;
}

.ready-led:hover {
  transform: scale(1.15);
}

.ready-led .led {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1px solid;
  transition: all 0.2s;
}

/* LED colors: GREEN when not ready, RED when ready */
.is-not-ready .ready-led .led {
  background-color: var(--vt-c-ink-green);
  border-color: var(--vt-c-deep-sea);
  box-shadow: 0 0 4px var(--vt-c-ink-green-light);
}

.is-ready .ready-led .led {
  background-color: var(--vt-c-metallic-accent);
  border-color: var(--vt-c-fog);
  box-shadow: 0 0 4px var(--vt-c-metallic-accent);
}

.no-characters {
  padding: 3px 4px;
  font-size: 9px;
  color: var(--vt-c-fog);
  font-style: italic;
}

.empty-state {
  padding: 12px;
  font-size: 10px;
  color: var(--vt-c-fog);
  font-style: italic;
  text-align: center;
}
</style>
