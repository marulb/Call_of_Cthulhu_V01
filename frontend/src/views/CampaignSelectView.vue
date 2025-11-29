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
    @continue="handleContinue"
    @back="handleBack"
  >
    <!-- Custom create form with campaign settings -->
    <template #create-form="{ onCancel }">
      <form @submit.prevent="handleCreate" class="campaign-create-form">
        <div class="form-group">
          <label>Campaign Name *</label>
          <input v-model="newCampaign.name" required type="text" placeholder="e.g., The Haunting of Blackwood Manor" />
        </div>
        
        <div class="form-group">
          <label>Description</label>
          <textarea v-model="newCampaign.description" placeholder="Brief overview of the campaign" rows="2"></textarea>
        </div>

        <div class="form-divider">
          <span>Campaign Settings (for AI narrative)</span>
        </div>

        <div class="form-group">
          <label>Tone</label>
          <select v-model="newCampaign.tone">
            <option value="">-- Select tone --</option>
            <option value="cosmic horror">Cosmic Horror</option>
            <option value="gothic horror">Gothic Horror</option>
            <option value="pulp adventure">Pulp Adventure</option>
            <option value="mystery noir">Mystery Noir</option>
            <option value="psychological horror">Psychological Horror</option>
            <option value="action thriller">Action Thriller</option>
          </select>
        </div>

        <div class="form-group">
          <label>Goal</label>
          <input v-model="newCampaign.goal" type="text" placeholder="e.g., Investigate strange disappearances in Arkham" />
        </div>

        <div class="form-group">
          <label>Story Elements (comma-separated)</label>
          <input v-model="newCampaign.storyElementsText" type="text" placeholder="e.g., cultists, ancient tome, forbidden knowledge" />
        </div>

        <div class="form-group checkbox-group">
          <label>
            <input type="checkbox" v-model="newCampaign.generateMilestones" />
            Generate story milestones with AI
          </label>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="creating">
            {{ creating ? 'Creating...' : 'Create Campaign' }}
          </button>
          <button type="button" @click="cancelCreate" class="btn-secondary">Cancel</button>
        </div>
      </form>
    </template>

    <!-- Show milestones in entity details -->
    <template #entity-details="{ entity }">
      <div class="campaign-details">
        <div v-if="entity.setting" class="setting-info">
          <p v-if="entity.setting.tone"><strong>Tone:</strong> {{ entity.setting.tone }}</p>
          <p v-if="entity.setting.goal"><strong>Goal:</strong> {{ entity.setting.goal }}</p>
        </div>
        <div v-if="entity.story_arc?.milestones?.length" class="milestones">
          <strong>Story Milestones:</strong>
          <ol>
            <li v-for="(milestone, idx) in entity.story_arc.milestones" :key="idx">
              {{ milestone }}
            </li>
          </ol>
        </div>
      </div>
    </template>
  </EntitySelectionTable>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
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
const creating = ref(false)

const newCampaign = reactive({
  name: '',
  description: '',
  tone: '',
  goal: '',
  storyElementsText: '',
  generateMilestones: true
})

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

async function handleCreate() {
  creating.value = true
  error.value = null
  
  try {
    // Parse story elements from comma-separated text
    const storyElements = newCampaign.storyElementsText
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0)

    // Build setting object if any fields are filled
    const hasSetting = !!(newCampaign.tone || newCampaign.goal || storyElements.length > 0)
    const setting = hasSetting ? {
      tone: newCampaign.tone || undefined,
      goal: newCampaign.goal || undefined,
      story_elements: storyElements.length > 0 ? storyElements : undefined
    } : undefined

    const createdCampaign = await campaignsAPI.create({
      realm_id: sessionStore.selectedRealm!.id,
      name: newCampaign.name,
      description: newCampaign.description || undefined,
      status: 'planning',
      setting,
      generate_milestones: newCampaign.generateMilestones && hasSetting,
      created_by: sessionStore.playerName
    })
    
    campaigns.value.push(createdCampaign)
    sessionStore.setCampaign(createdCampaign)
    resetForm()
  } catch (err: any) {
    error.value = err.message || 'Failed to create campaign'
  } finally {
    creating.value = false
  }
}

function cancelCreate() {
  resetForm()
}

function resetForm() {
  newCampaign.name = ''
  newCampaign.description = ''
  newCampaign.tone = ''
  newCampaign.goal = ''
  newCampaign.storyElementsText = ''
  newCampaign.generateMilestones = true
}

function handleContinue() {
  router.push({ name: 'select-characters' })
}

function handleBack() {
  router.push({ name: 'select-realm' })
}
</script>

<style scoped>
.campaign-create-form {
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
  font-weight: 500;
  color: var(--color-heading);
}

.form-group input[type="text"],
.form-group textarea,
.form-group select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-background);
  color: var(--color-text);
  font-size: 14px;
}

.form-group select {
  cursor: pointer;
}

.form-divider {
  display: flex;
  align-items: center;
  margin: 8px 0;
  color: var(--vt-c-fog);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-divider::before,
.form-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border);
}

.form-divider span {
  padding: 0 12px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: normal;
}

.checkbox-group input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
  border: none;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text);
}

/* Campaign details in expanded view */
.campaign-details {
  padding: 12px;
  background: var(--color-background-soft);
  border-radius: 4px;
}

.setting-info p {
  margin: 4px 0;
}

.milestones {
  margin-top: 12px;
}

.milestones ol {
  margin: 8px 0 0 20px;
  padding: 0;
}

.milestones li {
  margin: 6px 0;
  line-height: 1.4;
}
</style>
