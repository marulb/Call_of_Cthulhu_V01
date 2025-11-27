<template>
  <div class="game-view">
    <!-- Session Info Header -->
    <SessionInfoHeader :campaign-name="sessionStore.selectedCampaign?.name || ''"
      :realm-name="sessionStore.selectedRealm?.name || ''" :session-number="sessionStore.currentSession?.session_number || 1"
      :current-chapter="currentChapter" :master-player-name="masterPlayerName" :players-online-count="socket.playersOnline.value.length"
      :is-connected="socket.connected.value" />

    <!-- Main Layout: Game Content + Right Sidebar -->
    <div class="main-layout" :class="`layout-${layoutMode}`">
      <!-- Right Sidebar (visibility list + players) -->
      <div class="right-sidebar">
        <!-- Container Visibility List -->
        <div class="sidebar-section visibility-section">
          <ContainerVisibilityList
            :containers="visibilityContainers"
            @toggle-visibility="toggleContainerVisibility"
          />
        </div>

        <!-- Players List -->
        <div class="sidebar-section players-section">
          <PlayersList
            :players="playersWithDetails"
            :current-player-id="sessionStore.playerId || ''"
            :master-player-id="sessionStore.currentSession?.master_player_id"
            @toggle-ready="handleToggleReady"
            @character-double-click="handleCharacterDoubleClick"
          />
        </div>
      </div>

      <!-- Main Game Content: responsive grid controlled by BASE_BREAKPOINT -->
      <div class="game-content">
      <div class="game-grid" :class="`layout-${layoutMode}`" :style="{
        gridTemplateAreas,
        gridTemplateColumns
      }">
            <!-- Character Sheet (when open) -->
            <div v-if="containerVisibility.sheet && showCharacterSheet" class="grid-item sheet" :style="{ gridArea: 'sheet', height: areaHeightPx + 'px' }">
              <CharacterSheetForm
                v-if="editingCharacter"
                v-model="editingCharacter"
                :readonly="isCharacterReadOnly"
                :is-game-view="true"
                @submit="handleCharacterSheetSubmit"
                @close="closeCharacterSheet"
              />
            </div>

            <div v-if="containerVisibility.turn" class="grid-item turn" :style="{ gridArea: 'turn', height: areaHeightPx + 'px' }">
              <SceneProgress :turns="turns" :characters="sessionStore.selectedCharacters" @close="closeContainer('turn')" />
            </div>

            <div v-if="containerVisibility.action" class="grid-item action" :style="{ gridArea: 'action', height: areaHeightPx + 'px' }">
          <SceneActiveTurn :drafts="actionDrafts" :characters="sessionStore.selectedCharacters" :all-characters="allRealmCharacters" :players="allPlayers"
            :current-player-id="sessionStore.playerId || ''" :session-id="sessionStore.currentSession?.id || ''"
            @create-draft="handleCreateDraft" @update-draft="handleUpdateDraft" @delete-draft="handleDeleteDraft"
            @reorder-drafts="handleReorderDrafts" @submit-turn="handleSubmitTurn"
            @dungeonmasterResponse="handleDungeonmasterResponse" @close="closeContainer('action')" />
        </div>

            <div v-if="containerVisibility.realm" class="grid-item realm" :style="{ gridArea: 'realm', height: areaHeightPx + 'px' }">
          <RealmChat :messages="realmMessages" :current-player-id="sessionStore.playerId || ''"
            :connected="socket.connected.value" @send-message="handleSendRealmMessage" @close="closeContainer('realm')" />
        </div>

                    <div v-if="containerVisibility.rules" class="grid-item rules" :style="{ gridArea: 'rules', height: areaHeightPx + 'px' }">
                  <ProphetChat :messages="prophetMessages" :connected="socket.connected.value"
                    :is-waiting-for-response="isWaitingForProphetResponse" @send-message="handleSendProphetMessage" @close="closeContainer('rules')" />
                </div>
      </div>
    </div>
    </div><!-- closes main-layout -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'
import { useSocket } from '@/composables/useSocket'
import { charactersAPI } from '@/services/api'
import type { Character } from '@/services/api'
import SessionInfoHeader from '@/components/SessionInfoHeader.vue'
import PlayersList from '@/components/PlayersList.vue'
import SceneActiveTurn from '@/components/SceneActiveTurn.vue'
import SceneProgress from '@/components/SceneProgress.vue'
import RealmChat from '@/components/RealmChat.vue'
import ProphetChat from '@/components/ProphetChat.vue'
import CharacterSheetForm from '@/components/CharacterSheetForm.vue'
import ContainerVisibilityList from '@/components/ContainerVisibilityList.vue'
import type { VisibilityContainer } from '@/components/ContainerVisibilityList.vue'
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

