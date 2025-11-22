<template>
  <EntitySelectionTable
    title="Select World"
    description="Choose the ruleset and lore for your game"
    :entities="worlds"
    :selected-ids="selectedId ? [selectedId] : []"
    entity-type="World"
    :loading="loading"
    :error="error"
    :show-back="false"
    @select="handleSelect"
    @create="handleCreate"
    @continue="handleContinue"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'
import { worldsAPI } from '@/services/api'
import type { World } from '@/services/api'
import EntitySelectionTable from '@/components/EntitySelectionTable.vue'

const router = useRouter()
const sessionStore = useGameSessionStore()

const worlds = ref<World[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const selectedId = computed(() => sessionStore.selectedWorld?.id || null)

onMounted(async () => {
  await loadWorlds()
})

async function loadWorlds() {
  loading.value = true
  error.value = null
  try {
    worlds.value = await worldsAPI.list()
  } catch (err: any) {
    error.value = err.message || 'Failed to load worlds'
  } finally {
    loading.value = false
  }
}

function handleSelect(world: World) {
  sessionStore.setWorld(world)
}

async function handleCreate(data: { name: string; description?: string }) {
  try {
    const newWorld = await worldsAPI.create({
      name: data.name,
      description: data.description,
      created_by: sessionStore.playerName
    })
    worlds.value.push(newWorld)
    sessionStore.setWorld(newWorld)
  } catch (err: any) {
    error.value = err.message || 'Failed to create world'
  }
}

function handleContinue() {
  router.push({ name: 'select-realm' })
}
</script>
