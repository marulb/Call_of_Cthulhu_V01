<template>
  <div class="players-list-horizontal">
    <div class="players-container">
      <!-- Each player column -->
      <div
        v-for="player in players"
        :key="player.player_id"
        class="player-column"
      >
        <!-- Player Row (Header) -->
        <div class="player-row" :class="getPlayerClass(player)">
          <span class="entity-name">{{ player.player_name }}</span>
          <span v-if="player.player_id === masterPlayerId" class="master-badge">★</span>
          <button
            v-if="isLocalPlayer(player)"
            class="ready-toggle"
            :class="{ ready: isPlayerReady(player) }"
            @click="togglePlayerReady(player)"
            :title="isPlayerReady(player) ? 'Mark all as not ready' : 'Mark all as ready'"
          >
            <span class="led"></span>
          </button>
        </div>

        <!-- Characters Row - responsive: horizontal first, then vertical -->
        <div class="characters-row">
          <div
            v-for="char in player.characters"
            :key="char.id"
            class="character-cell"
            :class="getCharacterClass(player, char)"
          >
            <span class="entity-name">{{ char.name }}</span>
            <button
              v-if="isLocalPlayer(player)"
              class="ready-toggle"
              :class="{ ready: char.ready }"
              @click="toggleCharacterReady(player.player_id, char.id)"
              :title="char.ready ? 'Mark as not ready' : 'Mark as ready'"
            >
              <span class="led"></span>
            </button>
          </div>
          <div v-if="player.characters.length === 0" class="no-characters">
            (no characters)
          </div>
        </div>
      </div>

      <div v-if="players.length === 0" class="empty-state">
        No players online
      </div>
    </div>

    <!-- <div class="players-summary">
      <span class="summary-text">
        {{ onlineCount }} online • {{ readyCount }}/{{ totalCharacters }} ready
      </span>
    </div> -->
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

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
}>()

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
.players-list-horizontal {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 12px 16px;
  background: #f5f5f5;
  border-bottom: 2px solid #ddd;
  container-type: inline-size;
  container-name: players-list;
}

.players-container {
  display: flex;
  gap: 8px;
  flex: 1;
  align-items: flex-start;
  flex-wrap: wrap;
}

/* 
  Owner Group (player-column) = one player + their characters
  Layout modes controlled by container queries on .players-list-horizontal
*/
.player-column {
  display: flex;
  gap: 4px;
  box-sizing: border-box;
  /* Mode 1 (widest): flex-direction: row - player and characters side-by-side */
  flex-direction: row;
  align-items: center;
  /* Flexible sizing: grow/shrink between 80-160px per entity */
  flex: 1 1 auto;
  min-width: 80px;
}

/* Player Row (entity) */
.player-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  border: 2px solid;
  transition: all 0.2s;
  min-height: 36px;
  font-weight: 700;
  white-space: nowrap;
  box-sizing: border-box;
  /* Flexible width between 80-160px */
  flex: 1 1 auto;
  min-width: 80px;
  max-width: 160px;
}

/* Characters container */
.characters-row {
  display: flex;
  gap: 4px;
  flex-wrap: nowrap;
  flex: 1 1 auto;
}

/* Character Cell (entity) */
.character-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 2px solid;
  border-radius: 4px;
  transition: all 0.2s;
  min-height: 30px;
  font-weight: 500;
  white-space: nowrap;
  box-sizing: border-box;
  /* Flexible width between 80-160px */
  flex: 1 1 auto;
  min-width: 80px;
  max-width: 160px;
}

/* 
  Responsive Layout Modes:
  
  Mode 1 (default/widest): Single horizontal line
    All entities (players + characters) flow horizontally side-by-side
    Each entity flexes between 80-160px
    
  Mode 2 (medium): Two-line owner groups
    Each owner-group has player on top, characters below
    Owner groups sit side-by-side, wrapping as needed
    
  Mode 3 (narrow): Vertical owner groups
    Owner groups stack vertically
    Within each group: player on top, characters in horizontal row below
    
  Mode 4 (narrowest): Fully vertical
    Everything stacked vertically, one entity per line
*/

/* Mode 2: < 600px - Two-line owner groups (player top, characters below) */
@container players-list (max-width: 599px) {
  .player-column {
    flex-direction: column;
    align-items: stretch;
    /* Allow owner groups to sit side-by-side when possible */
    flex: 0 1 auto;
  }
  
  .player-row {
    width: 100%;
    max-width: none;
  }
  
  .characters-row {
    flex-wrap: wrap;
    width: 100%;
  }
  
  .character-cell {
    flex: 1 1 auto;
  }
}

/* Mode 3: < 400px - Vertical owner groups (groups stack, characters horizontal within group) */
@container players-list (max-width: 399px) {
  .players-container {
    flex-direction: column;
    align-items: stretch;
  }
  
  .player-column {
    width: 100%;
    flex: 0 0 auto;
  }
  
  .characters-row {
    flex-wrap: wrap;
  }
}

/* Mode 4: < 200px - Fully vertical (one entity per line) */
@container players-list (max-width: 199px) {
  .characters-row {
    flex-direction: column;
  }
  
  .character-cell {
    width: 100%;
    max-width: none;
  }
}


/* Local player/character: yellow (not ready) -> green (ready) */
.player-row.is-local.is-not-ready,
.character-cell.is-local.is-not-ready {
  background-color: #fff9c4;
  border-color: #f9a825;
}

.player-row.is-local.is-ready,
.character-cell.is-local.is-ready {
  background-color: #c8e6c9;
  border-color: #4caf50;
}

/* Remote player/character: red (not ready) -> green (ready) */
.player-row.is-remote.is-not-ready,
.character-cell.is-remote.is-not-ready {
  background-color: #ffcdd2;
  border-color: #e57373;
}

.player-row.is-remote.is-ready,
.character-cell.is-remote.is-ready {
  background-color: #c8e6c9;
  border-color: #4caf50;
}

.entity-name {
  font-size: 13px;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.player-row .entity-name {
  font-size: 14px;
  font-weight: 700;
}

.character-cell .entity-name {
  font-size: 12px;
  font-weight: 500;
  color: #555;
}

/* Master Badge */
.master-badge {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #333;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

/* Ready Toggle Button (LED style) - only shown for local player/characters */
.ready-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  transition: all 0.2s;
  flex-shrink: 0;
}

.ready-toggle:hover {
  transform: scale(1.2);
}

.ready-toggle .led {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid;
  transition: all 0.2s;
}

/* LED colors: ALWAYS red or green (never yellow) */
/* When entity is NOT ready -> LED is GREEN (click to mark ready) */
.is-not-ready .ready-toggle .led {
  background-color: #4caf50;
  border-color: #2e7d32;
  box-shadow: 0 0 8px rgba(76, 175, 80, 0.7);
}

/* When entity IS ready -> LED is RED (click to mark not ready) */
.is-ready .ready-toggle .led {
  background-color: #f44336;
  border-color: #c62828;
  box-shadow: 0 0 8px rgba(244, 67, 54, 0.7);
}

.no-characters {
  padding: 6px 10px;
  font-size: 11px;
  color: #999;
  font-style: italic;
  background: rgba(0, 0, 0, 0.05);
  border: 2px solid #ddd;
  border-radius: 4px;
  min-width: 80px;
}

.empty-state {
  padding: 16px;
  color: #999;
  font-style: italic;
}

.players-summary {
  padding: 8px 16px;
  background: white;
  border-radius: 6px;
  border: 2px solid #4caf50;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.summary-text {
  font-size: 13px;
  font-weight: 700;
  color: #2e7d32;
  white-space: nowrap;
}
</style>
