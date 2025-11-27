<template>
  <div class="character-sheet-form">
    <!-- Header with actions -->
    <div class="form-header">
      <h3>Character Sheet<!--{{ character.name || 'New Character' }}--></h3>
      <div class="header-actions">
        <button @click="loadFromJSON" class="btn-secondary" title="Load from JSON file">
          Load
        </button>
        <button @click="saveToJSON" class="btn-secondary" title="Save as JSON file">
          Save
        </button>
        <button
          v-if="!readonly"
          @click="handleSubmit"
          class="btn-primary"
          :disabled="!character.name"
        >
          {{ isGameView ? 'Saved' : 'Create Character' }}
        </button>
        <button v-if="isGameView" @click="emit('close')" class="btn-close" title="Close">✕</button>
      </div>
    </div>

    <!-- Hidden file input for JSON loading -->
    <input
      ref="fileInput"
      type="file"
      accept="application/json"
      style="display: none"
      @change="handleFileLoad"
    />

    <!-- Form Sections -->
    <div class="form-sections">
      <!-- Investigator Info -->
      <CollapsibleSection title="Investigator Info" :initiallyOpen="true">
        <div class="form-grid">
          <div class="form-field">
            <label>Name *</label>
            <input
              v-model="character.name"
              type="text"
              required
              :readonly="readonly"
              placeholder="Character name"
            />
          </div>
          <div class="form-field">
            <label>Occupation</label>
            <input
              v-model="character.data.investigator.occupation"
              type="text"
              :readonly="readonly"
              placeholder="e.g., Detective, Professor"
            />
          </div>
          <div class="form-field">
            <label>Birthplace</label>
            <input
              v-model="character.data.investigator.birthplace"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Pronoun</label>
            <input
              v-model="character.data.investigator.pronoun"
              type="text"
              :readonly="readonly"
              placeholder="e.g., he/him, she/her"
            />
          </div>
          <div class="form-field">
            <label>Residence</label>
            <input
              v-model="character.data.investigator.residence"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Age</label>
            <input
              v-model="character.data.investigator.age"
              type="text"
              :readonly="readonly"
            />
          </div>
        </div>
      </CollapsibleSection>

      <!-- Characteristics -->
      <CollapsibleSection title="Characteristics">
        <div class="characteristics-grid">
          <div v-for="char in characteristicNames" :key="char" class="characteristic-field">
            <label>{{ char }}</label>
            <input
              v-model="character.data.characteristics[char].reg"
              type="text"
              :readonly="readonly"
              placeholder="0"
            />
          </div>
        </div>
      </CollapsibleSection>

      <!-- Points Pools -->
      <CollapsibleSection title="Points & Status">
        <div class="form-grid">
          <div class="form-field">
            <label>Hit Points (Max)</label>
            <input
              v-model="character.data.hit_points.max"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Hit Points (Current)</label>
            <input
              v-model="character.data.hit_points.current"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Magic Points (Max)</label>
            <input
              v-model="character.data.magic_points.max"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Magic Points (Current)</label>
            <input
              v-model="character.data.magic_points.current"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Luck (Starting)</label>
            <input
              v-model="character.data.luck.starting"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Luck (Current)</label>
            <input
              v-model="character.data.luck.current"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Sanity (Max)</label>
            <input
              v-model="character.data.sanity.max"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Sanity (Current)</label>
            <input
              v-model="character.data.sanity.current"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Sanity (Insane)</label>
            <input
              v-model="character.data.sanity.insane"
              type="text"
              :readonly="readonly"
            />
          </div>
        </div>

        <div class="status-checkboxes">
          <label class="checkbox-label">
            <input
              v-model="character.data.status.temporary_insanity"
              type="checkbox"
              :disabled="readonly"
            />
            Temporary Insanity
          </label>
          <label class="checkbox-label">
            <input
              v-model="character.data.status.indefinite_insanity"
              type="checkbox"
              :disabled="readonly"
            />
            Indefinite Insanity
          </label>
          <label class="checkbox-label">
            <input
              v-model="character.data.status.major_wound"
              type="checkbox"
              :disabled="readonly"
            />
            Major Wound
          </label>
          <label class="checkbox-label">
            <input
              v-model="character.data.status.unconscious"
              type="checkbox"
              :disabled="readonly"
            />
            Unconscious
          </label>
          <label class="checkbox-label">
            <input
              v-model="character.data.status.dying"
              type="checkbox"
              :disabled="readonly"
            />
            Dying
          </label>
        </div>
      </CollapsibleSection>

      <!-- Skills -->
      <SkillsSection
        v-model="character.data.skills"
        :readonly="readonly"
        :showUsed="isGameView"
      />

      <!-- Combat -->
      <CombatSection v-model="character.data.combat" :readonly="readonly" />

      <!-- Story -->
      <StorySection v-model="character.data.story" :readonly="readonly" />

      <!-- Gear & Possessions -->
      <CollapsibleSection title="Gear & Possessions">
        <div class="form-field">
          <textarea
            v-model="character.data.gear_possessions"
            :readonly="readonly"
            rows="6"
            placeholder="List your character's equipment and possessions..."
          ></textarea>
        </div>
      </CollapsibleSection>

      <!-- Wealth -->
      <CollapsibleSection title="Wealth">
        <div class="form-grid">
          <div class="form-field">
            <label>Spending Level</label>
            <input
              v-model="character.data.wealth.spending_level"
              type="text"
              :readonly="readonly"
            />
          </div>
          <div class="form-field">
            <label>Cash</label>
            <input v-model="character.data.wealth.cash" type="text" :readonly="readonly" />
          </div>
          <div class="form-field">
            <label>Assets</label>
            <input
              v-model="character.data.wealth.assets"
              type="text"
              :readonly="readonly"
            />
          </div>
        </div>
      </CollapsibleSection>

      <!-- Relationships -->
      <RelationshipsSection
        v-model="character.data.relationships"
        :readonly="readonly"
      />

      <!-- OOC Notes -->
      <CollapsibleSection title="Out of Character Notes">
        <div class="form-field">
          <textarea
            v-model="character.ooc_notes"
            :readonly="readonly"
            rows="6"
            placeholder="Player notes, reminders, and OOC information..."
          ></textarea>
        </div>
      </CollapsibleSection>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Character, CharacterSheet } from '@/services/api'
