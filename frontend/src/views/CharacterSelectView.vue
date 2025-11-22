<template>
  <EntitySelectionTable
    title="Select Characters"
    description="Choose the characters you'll play (you can select multiple)"
    :entities="characters"
    :selected-ids="selectedIds"
    :multi-select="true"
    entity-type="Character"
    :loading="loading"
    :error="error"
    @toggle-select="handleToggle"
    @create="handleCreate"
    @continue="handleContinue"
    @back="handleBack"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'
import { charactersAPI } from '@/services/api'
import type { Character } from '@/services/api'
import EntitySelectionTable from '@/components/EntitySelectionTable.vue'

const router = useRouter()
const sessionStore = useGameSessionStore()

const characters = ref<Character[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

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

async function handleCreate(data: { name: string; description?: string }) {
  try {
    const newCharacter = await charactersAPI.create({
      realm_id: sessionStore.selectedRealm!.id,
      name: data.name,
      description: data.description,
      owner: sessionStore.playerName,
      created_by: sessionStore.playerName
    })
    characters.value.push(newCharacter)
    sessionStore.toggleCharacter(newCharacter)
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
