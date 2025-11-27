<template>
  <div class="collapsible-section">
    <div class="section-header" @click="toggle">
      <h3>{{ title }}</h3>
      <span class="toggle-icon" :class="{ open: isOpen }">▼</span>
    </div>
    <div v-show="isOpen" class="section-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  title: string
  initiallyOpen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  initiallyOpen: false
})

const isOpen = ref(props.initiallyOpen)

function toggle() {
  isOpen.value = !isOpen.value
}
</script>

<style scoped>
.collapsible-section {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-background-soft);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.section-header:hover {
  background: var(--color-background-mute);
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-heading);
}

.toggle-icon {
  font-size: 12px;
  color: var(--color-text);
  transition: transform 0.2s;
}

.toggle-icon.open {
  transform: rotate(180deg);
}

.section-content {
  padding: 16px;
  background: var(--color-background);
}
</style>
