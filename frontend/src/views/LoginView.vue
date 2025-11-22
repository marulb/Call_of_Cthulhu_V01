<template>
  <div class="login-container">
    <div class="login-card">
      <h1>Call of Cthulhu</h1>
      <p class="subtitle">Campaign Management System</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="playerName">Player Name</label>
          <input
            id="playerName"
            v-model="playerName"
            type="text"
            placeholder="Enter your name"
            required
            autofocus
            class="input-field"
          />
          <p class="hint">This is your real-world player name, not your character name</p>
        </div>

        <button type="submit" class="btn-primary" :disabled="!playerName.trim()">
          Continue
        </button>

        <button
          v-if="hasStoredName"
          type="button"
          class="btn-secondary"
          @click="loadStoredName"
        >
          Use Previous Name: {{ storedName }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'

const router = useRouter()
const sessionStore = useGameSessionStore()

const playerName = ref('')
const storedName = ref('')

const hasStoredName = computed(() => storedName.value.length > 0)

onMounted(() => {
  // Check if there's a stored player name
  const stored = localStorage.getItem('coc_player_name')
  if (stored) {
    storedName.value = stored
  }
})

function handleLogin() {
  if (playerName.value.trim()) {
    sessionStore.setPlayerName(playerName.value)
    router.push({ name: 'select-world' })
  }
}

function loadStoredName() {
  if (storedName.value) {
    playerName.value = storedName.value
    handleLogin()
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 20px;
}

.login-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  max-width: 450px;
  width: 100%;
}

h1 {
  color: #1a1a2e;
  margin: 0 0 10px 0;
  font-size: 32px;
  text-align: center;
}

.subtitle {
  color: #666;
  text-align: center;
  margin: 0 0 30px 0;
  font-size: 14px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.input-field {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.input-field:focus {
  outline: none;
  border-color: #4a90e2;
}

.hint {
  font-size: 12px;
  color: #999;
  margin: 0;
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
}

.btn-primary:hover:not(:disabled) {
  background: #357abd;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}
</style>
