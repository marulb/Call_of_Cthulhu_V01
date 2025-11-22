<template>
  <div class="session-select">
    <h2>Session Selection</h2>
    <p class="description">Start a new session or continue from the previous one</p>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="session-options">
      <!-- Continue Previous Session -->
      <div v-if="latestSession" class="session-option">
        <h3>Continue Previous Session</h3>
        <div class="session-info">
          <p><strong>Session #{{ latestSession.session_number }}</strong></p>
          <p v-if="latestSession.notes">{{ latestSession.notes }}</p>
          <p class="meta">
            Created: {{ new Date(latestSession.meta.created_at).toLocaleDateString() }}
          </p>
        </div>
        <button @click="continueSession" class="btn-primary">Continue Session</button>
      </div>

      <!-- New Session -->
      <div class="session-option">
        <h3>Start New Session</h3>
        <form @submit.prevent="createNewSession" class="session-form">
          <div class="form-group">
            <label>Session Number</label>
            <input
              v-model.number="newSessionNumber"
              type="number"
              min="1"
              required
              readonly
            />
          </div>
          <div class="form-group">
            <label>Notes (optional)</label>
            <textarea
              v-model="sessionNotes"
              placeholder="Session plan or notes..."
              rows="3"
            ></textarea>
          </div>
          <button type="submit" class="btn-primary">Start New Session</button>
        </form>
      </div>

      <!-- Back Button -->
      <div class="navigation">
        <button @click="handleBack" class="btn-secondary">Back</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'
import { sessionsAPI } from '@/services/api'
import type { Session } from '@/services/api'

const router = useRouter()
const sessionStore = useGameSessionStore()

const latestSession = ref<Session | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const sessionNotes = ref('')

const newSessionNumber = computed(() => {
  return latestSession.value ? latestSession.value.session_number + 1 : 1
})

onMounted(async () => {
  if (sessionStore.selectedRealm && sessionStore.selectedCampaign) {
    await loadLatestSession()
  }
})

async function loadLatestSession() {
  loading.value = true
  error.value = null
  try {
    latestSession.value = await sessionsAPI.getLatest(
      sessionStore.selectedRealm!.id,
      sessionStore.selectedCampaign!.id
    )
  } catch (err: any) {
    error.value = err.message || 'Failed to load session'
  } finally {
    loading.value = false
  }
}

function continueSession() {
  if (latestSession.value) {
    sessionStore.setSession(latestSession.value)
    router.push({ name: 'game' })
  }
}

async function createNewSession() {
  try {
    const newSession = await sessionsAPI.create({
      realm_id: sessionStore.selectedRealm!.id,
      campaign_id: sessionStore.selectedCampaign!.id,
      session_number: newSessionNumber.value,
      players_present: [sessionStore.playerName],
      notes: sessionNotes.value || undefined,
      created_by: sessionStore.playerName
    })
    sessionStore.setSession(newSession)
    router.push({ name: 'game' })
  } catch (err: any) {
    error.value = err.message || 'Failed to create session'
  }
}

function handleBack() {
  router.push({ name: 'select-characters' })
}
</script>

<style scoped>
.session-select {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h2 {
  color: #1a1a2e;
  margin: 0 0 10px 0;
}

.description {
  color: #666;
  margin: 0 0 20px 0;
}

.loading,
.error {
  padding: 20px;
  text-align: center;
  border-radius: 8px;
}

.loading {
  background: #f0f0f0;
  color: #666;
}

.error {
  background: #fee;
  color: #c00;
}

.session-options {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.session-option {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 24px;
}

.session-option h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.session-info {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.session-info p {
  margin: 0 0 8px 0;
}

.session-info .meta {
  color: #999;
  font-size: 12px;
}

.session-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.form-group input,
.form-group textarea {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #4a90e2;
}

.navigation {
  display: flex;
  justify-content: flex-start;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4a90e2;
  color: white;
  width: 100%;
}

.btn-primary:hover {
  background: #357abd;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}
</style>
