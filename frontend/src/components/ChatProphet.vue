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
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #ff9800;
  color: white;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.chat-badge {
  background: rgba(255, 255, 255, 0.2);
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
  background: #f9f9f9;
}

.message-item {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: white;
  border-radius: 8px;
  border-left: 3px solid #4caf50;
}

.message-item.is-ai {
  border-left-color: #ff9800;
  background: #fff9f0;
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
  color: #333;
}

.message-time {
  font-size: 11px;
  color: #999;
}

.message-content {
  font-size: 13px;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message-references {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: #666;
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
  background: #ff9800;
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
  color: #ff9800;
  font-size: 16px;
}

.ai-info>p {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 13px;
}

.example-questions {
  background: #fff9f0;
  padding: 12px;
  border-radius: 6px;
  text-align: left;
}

.example-questions p {
  margin: 0 0 6px 0;
  font-size: 12px;
  color: #666;
}

.example-questions ul {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: #666;
}

.example-questions li {
  margin-bottom: 4px;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: #f8f8f8;
  border-top: 1px solid #e0e0e0;
}

.chat-input textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  min-height: 42px;
}

.chat-input textarea:focus {
  outline: none;
  border-color: #ff9800;
}

.chat-input textarea:disabled {
  background: #f0f0f0;
  cursor: not-allowed;
}

.btn-send {
  padding: 10px 20px;
  background: #ff9800;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  align-self: flex-end;
}

.btn-send:hover:not(:disabled) {
  background: #f57c00;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-footer {
  padding: 8px 12px;
  background: #f8f8f8;
  border-top: 1px solid #e0e0e0;
  text-align: center;
}

.help-text {
  font-size: 11px;
  color: #999;
}
</style>
