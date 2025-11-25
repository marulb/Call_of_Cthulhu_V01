<template>
  <div class="entity-selection">
    <h2>{{ title }}</h2>
    <p v-if="description" class="description">{{ description }}</p>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="selection-container">
      <!-- Entity list -->
      <div v-if="entities.length > 0" class="entity-list">
        <div
          v-for="entity in entities"
          :key="entity.id"
          class="entity-item"
          :class="{ selected: isSelected(entity.id) }"
        >
          <div class="entity-header">
            <input
              v-if="multiSelect"
              type="checkbox"
              :checked="isSelected(entity.id)"
              @change="toggleSelection(entity)"
            />
            <input
              v-else
              type="radio"
              :name="'entity-select'"
              :checked="isSelected(entity.id)"
              @change="selectEntity(entity)"
            />
            <div class="entity-info" @click="toggleDetails(entity.id)">
              <h3>{{ entity.name }}</h3>
              <p v-if="entity.description" class="entity-description">{{
                entity.description
              }}</p>
            </div>
          </div>

          <!-- Expandable details -->
          <div v-if="expandedId === entity.id" class="entity-details">
            <slot name="entity-details" :entity="entity">
              <pre>{{ JSON.stringify(entity, null, 2) }}</pre>
            </slot>
          </div>
        </div>
      </div>

      <div v-else class="no-entities">
        <p>No {{ title.toLowerCase() }} found. Create your first one below!</p>
      </div>

      <!-- Create new entity -->
      <div class="create-section">
        <button v-if="!showCreateForm" @click="handleCreateClick" class="btn-create">
          + Create New {{ entityType }}
        </button>

        <div v-else class="create-form">
          <h3>Create New {{ entityType }}</h3>
          <slot name="create-form" :on-submit="handleCreate" :on-cancel="cancelCreate">
            <form @submit.prevent="handleCreate">
              <div class="form-group">
                <label>Name *</label>
                <input v-model="newEntityName" required type="text" placeholder="Enter name" />
              </div>
              <div class="form-group">
                <label>Description</label>
                <textarea
                  v-model="newEntityDescription"
                  placeholder="Optional description"
                  rows="3"
                ></textarea>
              </div>
              <div class="form-actions">
                <button type="submit" class="btn-primary">Create</button>
                <button type="button" @click="cancelCreate" class="btn-secondary">Cancel</button>
              </div>
            </form>
          </slot>
        </div>
      </div>

      <!-- Navigation buttons -->
      <div class="navigation-buttons">
        <button v-if="showBack" @click="$emit('back')" class="btn-secondary">Back</button>
        <button
          @click="$emit('continue')"
          class="btn-primary"
          :disabled="!canContinue"
        >
          Continue
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Entity {
  id: string
  name: string
  description?: string
  [key: string]: any
}

interface Props {
  title: string
  description?: string
  entities: Entity[]
  selectedIds: string[]
  multiSelect?: boolean
  entityType: string
  loading?: boolean
  error?: string | null
  showBack?: boolean
  useCustomCreate?: boolean  // If true, emit createClick instead of showing built-in form
}

const props = withDefaults(defineProps<Props>(), {
  multiSelect: false,
  loading: false,
  error: null,
  showBack: true,
  useCustomCreate: false
})

const emit = defineEmits<{
  select: [entity: any]
  toggleSelect: [entity: any]
  create: [data: { name: string; description?: string }]
  createClick: []  // Emitted when create button clicked (if useCustomCreate is true)
  continue: []
  back: []
}>()

const expandedId = ref<string | null>(null)
const showCreateForm = ref(false)
const newEntityName = ref('')
const newEntityDescription = ref('')

const canContinue = computed(() => props.selectedIds.length > 0)

function isSelected(id: string): boolean {
  return props.selectedIds.includes(id)
}

function selectEntity(entity: Entity) {
  emit('select', entity)
}

function toggleSelection(entity: Entity) {
  emit('toggleSelect', entity)
}

function toggleDetails(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function handleCreateClick() {
  if (props.useCustomCreate) {
    emit('createClick')
  } else {
    showCreateForm.value = true
  }
}

function handleCreate() {
  emit('create', {
    name: newEntityName.value,
    description: newEntityDescription.value || undefined
  })
  cancelCreate()
}

function cancelCreate() {
  showCreateForm.value = false
  newEntityName.value = ''
  newEntityDescription.value = ''
}
</script>

<style scoped>
.entity-selection {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h2 {
  color: var(--color-heading);
  margin: 0 0 10px 0;
}

.description {
  color: var(--vt-c-fog);
  margin: 0 0 20px 0;
}

.loading,
.error {
  padding: 20px;
  text-align: center;
  border-radius: 8px;
}

.loading {
  background: var(--color-background-soft);
  color: var(--vt-c-fog);
}

.error {
  background: var(--color-background-mute);
  color: var(--vt-c-metallic-accent);
  border-left: 3px solid var(--vt-c-metallic-accent);
}

.selection-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.entity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.entity-item {
  background: var(--color-background);
  border: 2px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.entity-item:hover {
  border-color: var(--vt-c-ink-green-light);
  box-shadow: 0 2px 8px var(--vt-c-divider-light-1);
}

.entity-item.selected {
  border-color: var(--vt-c-ink-green-light);
  background: var(--color-background-mute);
}

.entity-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.entity-header input[type='checkbox'],
.entity-header input[type='radio'] {
  margin-top: 4px;
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--vt-c-ink-green);
}

.entity-info {
  flex: 1;
  cursor: pointer;
}

.entity-info h3 {
  margin: 0 0 4px 0;
  color: var(--color-heading);
  font-size: 16px;
}

.entity-description {
  margin: 0;
  color: var(--vt-c-fog);
  font-size: 14px;
}

.entity-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.entity-details pre {
  background: var(--color-background-soft);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  color: var(--color-text);
}

.no-entities {
  background: var(--color-background-soft);
  padding: 40px 20px;
  text-align: center;
  border-radius: 8px;
  color: var(--vt-c-fog);
}

.create-section {
  border-top: 2px dashed var(--color-border);
  padding-top: 20px;
}

.btn-create {
  width: 100%;
  padding: 12px;
  background: var(--color-background);
  border: 2px dashed var(--vt-c-ink-green-light);
  color: var(--vt-c-ink-green-light);
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create:hover {
  background: var(--color-background-mute);
  border-style: solid;
}

.create-form {
  background: var(--color-background-soft);
  padding: 20px;
  border-radius: 8px;
}

.create-form h3 {
  margin: 0 0 16px 0;
  color: var(--color-heading);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 600;
  color: var(--color-text);
  font-size: 14px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
  background: var(--color-background);
  color: var(--color-text);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.form-actions {
  display: flex;
  gap: 12px;
}

.navigation-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
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
  background: var(--vt-c-ink-green);
  color: var(--vt-c-white);
}

.btn-primary:hover:not(:disabled) {
  background: var(--vt-c-ink-green-light);
}

.btn-primary:disabled {
  background: var(--vt-c-fog);
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-secondary {
  background: var(--color-background-soft);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-background-mute);
  border-color: var(--color-border-hover);
}
</style>
