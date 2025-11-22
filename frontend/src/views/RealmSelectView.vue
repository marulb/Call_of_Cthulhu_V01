<template>
  <EntitySelectionTable
    title="Select Realm"
    description="Choose your player group"
    :entities="realms"
    :selected-ids="selectedId ? [selectedId] : []"
    entity-type="Realm"
    :loading="loading"
    :error="error"
    @select="handleSelect"
    @create="handleCreate"
    @continue="handleContinue"
    @back="handleBack"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'
import { realmsAPI } from '@/services/api'
import type { Realm } from '@/services/api'
import EntitySelectionTable from '@/components/EntitySelectionTable.vue'

const router = useRouter()
const sessionStore = useGameSessionStore()

const realms = ref<Realm[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const selectedId = computed(() => sessionStore.selectedRealm?.id || null)

onMounted(async () => {
  if (sessionStore.selectedWorld) {
    await loadRealms()
  }
})

async function loadRealms() {
  loading.value = true
  error.value = null
  try {
    realms.value = await realmsAPI.list(sessionStore.selectedWorld!.id)
  } catch (err: any) {
    error.value = err.message || 'Failed to load realms'
  } finally {
    loading.value = false
  }
}

function handleSelect(realm: Realm) {
  sessionStore.setRealm(realm)
}

async function handleCreate(data: { name: string; description?: string }) {
  try {
    const newRealm = await realmsAPI.create({
      world_id: sessionStore.selectedWorld!.id,
      name: data.name,
      description: data.description,
      created_by: sessionStore.playerName
    })
    realms.value.push(newRealm)
    sessionStore.setRealm(newRealm)
  } catch (err: any) {
    error.value = err.message || 'Failed to create realm'
  }
}

function handleContinue() {
  router.push({ name: 'select-campaign' })
}

function handleBack() {
  router.push({ name: 'select-world' })
}
</script>
