<template>
  <div class="visibility-list">
    <div class="visibility-header">
      <h4>View</h4>
      <button class="btn-settings" title="Settings (coming soon)" disabled>⚙</button>
    </div>

    <div class="visibility-items">
      <div
        v-for="container in containers"
        :key="container.id"
        class="visibility-item"
        @click="toggleVisibility(container.id)"
      >
        <span class="container-name">{{ container.name }}</span>
        <button
          class="btn-eye"
          :class="{ 'visible': container.visible }"
          :title="container.visible ? 'Hide' : 'Show'"
        >
          <span v-if="container.visible">👁</span>
          <span v-else class="eye-closed">👁</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface VisibilityContainer {
  id: string
  name: string
  visible: boolean
}

const props = defineProps<{
  containers: VisibilityContainer[]
}>()

const emit = defineEmits<{
  toggleVisibility: [containerId: string]
}>()

function toggleVisibility(containerId: string) {
  emit('toggleVisibility', containerId)
}
</script>

<style scoped>
.visibility-list {
  display: flex;
  flex-direction: column;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.visibility-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.visibility-header h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-heading);
}

.btn-settings {
  background: none;
  border: none;
  font-size: 14px;
  color: var(--color-text-mute);
  cursor: not-allowed;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  opacity: 0.4;
}

.visibility-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px;
}

.visibility-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
  gap: 8px;
}

.visibility-item:hover {
  background: var(--color-background-mute);
}

.container-name {
  flex: 1;
  font-size: 11px;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-eye {
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.btn-eye span {
  display: inline-block;
  transition: opacity 0.2s;
}

.btn-eye .eye-closed {
  opacity: 0.3;
  filter: grayscale(100%);
}

.btn-eye.visible span {
  opacity: 1;
}

.btn-eye:hover {
  transform: scale(1.15);
}
</style>
