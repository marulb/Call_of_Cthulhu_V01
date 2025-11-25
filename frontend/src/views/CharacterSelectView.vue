<template>
  <div class="character-select-view">
    <EntitySelectionTable
      title="Select Characters"
      description="Choose the characters you'll play (you can select multiple)"
      :entities="characters"
      :selected-ids="selectedIds"
      :multi-select="true"
      entity-type="Character"
      :loading="loading"
      :error="error"
      :use-custom-create="true"
      @toggle-select="handleToggle"
      @createClick="showCreateModal"
      @continue="handleContinue"
      @back="handleBack"
    />

    <!-- Character Creation Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Create New Character</h2>
          <button @click="closeModal" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <CharacterSheetForm
            v-model="newCharacter"
            @submit="handleCreateCharacter"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'
import { charactersAPI } from '@/services/api'
import type { Character } from '@/services/api'
import EntitySelectionTable from '@/components/EntitySelectionTable.vue'
import CharacterSheetForm from '@/components/CharacterSheetForm.vue'

const router = useRouter()
const sessionStore = useGameSessionStore()

const characters = ref<Character[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showModal = ref(false)
const newCharacter = ref<Partial<Character>>({})

const selectedIds = computed(() => sessionStore.selectedCharacters.map((c) => c.id))

onMounted(async () => {
  if (sessionStore.selectedRealm) {
    await loadCharacters()
  }
})

async function loadCharacters() {
  loading.value = true
  error.value = null
  try {
    characters.value = await charactersAPI.list(
      sessionStore.selectedRealm!.id,
      sessionStore.playerName
    )
  } catch (err: any) {
    error.value = err.message || 'Failed to load characters'
  } finally {
    loading.value = false
  }
}

function handleToggle(character: Character) {
  sessionStore.toggleCharacter(character)
}

function showCreateModal() {
  newCharacter.value = {
    name: '',
    realm_id: sessionStore.selectedRealm!.id
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  newCharacter.value = {}
}

async function handleCreateCharacter(characterData: Partial<Character>) {
  try {
    const createdCharacter = await charactersAPI.create({
      realm_id: sessionStore.selectedRealm!.id,
      name: characterData.name!,
      description: characterData.description,
      owner: sessionStore.playerName,
      created_by: sessionStore.playerName,
      data: characterData.data,
      ooc_notes: characterData.ooc_notes,
      profile_completed: characterData.profile_completed
    })
    characters.value.push(createdCharacter)
    sessionStore.toggleCharacter(createdCharacter)
    closeModal()
  } catch (err: any) {
    error.value = err.message || 'Failed to create character'
  }
}

function handleContinue() {
  router.push({ name: 'select-session' })
}

function handleBack() {
  router.push({ name: 'select-campaign' })
}
</script>

<style scoped>
.character-select-view {
  position: relative;
  width: 100%;
  min-height: 100vh;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  overflow-y: auto;
}

.modal-content {
  background: var(--color-background);
  border-radius: 12px;
  width: 100%;
  max-width: 1400px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 2px solid var(--color-border);
}

.modal-header h2 {
  margin: 0;
  color: var(--color-heading);
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-text);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-close:hover {
  background: var(--color-background-mute);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}
</style>
