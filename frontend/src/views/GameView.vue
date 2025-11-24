<template>
  <div class="game-view">
    <!-- Session Info Header -->
    <SessionInfoHeader :campaign-name="sessionStore.selectedCampaign?.name || ''"
      :realm-name="sessionStore.selectedRealm?.name || ''" :session-number="sessionStore.currentSession?.session_number || 1"
      :current-chapter="currentChapter" :master-player-name="masterPlayerName" :players-online-count="socket.playersOnline.value.length"
      :is-connected="socket.connected.value" />

    <!-- Players List - Horizontal at top -->
    <div class="players-bar" ref="playersBarRef">
      <PlayersList 
        :players="playersWithDetails" 
        :current-player-id="sessionStore.playerId || ''"
        :master-player-id="sessionStore.currentSession?.master_player_id" 
        @toggle-ready="handleToggleReady" 
      />
    </div>

    <!-- Main Game Content: responsive grid controlled by BASE_BREAKPOINT -->
    <div class="game-content">
      <div class="game-grid" :class="`layout-${layoutMode}`">
            <div class="grid-item turn" :style="{ gridArea: 'turn', height: areaHeightPx + 'px' }">
              <SceneProgress :turns="turns" :characters="sessionStore.selectedCharacters" />
            </div>

            <div class="grid-item action" :style="{ gridArea: 'action', height: areaHeightPx + 'px' }">
          <SceneActiveTurn :drafts="actionDrafts" :characters="sessionStore.selectedCharacters" :all-characters="allRealmCharacters" :players="allPlayers"
            :current-player-id="sessionStore.playerId || ''" :session-id="sessionStore.currentSession?.id || ''"
            @create-draft="handleCreateDraft" @update-draft="handleUpdateDraft" @delete-draft="handleDeleteDraft"
            @reorder-drafts="handleReorderDrafts" @submit-turn="handleSubmitTurn"
            @dungeonmasterResponse="handleDungeonmasterResponse" />
        </div>

            <div class="grid-item realm" :style="{ gridArea: 'realm', height: areaHeightPx + 'px' }">
          <RealmChat :messages="realmMessages" :current-player-id="sessionStore.playerId || ''"
            :connected="socket.connected.value" @send-message="handleSendRealmMessage" />
        </div>

                    <div class="grid-item rules" :style="{ gridArea: 'rules', height: areaHeightPx + 'px' }">
                  <ProphetChat :messages="prophetMessages" :connected="socket.connected.value"
                    :is-waiting-for-response="isWaitingForProphetResponse" @send-message="handleSendProphetMessage" />
                </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'
import { useSocket } from '@/composables/useSocket'
import SessionInfoHeader from '@/components/SessionInfoHeader.vue'
import PlayersList from '@/components/PlayersList.vue'
import SceneActiveTurn from '@/components/SceneActiveTurn.vue'
import SceneProgress from '@/components/SceneProgress.vue'
import RealmChat from '@/components/RealmChat.vue'
import ProphetChat from '@/components/ProphetChat.vue'
import type { ActionDraft, Turn, ChatMessage } from '@/types/gameplay'

const router = useRouter()
const sessionStore = useGameSessionStore()
const socket = useSocket()

const actionDrafts = ref<ActionDraft[]>([])
const turns = ref<Turn[]>([])
const realmMessages = ref<ChatMessage[]>([])
const prophetMessages = ref<any[]>([])
const isWaitingForProphetResponse = ref(false)
const currentChapter = ref<string>('')
const currentScene = ref<any>(null)
const allRealmCharacters = ref<any[]>([]) // All characters in the realm
const characterReadyStates = ref<Map<string, boolean>>(new Map()) // character_id -> ready state

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8093'

// Single base breakpoint (px). Change this value to experiment with layouts.
const BASE_BREAKPOINT = 600

// Minimum area height for each grid item (px). If window height is larger, areas will expand.
const MIN_AREA_HEIGHT = 400

