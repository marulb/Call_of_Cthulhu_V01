<template>
  <CollapsibleSection title="Combat">
    <div class="combat-section">
      <!-- Combat Stats -->
      <div class="combat-stats">
        <div class="form-field">
          <label>Move</label>
          <input
            v-model.number="combat.move"
            type="number"
            :readonly="readonly"
          />
        </div>
        <div class="form-field">
          <label>Build</label>
          <input
            v-model="combat.build"
            type="text"
            :readonly="readonly"
          />
        </div>
        <div class="form-field">
          <label>Damage Bonus</label>
          <input
            v-model="combat.damage_bonus"
            type="text"
            :readonly="readonly"
          />
        </div>
      </div>

      <!-- Weapons -->
      <div class="weapons-section">
        <h4>Weapons</h4>
        <div class="weapons-list">
          <div v-for="(weapon, index) in visibleWeapons" :key="index" class="weapon-card">
            <div class="weapon-header">
              <input
                :value="weapon.name"
                @input="updateWeaponField(index, 'name', ($event.target as HTMLInputElement).value)"
                type="text"
                :readonly="readonly"
                placeholder="Weapon name"
                class="weapon-name-input"
              />
              <button
                v-if="!readonly"
                @click="removeWeapon(index)"
                class="btn-remove"
                title="Remove weapon"
              >
                −
              </button>
            </div>
            <div class="weapon-attributes">
              <div class="weapon-field">
                <label>Skill</label>
                <input
                  :value="weapon.skill"
                  @input="updateWeaponField(index, 'skill', ($event.target as HTMLInputElement).value)"
                  type="text"
                  :readonly="readonly"
                  placeholder="Skill %"
                />
              </div>
              <div class="weapon-field">
                <label>Damage</label>
                <input
                  :value="weapon.damage"
                  @input="updateWeaponField(index, 'damage', ($event.target as HTMLInputElement).value)"
                  type="text"
                  :readonly="readonly"
                  placeholder="e.g. 1D6"
                />
              </div>
              <div class="weapon-field">
                <label>Attacks</label>
                <input
                  :value="weapon.num_attacks"
                  @input="updateWeaponField(index, 'num_attacks', ($event.target as HTMLInputElement).value)"
                  type="text"
                  :readonly="readonly"
                  placeholder="e.g. 1"
                />
              </div>
              <div class="weapon-field">
                <label>Range</label>
                <input
                  :value="weapon.range"
                  @input="updateWeaponField(index, 'range', ($event.target as HTMLInputElement).value)"
                  type="text"
                  :readonly="readonly"
                  placeholder="e.g. 10m"
                />
              </div>
              <div class="weapon-field">
                <label>Ammo</label>
                <input
                  :value="weapon.ammo"
                  @input="updateWeaponField(index, 'ammo', ($event.target as HTMLInputElement).value)"
                  type="text"
                  :readonly="readonly"
                  placeholder="e.g. 6"
                />
              </div>
              <div class="weapon-field">
                <label>Malf</label>
                <input
                  :value="weapon.malf"
                  @input="updateWeaponField(index, 'malf', ($event.target as HTMLInputElement).value)"
                  type="text"
                  :readonly="readonly"
                  placeholder="e.g. 00"
                />
              </div>
            </div>
          </div>
        </div>

        <button
          v-if="!readonly"
          @click="addWeapon"
          class="btn-add-weapon"
        >
          + Add Weapon
        </button>
      </div>
    </div>
  </CollapsibleSection>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Combat } from '@/services/api'
import CollapsibleSection from './CollapsibleSection.vue'

interface Props {
  modelValue: Combat
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Combat): void
}>()

// Use computed getter/setter for proper two-way binding
const combat = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Show all weapons
const visibleWeapons = computed(() => {
  return combat.value.weapons || []
})

function updateWeaponField(index: number, field: string, value: string) {
  const weapons = combat.value.weapons || []
  const updatedWeapons = weapons.map((weapon, i) => {
    if (i === index) {
      return { ...weapon, [field]: value }
    }
    return weapon
  })

  emit('update:modelValue', {
    ...combat.value,
    weapons: updatedWeapons
  })
}

function addWeapon() {
  const weapons = combat.value.weapons || []

  // Create new combat object with updated weapons array
  const newWeapons = [
    ...weapons,
    {
      name: '',
      skill: '',
      damage: '',
      num_attacks: '1',
      range: '-',
      ammo: '-',
      malf: '-'
    }
  ]

  emit('update:modelValue', {
    ...combat.value,
    weapons: newWeapons
  })
}

function removeWeapon(index: number) {
  const weapons = combat.value.weapons || []

  // Create new combat object with updated weapons array
  emit('update:modelValue', {
    ...combat.value,
    weapons: weapons.filter((_, i) => i !== index)
  })
}
</script>

<style scoped>
.combat-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.combat-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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

.weapons-section h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-heading);
}

.weapons-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.weapon-card {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.weapon-header {
  display: flex;
  gap: 8px;
  align-items: center;
}

.weapon-name-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 15px;
  font-weight: 600;
  background: var(--color-background);
  color: var(--color-heading);
}

.weapon-name-input:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.weapon-name-input:read-only {
  background: var(--color-background-mute);
  cursor: default;
}

.weapon-attributes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.weapon-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.weapon-field label {
  font-weight: 600;
  font-size: 12px;
  color: var(--color-text);
  opacity: 0.8;
}

.weapon-field input {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 13px;
  background: var(--color-background);
  color: var(--color-text);
}

.weapon-field input:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.weapon-field input:read-only {
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

.btn-add-weapon {
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

.btn-add-weapon:hover {
  background: var(--color-background-mute);
  border-style: solid;
}
</style>
