<template>
  <CollapsibleSection title="Relationships">
    <div class="relationships-section">
      <div v-if="relationships.length === 0" class="no-relationships">
        <p>No relationships added yet.</p>
      </div>

      <div v-else class="relationships-list">
        <div v-for="(rel, index) in relationships" :key="`rel-${index}-${rel.object}-${rel.relation}`" class="relationship-card">
          <div class="relationship-header">
            <input
              :value="rel.object"
              @input="updateRelationshipField(index, 'object', ($event.target as HTMLInputElement).value)"
              type="text"
              :readonly="readonly"
              placeholder="Person, place, or thing"
              class="relationship-target-input"
            />
            <button
              v-if="!readonly"
              @click="removeRelationship(index)"
              class="btn-remove"
              title="Remove relationship"
            >
              −
            </button>
          </div>
          <div class="relationship-field">
            <label>Relationship</label>
            <input
              :value="rel.relation"
              @input="updateRelationshipField(index, 'relation', ($event.target as HTMLInputElement).value)"
              type="text"
              :readonly="readonly"
              placeholder="e.g., friend, enemy, mentor"
            />
          </div>
        </div>
      </div>

      <button
        v-if="!readonly"
        @click="addRelationship"
        class="btn-add-relationship"
      >
        + Add Relationship
      </button>
    </div>
  </CollapsibleSection>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Relationship } from '@/services/api'
import CollapsibleSection from './CollapsibleSection.vue'

interface Props {
  modelValue: Relationship[]
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Relationship[]): void
}>()

// Use computed getter for proper reactivity
const relationships = computed(() => props.modelValue)

function updateRelationshipField(index: number, field: string, value: string) {
  const updatedRelationships = relationships.value.map((rel, i) => {
    if (i === index) {
      return { ...rel, [field]: value }
    }
    return rel
  })

  emit('update:modelValue', updatedRelationships)
}

function addRelationship() {
  // Emit new array with added relationship
  emit('update:modelValue', [
    ...relationships.value,
    {
      object: '',
      relation: ''
    }
  ])
}

function removeRelationship(index: number) {
  // Emit new array without the removed relationship
  emit('update:modelValue', relationships.value.filter((_, i) => i !== index))
}
</script>

<style scoped>
.relationships-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.no-relationships {
  text-align: center;
  padding: 24px;
  color: var(--vt-c-fog);
  font-size: 14px;
}

.relationships-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.relationship-card {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.relationship-header {
  display: flex;
  gap: 8px;
  align-items: center;
}

.relationship-target-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 15px;
  font-weight: 600;
  background: var(--color-background);
  color: var(--color-heading);
}

.relationship-target-input:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.relationship-target-input:read-only {
  background: var(--color-background-mute);
  cursor: default;
}

.relationship-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.relationship-field label {
  font-weight: 600;
  font-size: 12px;
  color: var(--color-text);
  opacity: 0.8;
}

.relationship-field input {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 13px;
  background: var(--color-background);
  color: var(--color-text);
}

.relationship-field input:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.relationship-field input:read-only {
  background: var(--color-background-mute);
  cursor: not-allowed;
}

.btn-remove {
  width: 28px;
  height: 28px;
  padding: 0;
  background: var(--color-background-mute);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--vt-c-metallic-accent);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove:hover {
  background: var(--color-background-soft);
  border-color: var(--vt-c-metallic-accent);
}

.btn-add-relationship {
  padding: 10px 16px;
  background: var(--color-background-soft);
  border: 2px dashed var(--vt-c-ink-green-light);
  color: var(--vt-c-ink-green-light);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-relationship:hover {
  background: var(--color-background-mute);
  border-style: solid;
}
</style>