import CollapsibleSection from './CharacterSheet/CollapsibleSection.vue'
import SkillsSection from './CharacterSheet/SkillsSection.vue'
import CombatSection from './CharacterSheet/CombatSection.vue'
import StorySection from './CharacterSheet/StorySection.vue'
import RelationshipsSection from './CharacterSheet/RelationshipsSection.vue'

interface Props {
  modelValue: Partial<Character>
  readonly?: boolean
  isGameView?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  isGameView: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Partial<Character>): void
  (e: 'submit', value: Partial<Character>): void
  (e: 'close'): void
}>()

// Create a reactive copy of the character
const character = ref<Partial<Character>>(initializeCharacter(props.modelValue))

// Characteristic names
const characteristicNames = ['STR', 'CON', 'DEX', 'APP', 'INT', 'POW', 'SIZ', 'EDU']

// File input ref
const fileInput = ref<HTMLInputElement | null>(null)

// Flag to prevent watch loops
let isUpdating = false

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  if (!isUpdating) {
    character.value = initializeCharacter(newVal)
  }
}, { deep: true })

// Watch for internal changes and emit
watch(character, (newVal) => {
  isUpdating = true
  emit('update:modelValue', newVal)
  setTimeout(() => {
    isUpdating = false
  }, 0)
}, { deep: true })

function initializeCharacter(char: Partial<Character>): Partial<Character> {
  return {
    ...char,
    name: char.name || '',
    ooc_notes: char.ooc_notes || '',
    profile_completed: char.profile_completed || false,
    data: char.data || createEmptyCharacterSheet()
  }
}