// Reactive width/height and layout mode derived from BASE_BREAKPOINT
const windowWidth = ref<number>(typeof window !== 'undefined' ? window.innerWidth : 1200)
const windowHeight = ref<number>(typeof window !== 'undefined' ? window.innerHeight : 800)
const playersBarRef = ref<HTMLElement | null>(null)
const playersBarHeight = ref<number>(0)

function updateWidth() {
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight
  // Measure players bar height if available
  if (playersBarRef.value) {
    playersBarHeight.value = playersBarRef.value.offsetHeight
  }
}

const layoutMode = computed(() => {
  if (windowWidth.value <= BASE_BREAKPOINT) return 'small'
  if (windowWidth.value <= BASE_BREAKPOINT * 2) return 'medium'
  return 'large'
})

// Compute how many rows are visible based on layout mode
const rowsCount = computed(() => (layoutMode.value === 'small' ? 4 : layoutMode.value === 'medium' ? 2 : 1))

// Grid gap used in CSS (px) - must match .game-grid gap
const GRID_GAP = 16

// Compute available height for the grid (viewport minus players bar and outer paddings)
const availableGridHeight = computed(() => {
  // subtract playersBarHeight and some padding (game-content padding top+bottom = 32)
  const padding = 32
  const h = windowHeight.value - playersBarHeight.value - padding
  return h > 0 ? h : 0
})

// Compute per-area height in px (each grid row gets this height). Ensure minimum MIN_AREA_HEIGHT.
const areaHeightPx = computed(() => {
  const rows = rowsCount.value
  // subtract gaps between rows
  const totalGaps = (rows - 1) * GRID_GAP
  const per = Math.floor((availableGridHeight.value - totalGaps) / rows)
  return Math.max(MIN_AREA_HEIGHT, per)
})

// Prepare player data with their characters for the PlayersList component
const playersWithDetails = computed(() => {
  console.log('Computing playersWithDetails...')
  console.log('Players online:', socket.playersOnline.value)
  console.log('All realm characters:', allRealmCharacters.value)
  
  return socket.playersOnline.value.map((p) => {
    // Find all characters owned by this player
    // IMPORTANT: controller.owner stores player NAME, not player_id
    const playerCharacters = allRealmCharacters.value.filter(
      (c: any) => c.controller?.owner === p.player_name
    )
    
    console.log(`Player ${p.player_name} characters:`, playerCharacters)
    
    return {
      player_id: p.player_id,
      player_name: p.player_name,
      online: p.online,
      characters: playerCharacters.map((c: any) => ({
        id: c.id,
        name: c.name,
        ready: characterReadyStates.value.get(c.id) || false
      }))
    }
  })
})

const allPlayers = computed(() => {
  return socket.playersOnline.value.map((p) => ({
    player_id: p.player_id,
    player_name: p.player_name
  }))
})

const masterPlayerName = computed(() => {
  const masterId = sessionStore.currentSession?.master_player_id
  if (!masterId) return undefined
  const master = socket.playersOnline.value.find((p) => p.player_id === masterId)
  return master?.player_name
})

// Initialize and load data
onMounted(async () => {
  console.log('GameView mounted')

  // Start tracking window width for responsive layout
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', updateWidth)
    // set initial value
    updateWidth()
  }

  // Connect to Socket.io
  if (sessionStore.currentSession && sessionStore.playerId && sessionStore.playerName) {
    socket.connect(
      sessionStore.currentSession.id,
      sessionStore.playerId,
      sessionStore.playerName
    )
  }

  // Setup Socket.io event listeners
  setupSocketListeners()

  // Load initial game data
  await loadGameData()
})

onUnmounted(() => {
  // Disconnect from Socket.io
  if (sessionStore.currentSession && sessionStore.playerId) {
    socket.disconnect(sessionStore.currentSession.id, sessionStore.playerId)
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateWidth)
  }
})