// Character Sheet Modal State
const showCharacterSheet = ref(false)
const editingCharacter = ref<Character | null>(null)
let autosaveTimeout: ReturnType<typeof setTimeout> | null = null

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8093'

// Right sidebar width (px) - easily adjustable constant
const SIDEBAR_WIDTH = 180

// Single base breakpoint (px). Change this value to experiment with layouts.
const BASE_BREAKPOINT = 600

// Container visibility state
const containerVisibility = ref<Record<string, boolean>>({
  sheet: false,
  turn: true,
  action: true,
  realm: true,
  rules: true
})

const visibilityContainers = computed<VisibilityContainer[]>(() => [
  { id: 'sheet', name: 'Character', visible: containerVisibility.value.sheet ?? false },
  { id: 'turn', name: 'Progress', visible: containerVisibility.value.turn ?? true },
  { id: 'action', name: 'Active Turn', visible: containerVisibility.value.action ?? true },
  { id: 'realm', name: 'Realm Chat', visible: containerVisibility.value.realm ?? true },
  { id: 'rules', name: 'Prophet', visible: containerVisibility.value.rules ?? true }
])

function toggleContainerVisibility(containerId: string) {
  if (containerId === 'sheet') {
    // For character sheet, also close it if it's being hidden
    if (containerVisibility.value.sheet) {
      closeCharacterSheet()
    }
  } else {
    containerVisibility.value[containerId] = !containerVisibility.value[containerId]
  }
}

function closeContainer(containerId: string) {
  if (containerId === 'sheet') {
    closeCharacterSheet()
  } else {
    containerVisibility.value[containerId] = false
  }
}

// Minimum area height for each grid item (px). If window height is larger, areas will expand.
const MIN_AREA_HEIGHT = 400

// Reactive width/height and layout mode derived from BASE_BREAKPOINT
const windowWidth = ref<number>(typeof window !== 'undefined' ? window.innerWidth : 1200)
const windowHeight = ref<number>(typeof window !== 'undefined' ? window.innerHeight : 800)

function updateWidth() {
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight
}

const layoutMode = computed(() => {
  if (windowWidth.value <= BASE_BREAKPOINT) return 'small'
  if (windowWidth.value <= BASE_BREAKPOINT * 2) return 'medium'
  return 'large'
})

// Get list of visible containers (excluding sheet if not open)
const visibleContainers = computed(() => {
  const containers: string[] = []
  if (containerVisibility.value.sheet && showCharacterSheet.value) containers.push('sheet')
  if (containerVisibility.value.turn) containers.push('turn')
  if (containerVisibility.value.action) containers.push('action')
  if (containerVisibility.value.realm) containers.push('realm')
  if (containerVisibility.value.rules) containers.push('rules')
  return containers
})

// Dynamically compute grid template areas based on visible containers
const gridTemplateAreas = computed(() => {
  const visible = visibleContainers.value
  if (visible.length === 0) return '""'

  if (layoutMode.value === 'small') {
    // Stack all vertically
    return visible.map(c => `"${c}"`).join('\n    ')
  } else if (layoutMode.value === 'medium') {
    // 2 columns
    const rows: string[] = []
    for (let i = 0; i < visible.length; i += 2) {
      if (i + 1 < visible.length) {
        rows.push(`"${visible[i]} ${visible[i + 1]}"`)
      } else {
        rows.push(`"${visible[i]} ${visible[i]}"`)
      }
    }
    return rows.join('\n    ')
  } else {
    // Large: all side-by-side
    return `"${visible.join(' ')}"`
  }
})

// Dynamically compute grid template columns based on visible containers
const gridTemplateColumns = computed(() => {
  const visible = visibleContainers.value
  if (visible.length === 0) return '1fr'

  if (layoutMode.value === 'small') {
    return '1fr'
  } else if (layoutMode.value === 'medium') {
    return '1fr 1fr'
  } else {
    // Large: calculate columns based on container types
    const cols = visible.map(c => {
      if (c === 'sheet') return 'minmax(400px, 1.2fr)'
      return 'minmax(200px, 1fr)'
    })
    return cols.join(' ')
  }
})

// Compute how many rows are visible based on layout mode and visible containers
const rowsCount = computed(() => {
  const count = visibleContainers.value.length
  if (layoutMode.value === 'small') return count
  if (layoutMode.value === 'medium') return Math.ceil(count / 2)
  return 1
})

// Grid gap used in CSS (px) - must match .game-grid gap
const GRID_GAP = 16

