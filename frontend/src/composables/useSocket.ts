/**
 * Socket.io composable for real-time gameplay features
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { io, type Socket } from 'socket.io-client'
import type { ActionDraft, ChatMessage, PlayerPresence } from '@/types/gameplay'

const socket = ref<Socket | null>(null)
const connected = ref(false)
const playersOnline = ref<PlayerPresence[]>([])

export function useSocket() {
  function connect(sessionId: string, playerId: string, playerName: string) {
    if (socket.value?.connected) {
      console.log('Socket already connected')
      return
    }

    const socketUrl = import.meta.env.VITE_API_URL || 'http://localhost:8093'

    socket.value = io(socketUrl, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    })

    socket.value.on('connect', () => {
      console.log('Socket.io connected:', socket.value?.id)
      connected.value = true

      // Join session room
      socket.value?.emit('join_session', {
        session_id: sessionId,
        player_id: playerId,
        player_name: playerName
      })
    })

    socket.value.on('disconnect', () => {
      console.log('Socket.io disconnected')
      connected.value = false
    })

    socket.value.on('error', (error: any) => {
      console.error('Socket.io error:', error)
    })

    // Session events
    socket.value.on('session_joined', (data: any) => {
      console.log('Joined session:', data)
      playersOnline.value = data.players_online || []
    })

    socket.value.on('player_joined', (data: any) => {
      console.log('Player joined:', data)
      playersOnline.value.push({
        player_id: data.player_id,
        player_name: data.player_name,
        online: true
      })
    })

    socket.value.on('player_left', (data: any) => {
      console.log('Player left:', data)
      playersOnline.value = playersOnline.value.filter(
        (p) => p.player_id !== data.player_id
      )
    })

    socket.value.on('player_disconnected', (data: any) => {
      console.log('Player disconnected:', data)
      const player = playersOnline.value.find((p) => p.player_id === data.player_id)
      if (player) {
        player.online = false
      }
    })
  }

  function disconnect(sessionId?: string, playerId?: string) {
    if (sessionId && playerId) {
      socket.value?.emit('leave_session', {
        session_id: sessionId,
        player_id: playerId
      })
    }
    socket.value?.disconnect()
    connected.value = false
    playersOnline.value = []
  }

  // Action draft events
  function emitActionDraftCreated(draft: ActionDraft) {
    socket.value?.emit('action_draft_created', draft)
  }

  function emitActionDraftUpdated(draft: ActionDraft) {
    socket.value?.emit('action_draft_updated', draft)
  }

  function emitActionDraftDeleted(sessionId: string, draftId: string) {
    socket.value?.emit('action_draft_deleted', {
      session_id: sessionId,
      draft_id: draftId
    })
  }

  function emitActionDraftReordered(sessionId: string, order: string[]) {
    socket.value?.emit('action_draft_reordered', {
      session_id: sessionId,
      order
    })
  }

  // Ready state events
  function emitReadyStateChanged(
    sessionId: string,
    playerId: string,
    characterId: string,
    ready: boolean
  ) {
    socket.value?.emit('ready_state_changed', {
      session_id: sessionId,
      player_id: playerId,
      character_id: characterId,
      ready
    })
  }

  // Turn submission events
  function emitTurnSubmitted(sessionId: string, turnId: string) {
    socket.value?.emit('turn_submitted', {
      session_id: sessionId,
      turn_id: turnId
    })
  }

  // Chat events
  function emitRealmChatMessage(message: ChatMessage, sessionId: string) {
    socket.value?.emit('realm_chat_message', {
      session_id: sessionId,
      player_id: message.player_id,
      player_name: message.player_name,
      message: message.message,
      timestamp: message.timestamp
    })
  }

  function emitRulesChatMessage(playerId: string, message: string, timestamp: string) {
    socket.value?.emit('rules_chat_message', {
      player_id: playerId,
      message,
      timestamp
    })
  }

  // Event listeners
  function onActionDraftCreated(callback: (data: ActionDraft) => void) {
    socket.value?.on('action_draft_created', callback)
  }

  function onActionDraftUpdated(callback: (data: ActionDraft) => void) {
    socket.value?.on('action_draft_updated', callback)
  }

  function onActionDraftDeleted(callback: (data: { draft_id: string }) => void) {
    socket.value?.on('action_draft_deleted', callback)
  }

  function onActionDraftReordered(callback: (data: { order: string[] }) => void) {
    socket.value?.on('action_draft_reordered', callback)
  }

  function onReadyStateChanged(
    callback: (data: { player_id: string; character_id: string; ready: boolean }) => void
  ) {
    socket.value?.on('ready_state_changed', callback)
  }

  function onTurnSubmitted(callback: (data: { turn_id: string; status: string }) => void) {
    socket.value?.on('turn_submitted', callback)
  }

  function onTurnCompleted(callback: (data: { turn_id: string; reaction: any }) => void) {
    socket.value?.on('turn_completed', callback)
  }

  function onRealmChatMessage(callback: (data: ChatMessage) => void) {
    socket.value?.on('realm_chat_message', callback)
  }

  function onRulesChatResponse(callback: (data: { message: string; timestamp: string }) => void) {
    socket.value?.on('rules_chat_response', callback)
  }

  function onMasterTransferred(
    callback: (data: { new_master_id: string; new_master_name: string }) => void
  ) {
    socket.value?.on('master_transferred', callback)
  }

  return {
    socket,
    connected,
    playersOnline,
    connect,
    disconnect,
    emitActionDraftCreated,
    emitActionDraftUpdated,
    emitActionDraftDeleted,
    emitActionDraftReordered,
    emitReadyStateChanged,
    emitTurnSubmitted,
    emitRealmChatMessage,
    emitRulesChatMessage,
    onActionDraftCreated,
    onActionDraftUpdated,
    onActionDraftDeleted,
    onActionDraftReordered,
    onReadyStateChanged,
    onTurnSubmitted,
    onTurnCompleted,
    onRealmChatMessage,
    onRulesChatResponse,
    onMasterTransferred
  }
}
