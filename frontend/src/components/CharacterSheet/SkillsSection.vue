<template>
  <CollapsibleSection title="Skills">
    <div class="skills-section">
      <div class="skills-grid">
        <div v-for="(skill, skillName) in sortedSkills" :key="skillName" class="skill-row">
          <input
            v-model="editableSkillNames[skillName as string]"
            type="text"
            class="skill-name"
            :readonly="readonly"
            @blur="handleSkillNameChange(skillName as string, editableSkillNames[skillName as string])"
          />
          <input
            v-if="!showUsed"
            v-model="skill.base"
            type="text"
            class="skill-base"
            :readonly="readonly"
            placeholder="Base"
          />
          <input
            v-model="skill.reg"
            type="text"
            class="skill-reg"
            :readonly="readonly"
            placeholder="Value"
          />
          <label v-if="showUsed" class="skill-used">
            <input
              v-model="skill.used"
              type="checkbox"
              :disabled="readonly"
            />
            <span>Used</span>
          </label>
          <button
            v-if="!readonly && !isDefaultSkill(skillName as string)"
            @click="removeSkill(skillName as string)"
            class="btn-remove"
            title="Remove skill"
          >
            −
          </button>
        </div>
      </div>

      <button
        v-if="!readonly"
        @click="addSkill"
        class="btn-add-skill"
      >
        + Add Skill
      </button>
    </div>
  </CollapsibleSection>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Skill } from '@/services/api'
import CollapsibleSection from './CollapsibleSection.vue'

interface Props {
  modelValue: Record<string, Skill>
  readonly?: boolean
  showUsed?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  showUsed: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, Skill>): void
}>()

// Default skills from CoC 7th Edition
const defaultSkills: Record<string, string> = {
  'Accounting': '05',
  'Anthropology': '01',
  'Appraise': '05',
  'Archaeology': '01',
  'Art/Craft': '05',
  'Charm': '15',
  'Climb': '20',
  'Credit Rating': '00',
  'Cthulhu Mythos': '00',
  'Disguise': '05',
  'Dodge': 'DEX/2',
  'Drive Auto': '20',
  'Elec. Repair': '10',
  'Fast Talk': '05',
  'Fighting (Brawl)': '25',
  'Firearms (Handgun)': '20',
  'Firearms (Rifle/Shotgun)': '25',
  'First Aid': '30',
  'History': '05',
  'Intimidate': '15',
  'Jump': '20',
  'Language (Own)': 'EDU',
  'Language': '01',
  'Law': '05',
  'Library Use': '20',
  'Listen': '20',
  'Locksmith': '01',
  'Mech. Repair': '10',
  'Medicine': '01',
  'Natural World': '10',
  'Navigate': '10',
  'Occult': '05',
  'Persuade': '10',
  'Pilot': '01',
  'Psychoanalysis': '01',
  'Psychology': '10',
  'Ride': '05',
  'Science': '01',
  'Sleight of Hand': '10',
  'Spot Hidden': '25',
  'Stealth': '20',
  'Survival': '10',
  'Swim': '20',
  'Throw': '20',
  'Track': '10'
}

// Local reactive copy
const skills = ref<Record<string, Skill>>({ ...props.modelValue })

// Editable skill names (for renaming)
const editableSkillNames = ref<Record<string, string>>({})

// Initialize with default skills if empty
if (Object.keys(skills.value).length === 0) {
  Object.entries(defaultSkills).forEach(([name, base]) => {
    skills.value[name] = {
      base,
      reg: '',
      used: false
    }
  })
}

// Initialize editable names
Object.keys(skills.value).forEach(skillName => {
  editableSkillNames.value[skillName] = skillName
})

// Sort skills alphabetically
const sortedSkills = computed(() => {
  const sorted: Record<string, Skill> = {}
  Object.keys(skills.value)
    .sort((a, b) => a.localeCompare(b))
    .forEach(key => {
      sorted[key] = skills.value[key]
    })
  return sorted
})

// Watch for external changes
watch(() => props.modelValue, (newVal) => {
  skills.value = { ...newVal }
  Object.keys(skills.value).forEach(skillName => {
    if (!editableSkillNames.value[skillName]) {
      editableSkillNames.value[skillName] = skillName
    }
  })
}, { deep: true })

// Watch for internal changes and emit
watch(skills, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

function isDefaultSkill(skillName: string): boolean {
  return skillName in defaultSkills
}

function addSkill() {
  const newSkillName = 'New Skill'
  let counter = 1
  let finalName = newSkillName

  while (finalName in skills.value) {
    finalName = `${newSkillName} ${counter}`
    counter++
  }

  skills.value[finalName] = {
    base: '00',
    reg: '',
    used: false
  }
  editableSkillNames.value[finalName] = finalName
}

function removeSkill(skillName: string) {
  delete skills.value[skillName]
  delete editableSkillNames.value[skillName]
}

function handleSkillNameChange(oldName: string, newName: string) {
  if (oldName === newName || !newName.trim()) return

  // Check if new name already exists
  if (newName in skills.value && newName !== oldName) {
    alert('A skill with this name already exists')
    editableSkillNames.value[oldName] = oldName
    return
  }

  // Rename the skill
  const skillData = skills.value[oldName]
  delete skills.value[oldName]
  skills.value[newName] = skillData
  delete editableSkillNames.value[oldName]
  editableSkillNames.value[newName] = newName
}
</script>

<style scoped>
.skills-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skills-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skill-row {
  display: grid;
  grid-template-columns: 1fr auto auto auto auto;
  gap: 8px;
  align-items: center;
}

@media (max-width: 768px) {
  .skill-row {
    grid-template-columns: 1fr auto auto;
  }
}

.skill-name {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  background: var(--color-background);
  color: var(--color-text);
}

.skill-base,
.skill-reg {
  width: 80px;
  padding: 6px 8px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 13px;
  text-align: center;
  background: var(--color-background);
  color: var(--color-text);
}

.skill-name:focus,
.skill-base:focus,
.skill-reg:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.skill-name:read-only,
.skill-base:read-only,
.skill-reg:read-only {
  background: var(--color-background-soft);
  cursor: not-allowed;
}

.skill-used {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text);
  cursor: pointer;
  white-space: nowrap;
}

.skill-used input[type='checkbox'] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--vt-c-ink-green);
}

.skill-used input[type='checkbox']:disabled {
  cursor: not-allowed;
  opacity: 0.5;
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
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove:hover {
  background: var(--color-background-soft);
  border-color: var(--vt-c-metallic-accent);
}

.btn-add-skill {
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

.btn-add-skill:hover {
  background: var(--color-background-mute);
  border-style: solid;
}
</style>
