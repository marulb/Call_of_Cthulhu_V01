<template>
  <div class="realm-chat">
    <div class="chat-header">
      <h3>Realm Chat</h3>
      <span class="chat-badge">Group</span>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" class="message-item"
        :class="{ 'is-mine': message.player_id === currentPlayerId }">
        <div class="message-header">
          <span class="message-author">{{ message.player_name }}</span>
          <span class="message-time">{{ formatTime(message.timestamp) }}</span>
        </div>
        <div class="message-content">{{ message.message }}</div>
      </div>

      <div v-if="messages.length === 0" class="empty-state">
        <p>No messages yet. Start a conversation!</p>
      </div>
    </div>

    <div class="chat-input">
      <input v-model="newMessage" type="text" placeholder="Type a message..." @keyup.enter="sendMessage"
        :disabled="!connected" />
      <button @click="sendMessage" :disabled="!newMessage.trim() || !connected" class="btn-send">
        Send
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import type { ChatMessage } from '@/types/gameplay'

const props = defineProps<{
  messages: ChatMessage[]
  currentPlayerId: string
  connected: boolean
}>()

const emit = defineEmits<{
  sendMessage: [message: string]
}>()

const newMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

function sendMessage() {
  if (!newMessage.value.trim()) return

  emit('sendMessage', newMessage.value.trim())
  newMessage.value = ''
}

function formatTime(timestamp: string) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

watch(
  () => props.messages.length,
  () => {
    scrollToBottom()
  }
)
</script>

<style scoped>
.realm-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-background);
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--vt-c-divider-light-1);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--vt-c-ink-green-light);
  color: var(--vt-c-white);
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.chat-badge {
  background: var(--vt-c-divider-light-2);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: var(--color-background-soft);
}

/* Scrollbar styles for messages */
.messages-container {
  scrollbar-color: var(--color-scrollbar-thumb) var(--color-scrollbar-track);
  scrollbar-width: thin;
}

.messages-container::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.messages-container::-webkit-scrollbar-track {
  background: var(--color-scrollbar-track);
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--color-scrollbar-thumb);
  border-radius: 8px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: var(--color-scrollbar-thumb-hover);
}

.message-item {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: var(--color-background);
  border-radius: 8px;
  border-left: 3px solid var(--vt-c-ink-green-light);
}

.message-item.is-mine {
  border-left-color: var(--vt-c-metallic-accent);
  background: var(--color-background-mute);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.message-author {
  font-weight: 600;
  font-size: 13px;
  color: var(--color-text);
}

.message-time {
  font-size: 11px;
  color: var(--vt-c-fog);
}

.message-content {
  font-size: 13px;
  line-height: 1.4;
  color: var(--color-text);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--vt-c-fog);
}

.empty-state p {
  margin: 0;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: var(--color-background-soft);
  border-top: 1px solid var(--color-border);
}

.chat-input input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  background: var(--color-background);
  color: var(--color-text);
}

.chat-input input:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.chat-input input:disabled {
  background: var(--color-background-mute);
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-send {
  padding: 10px 20px;
  background: var(--vt-c-ink-green-light);
  color: var(--vt-c-white);
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-send:hover:not(:disabled) {
  background: var(--vt-c-ink-green);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