function createEmptyCharacterSheet(): CharacterSheet {
  return {
    investigator: {
      name: '',
      birthplace: '',
      pronoun: '',
      occupation: '',
      residence: '',
      age: ''
    },
    characteristics: {
      STR: { reg: '' },
      CON: { reg: '' },
      DEX: { reg: '' },
      APP: { reg: '' },
      INT: { reg: '' },
      POW: { reg: '' },
      SIZ: { reg: '' },
      EDU: { reg: '' }
    },
    hit_points: { max: '', current: '' },
    magic_points: { max: '', current: '' },
    luck: { starting: '', current: '' },
    sanity: { max: '', current: '', insane: '' },
    status: {
      temporary_insanity: false,
      indefinite_insanity: false,
      major_wound: false,
      unconscious: false,
      dying: false
    },
    skills: {},
    combat: {
      weapons: [
        {
          name: 'Brawl',
          skill: 'Fighting (Brawl)',
          damage: '1D3 + DB',
          num_attacks: '1',
          range: '-',
          ammo: '-',
          malf: '-'
        }
      ],
      move: 8,
      build: '',
      damage_bonus: ''
    },
    story: {
      my_story: '',
      backstory: {
        personal_description: '',
        ideology_beliefs: '',
        significant_people: '',
        meaningful_locations: '',
        treasured_possessions: '',
        traits: '',
        injuries_scars: '',
        phobias_manias: '',
        arcane_tomes_spells: '',
        encounters_strange_entities: ''
      }
    },
    gear_possessions: '',
    wealth: {
      spending_level: '',
      cash: '',
      assets: ''
    },
    relationships: []
  }
}

function handleSubmit() {
  if (!character.value.name) {
    alert('Character name is required')
    return
  }

  // Copy base values to reg if reg is empty (only on submit, base not saved to DB)
  if (character.value.data?.skills) {
    Object.entries(character.value.data.skills).forEach(([skillName, skill]) => {
      if (skill.base && !skill.reg) {
        skill.reg = skill.base
      }
      // Remove base from the data that gets sent to backend
      delete (skill as any).base
    })
  }

  // Mark as ready and emit
  character.value.profile_completed = true
  emit('submit', character.value)
}

function loadFromJSON() {
  fileInput.value?.click()
}

function handleFileLoad(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const json = JSON.parse(e.target?.result as string)
      character.value = initializeCharacter(json)
    } catch (err) {
      alert('Invalid JSON file')
      console.error(err)
    }
  }
  reader.readAsText(file)
}

function saveToJSON() {
  const dataStr = JSON.stringify(character.value, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${character.value.name || 'character'}.json`
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.character-sheet-form {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-background);
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--vt-c-divider-light-1);
  overflow: hidden;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
}

.form-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-heading);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--color-text);
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.btn-close:hover {
  background: var(--color-background-mute);
}

.form-sections {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 0;
}

.form-sections > * + * {
  margin-top: 16px;
}

/* Scrollbar styles: WebKit + Firefox friendly */
.form-sections {
  scrollbar-color: var(--color-scrollbar-thumb) var(--color-scrollbar-track);
  scrollbar-width: thin;
}

.form-sections::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.form-sections::-webkit-scrollbar-track {
  background: var(--color-scrollbar-track);
}

.form-sections::-webkit-scrollbar-thumb {
  background: var(--color-scrollbar-thumb);
  border-radius: 8px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.form-sections::-webkit-scrollbar-thumb:hover {
  background: var(--color-scrollbar-thumb-hover);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
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

.form-field input,
.form-field textarea {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  background: var(--color-background);
  color: var(--color-text);
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.form-field input:read-only,
.form-field textarea:read-only {
  background: var(--color-background-soft);
  cursor: not-allowed;
}

.characteristics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.characteristic-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.characteristic-field label {
  font-weight: 700;
  font-size: 12px;
  color: var(--color-text);
  text-align: center;
}

.characteristic-field input {
  padding: 8px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  background: var(--color-background);
  color: var(--color-text);
}

.status-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text);
  cursor: pointer;
}

.checkbox-label input[type='checkbox'] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--vt-c-ink-green);
}

.checkbox-label input[type='checkbox']:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.btn-primary,
.btn-secondary {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
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