// Compute available height for the grid (viewport minus header and main-layout padding)
const availableGridHeight = computed(() => {
  // Approximate header height + main-layout padding (top+bottom = 32)
  const headerHeight = 60
  const padding = 32
  const h = windowHeight.value - headerHeight - padding
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

// Character Sheet handlers
const isCharacterReadOnly = computed(() => {
  if (!editingCharacter.value) return true
  // Character is read-only if current player is not the owner
  return editingCharacter.value.controller?.owner !== sessionStore.playerName
})

async function handleCharacterDoubleClick(characterId: string) {
  try {
    // Load full character data from API
    const character = await charactersAPI.get(characterId)
    editingCharacter.value = character
    showCharacterSheet.value = true
    containerVisibility.value.sheet = true
  } catch (error) {
    console.error('Error loading character:', error)
    alert('Failed to load character sheet')
  }
}

function closeCharacterSheet() {
  showCharacterSheet.value = false
  containerVisibility.value.sheet = false
  editingCharacter.value = null
  if (autosaveTimeout) {
    clearTimeout(autosaveTimeout)
    autosaveTimeout = null
  }
}

async function handleCharacterSheetSubmit(characterData: Partial<Character>) {
  if (!characterData.id) return

  try {
    await charactersAPI.update(characterData.id, {
      realm_id: characterData.realm_id!,
      name: characterData.name!,
      description: characterData.description,
      owner: characterData.controller!.owner,
      created_by: sessionStore.playerName,
      data: characterData.data,
      ooc_notes: characterData.ooc_notes,
      profile_completed: characterData.profile_completed
    })

    // Update local character in allRealmCharacters
    const index = allRealmCharacters.value.findIndex(c => c.id === characterData.id)
    if (index !== -1) {
      allRealmCharacters.value[index] = { ...characterData }
    }

    // If profile is now completed, close the modal
    if (characterData.profile_completed) {
      closeCharacterSheet()
    }
  } catch (error) {
    console.error('Error updating character:', error)
    alert('Failed to save character sheet')
  }
}

// Autosave character sheet changes (only if profile is completed)
watch(editingCharacter, (newChar) => {
  if (!newChar || isCharacterReadOnly.value || !newChar.profile_completed) return

  // Clear existing timeout
  if (autosaveTimeout) {
    clearTimeout(autosaveTimeout)
  }

  // Set new timeout for autosave (debounce 2 seconds)
  autosaveTimeout = setTimeout(async () => {
    await handleCharacterSheetSubmit(newChar)
  }, 2000)
}, { deep: true })

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

/* Main layout container: game content + right sidebar */
.main-layout {
  flex: 1;
  display: flex;
  gap: 12px;
  padding: 16px;
  overflow: hidden;
}

/* Small layout: sidebar on top, game content below */
.main-layout.layout-small {
  flex-direction: column;
}

/* Medium and large layouts: sidebar on right */
.main-layout.layout-medium,
.main-layout.layout-large {
  flex-direction: row;
}

/* Right sidebar: contains visibility list + players */
.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-shrink: 0;
}

/* Small layout: sidebar full width on top */
.layout-small .right-sidebar {
  width: 100%;
  flex-direction: row;
  max-height: 200px;
}

/* Medium/Large layouts: sidebar fixed width on right */
.layout-medium .right-sidebar,
.layout-large .right-sidebar {
  width: 120px;
  max-height: none;
}

.sidebar-section {
  background: var(--color-background);
  border-radius: 8px;
  overflow: hidden;
}

/* Small layout: sections side by side */
.layout-small .sidebar-section {
  flex: 1;
  min-width: 0;
}

/* Medium/Large layouts: sections stacked */
.layout-medium .sidebar-section,
.layout-large .sidebar-section {
  width: 100%;
}

.visibility-section {
  flex-shrink: 0;
}

.players-section {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.game-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* Grid container that will change layout based on computed layoutMode class */
.game-grid {
  display: grid;
  gap: 16px;
  width: 100%;
  align-items: start;
  /* grid-template-areas and grid-template-columns are set dynamically via :style */
}

.grid-item {
  display: flex;
  flex-direction: column;
  min-height: 220px;
  overflow: hidden;
}

.grid-item.sheet { grid-area: sheet }
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

/* Character Sheet Styles */
.grid-item.sheet {
  background: var(--color-background);
  border: 2px solid var(--vt-c-ink-green);
  border-radius: 8px;
  overflow: hidden;
}

.grid-item.sheet .list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.grid-item.sheet .list-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-heading);
}

.grid-item.sheet .btn-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--color-text);
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

.grid-item.sheet .btn-close:hover {
  background: var(--color-background-mute);
}
</style>
