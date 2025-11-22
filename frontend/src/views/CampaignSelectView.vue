<template>
  <EntitySelectionTable
    title="Select Campaign"
    description="Choose your story arc"
    :entities="campaigns"
    :selected-ids="selectedId ? [selectedId] : []"
    entity-type="Campaign"
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
import { campaignsAPI } from '@/services/api'
import type { Campaign } from '@/services/api'
import EntitySelectionTable from '@/components/EntitySelectionTable.vue'

const router = useRouter()
const sessionStore = useGameSessionStore()

const campaigns = ref<Campaign[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const selectedId = computed(() => sessionStore.selectedCampaign?.id || null)

onMounted(async () => {
  if (sessionStore.selectedRealm) {
    await loadCampaigns()
  }
})

async function loadCampaigns() {
  loading.value = true
  error.value = null
  try {
    campaigns.value = await campaignsAPI.list(sessionStore.selectedRealm!.id)
  } catch (err: any) {
    error.value = err.message || 'Failed to load campaigns'
  } finally {
    loading.value = false
  }
}

function handleSelect(campaign: Campaign) {
  sessionStore.setCampaign(campaign)
}

async function handleCreate(data: { name: string; description?: string }) {
  try {
    const newCampaign = await campaignsAPI.create({
      realm_id: sessionStore.selectedRealm!.id,
      name: data.name,
      description: data.description,
      status: 'planning',
      created_by: sessionStore.playerName
    })
    campaigns.value.push(newCampaign)
    sessionStore.setCampaign(newCampaign)
  } catch (err: any) {
    error.value = err.message || 'Failed to create campaign'
  }
}

function handleContinue() {
  router.push({ name: 'select-characters' })
}

function handleBack() {
  router.push({ name: 'select-realm' })
}
</script>
