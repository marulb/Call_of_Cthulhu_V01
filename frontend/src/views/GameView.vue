<template>
  <div class="game-view">
    <!-- Session Info Header -->
    <SessionInfoHeader :campaign-name="sessionStore.selectedCampaign?.name || ''"
      :realm-name="sessionStore.selectedRealm?.name || ''" :session-number="sessionStore.currentSession?.session_number || 1"
      :current-chapter="currentChapter" :master-player-name="masterPlayerName" :players-online-count="socket.playersOnline.value.length"
      :is-connected="socket.connected.value" />

    <!-- Main Game Content -->
    <div class="game-content">
      <!-- Left Sidebar: Players List -->
      <div class="sidebar-left">
        <PlayersList :players="playersWithDetails" :master-player-id="sessionStore.currentSession?.master_player_id" />
      </div>

      <!-- Middle Column: Action List & Turn History -->
      <div class="content-middle">
        <div class="content-top">
          <div class="action-list-container">
            <ActionList :drafts="actionDrafts" :characters="sessionStore.selectedCharacters" :players="allPlayers"
              :current-player-id="sessionStore.playerId || ''" :session-id="sessionStore.currentSession?.id || ''"
              @create-draft="handleCreateDraft" @update-draft="handleUpdateDraft" @delete-draft="handleDeleteDraft"
              @reorder-drafts="handleReorderDrafts" @submit-turn="handleSubmitTurn" />
          </div>

          <div class="turn-history-container">
            <TurnHistory :turns="turns" :characters="sessionStore.selectedCharacters" />
          </div>
        </div>

        <!-- Bottom Row: Chats -->
        <div class="content-bottom">
          <div class="realm-chat-container">
            <RealmChat :messages="realmMessages" :current-player-id="sessionStore.playerId || ''"
              :connected="socket.connected.value" @send-message="handleSendRealmMessage" />
          </div>

          <div class="rules-chat-container">
            <RulesChat :messages="rulesMessages" :connected="socket.connected.value"
              :is-waiting-for-response="isWaitingForRulesResponse" @send-message="handleSendRulesMessage" />
          </div>
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
import ActionList from '@/components/ActionList.vue'
import TurnHistory from '@/components/TurnHistory.vue'
import RealmChat from '@/components/RealmChat.vue'
import RulesChat from '@/components/RulesChat.vue'
import type { ActionDraft, Turn, ChatMessage } from '@/types/gameplay'

const router = useRouter()
const sessionStore = useGameSessionStore()
const socket = useSocket()

const actionDrafts = ref<ActionDraft[]>([])
const turns = ref<Turn[]>([])
const realmMessages = ref<ChatMessage[]>([])
const rulesMessages = ref<any[]>([])
const isWaitingForRulesResponse = ref(false)
const currentChapter = ref<string>('')
const currentScene = ref<any>(null)

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8093'

const playersWithDetails = computed(() => {
  return socket.playersOnline.value.map((p) => {
    const character = sessionStore.selectedCharacters.find(
      (c: any) => c.player_id === p.player_id
    )
    return {
      ...p,
      character_name: character?.name,
      ready: actionDrafts.value.some(
        (d: ActionDraft) => d.player_id === p.player_id && d.ready
      )
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

  // Turn events
  socket.onTurnCompleted(async (data: { turn_id: string; reaction: any }) => {
    // Reload turns to get the updated turn with reaction
    await loadTurns()

    // Clear action drafts after turn completion
    actionDrafts.value = []
  })

  // Chat events
  socket.onRealmChatMessage((message: ChatMessage) => {
    realmMessages.value.push(message)
  })

  socket.onRulesChatResponse((data: { message: string; timestamp: string }) => {
    rulesMessages.value.push({
      message: data.message,
      isAi: true,
      timestamp: data.timestamp
    })
    isWaitingForRulesResponse.value = false
  })
}

async function loadGameData() {
  try {
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

function handleSendRulesMessage(message: string) {
  const userMessage = {
    message,
    isAi: false,
    timestamp: new Date().toISOString()
  }

  rulesMessages.value.push(userMessage)
  isWaitingForRulesResponse.value = true

  socket.emitRulesChatMessage(sessionStore.playerId!, message, new Date().toISOString())

  // Also call REST API as fallback
  fetch(`${API_BASE}/api/v1/ai/rules/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: sessionStore.playerId,
      question: message
    })
  })
    .then((res) => res.json())
    .then((data) => {
      if (isWaitingForRulesResponse.value) {
        rulesMessages.value.push({
          message: data.answer,
          isAi: true,
          timestamp: new Date().toISOString(),
          references: data.rules_references
        })
        isWaitingForRulesResponse.value = false
      }
    })
    .catch((error) => {
      console.error('Error getting rules response:', error)
      isWaitingForRulesResponse.value = false
    })
}
</script>

<style scoped>
.game-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f0f0f0;
  overflow: hidden;
}

.game-content {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.sidebar-left {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.content-middle {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.content-top {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  min-height: 0;
}

.action-list-container,
.turn-history-container {
  min-height: 0;
  display: flex;
}

.content-bottom {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  height: 350px;
}

.realm-chat-container,
.rules-chat-container {
  display: flex;
}

@media (max-width: 1200px) {
  .game-content {
    grid-template-columns: 250px 1fr;
  }
}

@media (max-width: 768px) {
  .game-content {
    grid-template-columns: 1fr;
  }

  .sidebar-left {
    height: 200px;
  }

  .content-top {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .content-bottom {
    grid-template-columns: 1fr;
    height: auto;
  }

  .realm-chat-container,
  .rules-chat-container {
    height: 300px;
  }
}
</style>
