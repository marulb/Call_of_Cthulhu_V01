<template>
  <CollapsibleSection title="Story & Backstory">
    <div class="story-section">
      <div class="form-field">
        <label>My Story</label>
        <textarea
          v-model="story.my_story"
          :readonly="readonly"
          rows="4"
          placeholder="Write your character's story..."
        ></textarea>
      </div>

      <div class="backstory-section">
        <h4>Backstory Details</h4>
        <div class="backstory-grid">
          <div class="form-field">
            <label>Personal Description</label>
            <textarea
              v-model="story.backstory.personal_description"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Ideology & Beliefs</label>
            <textarea
              v-model="story.backstory.ideology_beliefs"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Significant People</label>
            <textarea
              v-model="story.backstory.significant_people"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Meaningful Locations</label>
            <textarea
              v-model="story.backstory.meaningful_locations"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Treasured Possessions</label>
            <textarea
              v-model="story.backstory.treasured_possessions"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Traits</label>
            <textarea
              v-model="story.backstory.traits"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Injuries & Scars</label>
            <textarea
              v-model="story.backstory.injuries_scars"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Phobias & Manias</label>
            <textarea
              v-model="story.backstory.phobias_manias"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Arcane Tomes & Spells</label>
            <textarea
              v-model="story.backstory.arcane_tomes_spells"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
          <div class="form-field">
            <label>Encounters with Strange Entities</label>
            <textarea
              v-model="story.backstory.encounters_strange_entities"
              :readonly="readonly"
              rows="3"
            ></textarea>
          </div>
        </div>
      </div>
    </div>
  </CollapsibleSection>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Story } from '@/services/api'
import CollapsibleSection from './CollapsibleSection.vue'

interface Props {
  modelValue: Story
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Story): void
}>()

const story = ref<Story>({ ...props.modelValue })

watch(() => props.modelValue, (newVal) => {
  story.value = { ...newVal }
}, { deep: true })

watch(story, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })
</script>

<style scoped>
.story-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
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

.form-field textarea {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  background: var(--color-background);
  color: var(--color-text);
}

.form-field textarea:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.form-field textarea:read-only {
  background: var(--color-background-soft);
  cursor: not-allowed;
}

.backstory-section h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-heading);
}

.backstory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}
</style>