function setupSocketListeners() {
  // Action draft events
  socket.onActionDraftCreated((draft: ActionDraft) => {
    actionDrafts.value.push(draft)
  })

  socket.onActionDraftUpdated((draft: ActionDraft) => {
    const index = actionDrafts.value.findIndex((d) => d.id === draft.id)
    if (index !== -1) {
      actionDrafts.value[index] = draft
    }
  })

  socket.onActionDraftDeleted((data: { draft_id: string }) => {
    actionDrafts.value = actionDrafts.value.filter((d) => d.id !== data.draft_id)
  })

  socket.onActionDraftReordered((data: { order: string[] }) => {
    const ordered: ActionDraft[] = []
    data.order.forEach((id, index) => {
      const draft = actionDrafts.value.find((d) => d.id === id)
      if (draft) {
        draft.order = index
        ordered.push(draft)
      }
    })
    actionDrafts.value = ordered
  })

  // Ready state events
  socket.onReadyStateChanged((data: { player_id: string; character_id: string; ready: boolean }) => {
    characterReadyStates.value.set(data.character_id, data.ready)
  })

  // Turn events
  socket.onTurnCompleted(async (data: { turn_id: string; reaction: any }) => {
    // Reload turns to get the updated turn with reaction
    await loadTurns()

    // Clear action drafts and ready states after turn completion
    actionDrafts.value = []
    characterReadyStates.value.clear()
  })

  // Chat events
  socket.onRealmChatMessage((message: ChatMessage) => {
    realmMessages.value.push(message)
  })

  socket.onProphetChatResponse((data: { message: string; timestamp: string }) => {
    prophetMessages.value.push({
      message: data.message,
      isAi: true,
      timestamp: data.timestamp
    })
    isWaitingForProphetResponse.value = false
  })
}

async function loadGameData() {
  try {
    // Load all characters in the realm
    await loadAllRealmCharacters()

    // Load current campaign's active chapter
    const campaignId = sessionStore.selectedCampaign?.id
    if (campaignId) {
      const chaptersRes = await fetch(
        `${API_BASE}/api/v1/chapters?campaign_id=${campaignId}&status=active`
      )
      const chapters = await chaptersRes.json()
      if (chapters.length > 0) {
        currentChapter.value = chapters[0].name

        // Load active scene from chapter
        const scenesRes = await fetch(
          `${API_BASE}/api/v1/scenes?chapter_id=${chapters[0].id}&status=active`
        )
        const scenes = await scenesRes.json()
        if (scenes.length > 0) {
          currentScene.value = scenes[0]
          await loadTurns()
        }
      }
    }

    // Load action drafts for current session
    await loadActionDrafts()
  } catch (error) {
    console.error('Error loading game data:', error)
  }
}

async function loadAllRealmCharacters() {
  try {
    const realmId = sessionStore.selectedRealm?.id
    if (!realmId) return

    const response = await fetch(`${API_BASE}/api/v1/characters?realm_id=${realmId}`)
    if (response.ok) {
      allRealmCharacters.value = await response.json()
      console.log('Loaded realm characters:', allRealmCharacters.value)
    }
  } catch (error) {
    console.error('Error loading realm characters:', error)
  }
}

