<template>
  <div class="prophet-chat">
    <div class="chat-header">
      <h3>Prophet</h3>
      <span class="chat-badge">AI</span>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" class="message-item"
        :class="{ 'is-ai': message.isAi }">
        <div class="message-header">
          <span class="message-author">
            {{ message.isAi ? 'Prophet' : 'You' }}
          </span>
          <span class="message-time">{{ formatTime(message.timestamp) }}</span>
        </div>
        <div class="message-content">{{ message.message }}</div>
        <div v-if="message.references && message.references.length > 0" class="message-references">
          <strong>References:</strong>
          <ul>
            <li v-for="(ref, refIndex) in message.references" :key="refIndex">{{ ref }}</li>
          </ul>
        </div>
      </div>

      <div v-if="isWaitingForResponse" class="message-item is-ai typing">
        <div class="message-header">
          <span class="message-author">Prophet</span>
        </div>
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <div v-if="messages.length === 0" class="empty-state">
        <div class="ai-info">
          <h4>Prophet - Your Guide to the Unknown</h4>
          <p>Ask me about the mysteries and knowledge of the realm!</p>
          <div class="example-questions">
            <p><strong>Example questions:</strong></p>
            <ul>
              <li>What do I know about this place?</li>
              <li>Tell me about the local legends</li>
              <li>What secrets might be hidden here?</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <textarea v-model="newMessage" placeholder="Ask the Prophet..." rows="2" @keyup.ctrl.enter="sendMessage"
        :disabled="!connected || isWaitingForResponse"></textarea>
      <button @click="sendMessage" :disabled="!newMessage.trim() || !connected || isWaitingForResponse"
        class="btn-send">
        Ask
      </button>
    </div>

    <div class="chat-footer">
      <span class="help-text">Press Ctrl+Enter to send</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'

interface ProphetMessage {
  message: string
  isAi: boolean
  timestamp: string
  references?: string[]
}

const props = defineProps<{
  messages: ProphetMessage[]
  connected: boolean
  isWaitingForResponse: boolean
}>()

const emit = defineEmits<{
  sendMessage: [message: string]
}>()

const newMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

function sendMessage() {
  if (!newMessage.value.trim() || props.isWaitingForResponse) return

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

watch(
  () => props.isWaitingForResponse,
  () => {
    scrollToBottom()
  }
)
</script>

<style scoped>
.prophet-chat {
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
  background: var(--vt-c-metallic-accent);
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

.message-item {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: var(--color-background);
  border-radius: 8px;
  border-left: 3px solid var(--vt-c-ink-green);
}

.message-item.is-ai {
  border-left-color: var(--vt-c-metallic-accent);
  background: var(--color-background-mute);
}

.message-item.typing {
  padding: 16px 12px;
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
  line-height: 1.5;
  color: var(--color-text);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message-references {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
  font-size: 12px;
  color: var(--vt-c-fog);
}

.message-references ul {
  margin: 4px 0 0 0;
  padding-left: 20px;
}

.message-references li {
  margin-bottom: 2px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--vt-c-metallic-accent);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {

  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.5;
  }

  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

.empty-state {
  text-align: center;
  padding: 20px;
}

.ai-info {
  max-width: 300px;
  margin: 0 auto;
}

.ai-info h4 {
  margin: 0 0 8px 0;
  color: var(--vt-c-metallic-accent);
  font-size: 16px;
}

.ai-info>p {
  margin: 0 0 16px 0;
  color: var(--vt-c-fog);
  font-size: 13px;
}

.example-questions {
  background: var(--color-background-mute);
  padding: 12px;
  border-radius: 6px;
  text-align: left;
}

.example-questions p {
  margin: 0 0 6px 0;
  font-size: 12px;
  color: var(--vt-c-fog);
}

.example-questions ul {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: var(--vt-c-fog);
}

.example-questions li {
  margin-bottom: 4px;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: var(--color-background-soft);
  border-top: 1px solid var(--color-border);
}

.chat-input textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  min-height: 42px;
  background: var(--color-background);
  color: var(--color-text);
}

.chat-input textarea:focus {
  outline: none;
  border-color: var(--vt-c-metallic-accent);
}

.chat-input textarea:disabled {
  background: var(--color-background-mute);
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-send {
  padding: 10px 20px;
  background: var(--vt-c-metallic-accent);
  color: var(--vt-c-white);
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  align-self: flex-end;
}

.btn-send:hover:not(:disabled) {
  background: var(--vt-c-ink-green);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-footer {
  padding: 8px 12px;
  background: var(--color-background-soft);
  border-top: 1px solid var(--color-border);
  text-align: center;
}

.help-text {
  font-size: 11px;
  color: var(--vt-c-fog);
}
</style>
