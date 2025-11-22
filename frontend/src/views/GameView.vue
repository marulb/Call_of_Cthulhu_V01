<template>
  <div class="game-view">
    <div class="game-header">
      <h1>{{ sessionStore.selectedCampaign?.name }}</h1>
      <p class="session-info">
        Session #{{ sessionStore.currentSession?.session_number }} •
        {{ sessionStore.selectedRealm?.name }}
      </p>
    </div>

    <div class="game-content">
      <div class="placeholder">
        <h2>Game Session View</h2>
        <p>This is where the actual game session interface will be implemented.</p>

        <div class="context-info">
          <h3>Current Context:</h3>
          <ul>
            <li><strong>Player:</strong> {{ sessionStore.playerName }}</li>
            <li><strong>World:</strong> {{ sessionStore.selectedWorld?.name }}</li>
            <li><strong>Realm:</strong> {{ sessionStore.selectedRealm?.name }}</li>
            <li><strong>Campaign:</strong> {{ sessionStore.selectedCampaign?.name }}</li>
            <li>
              <strong>Characters:</strong>
              {{ sessionStore.selectedCharacters.map((c) => c.name).join(', ') }}
            </li>
            <li><strong>Session:</strong> #{{ sessionStore.currentSession?.session_number }}</li>
          </ul>
        </div>

        <button @click="endSession" class="btn-secondary">End Session</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'

const router = useRouter()
const sessionStore = useGameSessionStore()

function endSession() {
  if (confirm('Are you sure you want to end this session?')) {
    sessionStore.resetSession()
    router.push({ name: 'login' })
  }
}
</script>

<style scoped>
.game-view {
  min-height: 100vh;
  background: #f5f5f5;
}

.game-header {
  background: white;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.game-header h1 {
  margin: 0 0 8px 0;
  color: #1a1a2e;
}

.session-info {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.game-content {
  padding: 40px 20px;
}

.placeholder {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.placeholder h2 {
  margin: 0 0 16px 0;
  color: #333;
}

.placeholder p {
  color: #666;
  margin-bottom: 32px;
}

.context-info {
  background: #f9f9f9;
  padding: 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  text-align: left;
}

.context-info h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.context-info ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.context-info li {
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
}

.context-info li:last-child {
  border-bottom: none;
}

.btn-secondary {
  padding: 12px 24px;
  background: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #e0e0e0;
}
</style>