async function loadActionDrafts() {
  try {
    const sessionId = sessionStore.currentSession?.id
    if (!sessionId) return

    const response = await fetch(`${API_BASE}/api/v1/action-drafts?session_id=${sessionId}`)
    if (response.ok) {
      actionDrafts.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading action drafts:', error)
  }
}

async function loadTurns() {
  try {
    if (!currentScene.value) return

    const response = await fetch(`${API_BASE}/api/v1/turns?scene_id=${currentScene.value.id}`)
    if (response.ok) {
      turns.value = await response.json()
    }
  } catch (error) {
    console.error('Error loading turns:', error)
  }
}

// Action draft handlers
async function handleCreateDraft(draftData: Partial<ActionDraft>) {
  try {
    const response = await fetch(`${API_BASE}/api/v1/action-drafts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(draftData)
    })

    if (response.ok) {
      const newDraft = await response.json()
      actionDrafts.value.push(newDraft)
      socket.emitActionDraftCreated(newDraft)
    }
  } catch (error) {
    console.error('Error creating draft:', error)
  }
}

async function handleUpdateDraft(draft: ActionDraft) {
  try {
    const response = await fetch(`${API_BASE}/api/v1/action-drafts/${draft.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(draft)
    })

    if (response.ok) {
      const updatedDraft = await response.json()
      const index = actionDrafts.value.findIndex((d) => d.id === draft.id)
      if (index !== -1) {
        actionDrafts.value[index] = updatedDraft
      }
      socket.emitActionDraftUpdated(updatedDraft)
    }
  } catch (error) {
    console.error('Error updating draft:', error)
  }
}

async function handleDeleteDraft(draftId: string) {
  try {
    const response = await fetch(`${API_BASE}/api/v1/action-drafts/${draftId}`, {
      method: 'DELETE'
    })

    if (response.ok) {
      actionDrafts.value = actionDrafts.value.filter((d) => d.id !== draftId)
      socket.emitActionDraftDeleted(sessionStore.currentSession!.id, draftId)
    }
  } catch (error) {
    console.error('Error deleting draft:', error)
  }
}

// Handle ready state toggle
function handleToggleReady(playerId: string, characterId: string) {
  const currentState = characterReadyStates.value.get(characterId) || false
  const newState = !currentState
  
  // Update local state
  characterReadyStates.value.set(characterId, newState)
  
  // Broadcast to other players
  socket.emitReadyStateChanged(
    sessionStore.currentSession!.id,
    playerId,
    characterId,
    newState
  )
}

async function handleReorderDrafts(order: string[]) {
  try {
    // Update local order
    const ordered: ActionDraft[] = []
    order.forEach((id, index) => {
      const draft = actionDrafts.value.find((d) => d.id === id)
      if (draft) {
        draft.order = index
        ordered.push(draft)
      }
    })
    actionDrafts.value = ordered

    // Broadcast reorder
    socket.emitActionDraftReordered(sessionStore.currentSession!.id, order)

    // Update each draft's order on backend
    for (const draft of ordered) {
      await fetch(`${API_BASE}/api/v1/action-drafts/${draft.id}/order?order=${draft.order}`, {
        method: 'PATCH'
      })
    }
  } catch (error) {
    console.error('Error reordering drafts:', error)
  }
}

async function handleSubmitTurn() {
  try {
    if (!currentScene.value) return

    // Create turn with all action drafts
    const actions = actionDrafts.value.map((draft) => ({
      actor_id: draft.character_id,
      speak: draft.speak,
      act: draft.act,
      appearance: draft.appearance,
      emotion: draft.emotion,
      ooc: draft.ooc
    }))

    const turnData = {
      scene_id: currentScene.value.id,
      order: turns.value.length + 1,
      actions,
      created_by: sessionStore.playerId
    }

    const response = await fetch(`${API_BASE}/api/v1/turns`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(turnData)
    })

    if (response.ok) {
      const newTurn = await response.json()

      // Submit turn for AI processing
      await fetch(`${API_BASE}/api/v1/turns/${newTurn.id}/submit?submitted_by=${sessionStore.playerId}`, {
        method: 'POST'
      })

      // Clear action drafts
      await fetch(`${API_BASE}/api/v1/action-drafts/session/${sessionStore.currentSession!.id}/clear`, {
        method: 'DELETE'
      })

      actionDrafts.value = []

      // Broadcast turn submission
      socket.emitTurnSubmitted(sessionStore.currentSession!.id, newTurn.id)

      // Reload turns
      await loadTurns()
    }
  } catch (error) {
    console.error('Error submitting turn:', error)
    alert('Failed to submit turn. Please try again.')
  }
}

