<template>
  <CollapsibleSection title="Relationships">
    <div class="relationships-section">
      <div v-if="relationships.length === 0" class="no-relationships">
        <p>No relationships added yet.</p>
      </div>

      <div v-else class="relationships-list">
        <div v-for="(rel, index) in relationships" :key="index" class="relationship-row">
          <div class="relationship-fields">
            <div class="form-field">
              <label>Target (Name/ID)</label>
              <input
                v-model="rel.object"
                type="text"
                :readonly="readonly"
                placeholder="Person, place, or thing"
              />
            </div>
            <div class="form-field">
              <label>Relationship</label>
              <input
                v-model="rel.relation"
                type="text"
                :readonly="readonly"
                placeholder="e.g., friend, enemy, mentor"
              />
            </div>
          </div>
          <button
            v-if="!readonly"
            @click="removeRelationship(index)"
            class="btn-remove"
            title="Remove relationship"
          >
            −
          </button>
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
import { ref, watch } from 'vue'
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

const relationships = ref<Relationship[]>([...props.modelValue])

watch(() => props.modelValue, (newVal) => {
  relationships.value = [...newVal]
}, { deep: true })

watch(relationships, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

function addRelationship() {
  relationships.value.push({
    object: '',
    relation: ''
  })
}

function removeRelationship(index: number) {
  relationships.value.splice(index, 1)
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
  gap: 12px;
}

.relationship-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.relationship-fields {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

@media (max-width: 768px) {
  .relationship-fields {
    grid-template-columns: 1fr;
  }
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-field label {
  font-weight: 600;
  font-size: 13px;
  color: var(--color-text);
}

.form-field input {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  background: var(--color-background);
  color: var(--color-text);
}

.form-field input:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.form-field input:read-only {
  background: var(--color-background-soft);
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
