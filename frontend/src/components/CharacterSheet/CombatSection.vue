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
          <div v-for="(weapon, index) in combat.weapons" :key="index" class="weapon-row">
            <div class="weapon-fields">
              <input
                v-model="weapon.name"
                type="text"
                :readonly="readonly"
                placeholder="Weapon name"
                class="weapon-name"
              />
              <input
                v-model="weapon.skill"
                type="text"
                :readonly="readonly"
                placeholder="Skill"
                class="weapon-skill"
              />
              <input
                v-model="weapon.damage"
                type="text"
                :readonly="readonly"
                placeholder="Damage"
                class="weapon-damage"
              />
              <input
                v-model="weapon.num_attacks"
                type="text"
                :readonly="readonly"
                placeholder="Attacks"
                class="weapon-attacks"
              />
              <input
                v-model="weapon.range"
                type="text"
                :readonly="readonly"
                placeholder="Range"
                class="weapon-range"
              />
              <input
                v-model="weapon.ammo"
                type="text"
                :readonly="readonly"
                placeholder="Ammo"
                class="weapon-ammo"
              />
              <input
                v-model="weapon.malf"
                type="text"
                :readonly="readonly"
                placeholder="Malf"
                class="weapon-malf"
              />
            </div>
            <button
              v-if="!readonly"
              @click="removeWeapon(index)"
              class="btn-remove"
              title="Remove weapon"
            >
              −
            </button>
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
import { ref, watch } from 'vue'
import type { Combat, Weapon } from '@/services/api'
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

const combat = ref<Combat>({ ...props.modelValue })

watch(() => props.modelValue, (newVal) => {
  combat.value = { ...newVal }
}, { deep: true })

watch(combat, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

function addWeapon() {
  combat.value.weapons.push({
    name: '',
    skill: '',
    damage: '',
    num_attacks: '1',
    range: '-',
    ammo: '-',
    malf: '-'
  })
}

function removeWeapon(index: number) {
  combat.value.weapons.splice(index, 1)
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
  gap: 12px;
}

.weapon-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.weapon-fields {
  flex: 1;
  display: grid;
  grid-template-columns: 2fr 2fr 1fr 1fr 1fr 1fr 1fr;
  gap: 8px;
}

@media (max-width: 1024px) {
  .weapon-fields {
    grid-template-columns: 1fr 1fr;
  }
}

.weapon-name,
.weapon-skill,
.weapon-damage,
.weapon-attacks,
.weapon-range,
.weapon-ammo,
.weapon-malf {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 13px;
  background: var(--color-background);
  color: var(--color-text);
}

.weapon-name:focus,
.weapon-skill:focus,
.weapon-damage:focus,
.weapon-attacks:focus,
.weapon-range:focus,
.weapon-ammo:focus,
.weapon-malf:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.weapon-name:read-only,
.weapon-skill:read-only,
.weapon-damage:read-only,
.weapon-attacks:read-only,
.weapon-range:read-only,
.weapon-ammo:read-only,
.weapon-malf:read-only {
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