// Handler for direct DungeonMaster responses emitted by SceneActiveTurn
async function handleDungeonmasterResponse(payload: any) {
  try {
    const description = payload.description || payload.error || 'No response from Keeper'
    const summary = payload.summary

    const actions = payload.actions || actionDrafts.value.map((draft) => ({
      actor_id: draft.character_id,
      speak: draft.speak,
      act: draft.act,
      appearance: draft.appearance,
      emotion: draft.emotion,
      ooc: draft.ooc
    }))

    // Create a local turn object to display the scene progress immediately
    const newTurn: any = {
      id: `local-${Date.now()}`,
      scene_id: currentScene.value?.id || null,
      order: turns.value.length + 1,
      actions,
      status: 'completed',
      reaction: {
        description,
        summary
      },
      meta: { created_by: sessionStore.playerId }
    }

    // Push to UI
    turns.value.push(newTurn)

    // Clear local drafts and notify backend to clear session drafts if possible
    actionDrafts.value = []
    try {
      await fetch(`${API_BASE}/api/v1/action-drafts/session/${sessionStore.currentSession!.id}/clear`, {
        method: 'DELETE'
      })
    } catch (e) {
      console.warn('Could not clear action drafts on backend:', e)
    }

    // Broadcast turn submission so other clients can update
    if (sessionStore.currentSession) {
      socket.emitTurnSubmitted(sessionStore.currentSession.id, newTurn.id)
    }
  } catch (err) {
    console.error('Error handling dungeonmaster response:', err)
  }
}

// Chat handlers
function handleSendRealmMessage(message: string) {
  const chatMessage: ChatMessage = {
    player_id: sessionStore.playerId!,
    player_name: sessionStore.playerName!,
    message,
    timestamp: new Date().toISOString()
  }

  realmMessages.value.push(chatMessage)
  socket.emitRealmChatMessage(chatMessage, sessionStore.currentSession!.id)
}

function handleSendProphetMessage(message: string) {
  const userMessage = {
    message,
    isAi: false,
    timestamp: new Date().toISOString()
  }

  prophetMessages.value.push(userMessage)
  isWaitingForProphetResponse.value = true

  // n8n prophet webhook
  const N8N_PROPHET_WEBHOOK = import.meta.env.VITE_N8N_PROPHET_WEBHOOK || 'http://localhost:5693/webhook/coc_prophet'

  // Call prophet webhook directly
  fetch(N8N_PROPHET_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: sessionStore.playerId,
      question: message
    })
  })
    .then((res) => res.json())
    .then((data) => {
      // Extract response from n8n workflow output
      const responseText = data?.output || data?.text || data?.response || 'No response from Prophet'
      prophetMessages.value.push({
        message: responseText,
        isAi: true,
        timestamp: new Date().toISOString(),
        references: data.references || []
      })
      isWaitingForProphetResponse.value = false
    })
    .catch((error) => {
      console.error('Error getting prophet response:', error)
      prophetMessages.value.push({
        message: 'The Prophet seems troubled and cannot respond at this time...',
        isAi: true,
        timestamp: new Date().toISOString()
      })
      isWaitingForProphetResponse.value = false
    })
}
</script>

<style scoped>
.game-view {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--color-background-soft);
}

.players-bar {
  background: var(--color-background);
  border-bottom: 2px solid var(--color-border);
  padding: 12px 16px;
}

.game-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  width: 100%;
}

/* Grid container that will change layout based on computed layoutMode class */
.game-grid {
  display: grid;
  gap: 16px;
  width: 100%;
  align-items: start;
}

/* Small: all stacked vertically (<= BASE_BREAKPOINT) */
.layout-small {
  grid-template-columns: 1fr;
  grid-template-areas:
    "turn"
    "action"
    "realm"
    "rules";
}

/* Medium: two-by-two (<= BASE_BREAKPOINT * 2) */
.layout-medium {
  grid-template-columns: 1fr 1fr;
  grid-template-areas:
    "turn action"
    "realm rules";
}

/* Large: all side-by-side */
.layout-large {
  grid-template-columns: repeat(4, 1fr);
  grid-template-areas: "turn action realm rules";
}

.grid-item {
  display: flex;
  flex-direction: column;
  min-height: 220px;
  overflow: hidden;
}

.grid-item.turn { grid-area: turn }
.grid-item.action { grid-area: action }
.grid-item.realm { grid-area: realm }
.grid-item.rules { grid-area: rules }

/* Ensure children stretch and keep internal scroll where needed */
.grid-item > * {
  flex: 1 1 auto;
  min-height: 0; /* allow internal scroll */
}

/* sensible defaults for very small screens */
@media (max-width: 480px) {
  .grid-item { min-height: 180px }
}
</style>
