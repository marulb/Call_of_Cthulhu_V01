<template>
  <div class="settings-overlay" @click.self="emit('close')">
    <div class="settings-modal">
      <div class="modal-header">
        <h2>⚙ Session Settings</h2>
        <button @click="emit('close')" class="btn-close" title="Close">✕</button>
      </div>

      <div class="modal-body">
        <!-- Storyteller Voice Section -->
        <div class="settings-section" :class="{ expanded: expandedSections.voice }">
          <div class="section-header" @click="toggleSection('voice')">
            <span class="section-icon">{{ expandedSections.voice ? '▼' : '▶' }}</span>
            <h3>🎭 Storyteller Voice</h3>
          </div>
          <div v-show="expandedSections.voice" class="section-content">
            <div class="setting-row">
              <label for="voice-select">Voice</label>
              <select id="voice-select" v-model="selectedVoiceName" @change="onVoiceChange">
                <option value="">-- Select Voice --</option>
                <option v-for="voice in englishVoices" :key="voice.name" :value="voice.name">
                  {{ voice.name }} ({{ voice.lang }})
                </option>
              </select>
            </div>

            <div class="setting-row">
              <label for="rate-slider">Speed</label>
              <div class="slider-container">
                <input
                  id="rate-slider"
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  v-model.number="localRate"
                  @input="onRateChange"
                />
                <span class="slider-value">{{ localRate.toFixed(1) }}x</span>
              </div>
            </div>

            <div class="setting-row">
              <label for="pitch-slider">Pitch</label>
              <div class="slider-container">
                <input
                  id="pitch-slider"
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  v-model.number="localPitch"
                  @input="onPitchChange"
                />
                <span class="slider-value">{{ localPitch.toFixed(1) }}</span>
              </div>
            </div>

            <div class="setting-row">
              <label for="volume-slider">Volume</label>
              <div class="slider-container">
                <input
                  id="volume-slider"
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  v-model.number="localVolume"
                  @input="onVolumeChange"
                />
                <span class="slider-value">{{ Math.round(localVolume * 100) }}%</span>
              </div>
            </div>

            <div class="test-area">
              <label for="test-text">Test your settings</label>
              <textarea
                id="test-text"
                v-model="testText"
                placeholder="Enter text to test the voice..."
                rows="3"
              ></textarea>
              <div class="test-actions">
                <button @click="playTest" class="btn-test" :disabled="!testText.trim()">
                  {{ isSpeaking ? '■ Stop' : '▶ Play' }}
                </button>
                <button @click="resetSettings" class="btn-reset">Reset to Defaults</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Display Options Section (placeholder for future) -->
        <div class="settings-section" :class="{ expanded: expandedSections.display }">
          <div class="section-header" @click="toggleSection('display')">
            <span class="section-icon">{{ expandedSections.display ? '▼' : '▶' }}</span>
            <h3>🖥️ Display Options</h3>
          </div>
          <div v-show="expandedSections.display" class="section-content">
            <p class="placeholder-text">Display settings coming soon...</p>
          </div>
        </div>

        <!-- Notifications Section (placeholder for future) -->
        <div class="settings-section" :class="{ expanded: expandedSections.notifications }">
          <div class="section-header" @click="toggleSection('notifications')">
            <span class="section-icon">{{ expandedSections.notifications ? '▼' : '▶' }}</span>
            <h3>🔔 Notifications</h3>
          </div>
          <div v-show="expandedSections.notifications" class="section-content">
            <p class="placeholder-text">Notification settings coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useSpeechSynthesis } from '@/composables/useSpeechSynthesis'
import { useSettingsStore } from '@/stores/settings'

const emit = defineEmits<{
  close: []
}>()

const settingsStore = useSettingsStore()
const {
  englishVoices,
  isSpeaking,
  speak,
  stop,
  loadVoices,
} = useSpeechSynthesis()

// Collapsible sections state
const expandedSections = ref({
  voice: true,
  display: false,
  notifications: false,
})

function toggleSection(section: keyof typeof expandedSections.value) {
  expandedSections.value[section] = !expandedSections.value[section]
}

// Local state for form inputs (synced with store)
const selectedVoiceName = ref(settingsStore.voiceName)
const localRate = ref(settingsStore.rate)
const localPitch = ref(settingsStore.pitch)
const localVolume = ref(settingsStore.volume)

// Test area
const testText = ref('The fog rolled in from the harbor, bringing with it whispers of things best left forgotten...')

function onVoiceChange() {
  settingsStore.setVoice(selectedVoiceName.value)
}

function onRateChange() {
  settingsStore.setRate(localRate.value)
}

function onPitchChange() {
  settingsStore.setPitch(localPitch.value)
}

function onVolumeChange() {
  settingsStore.setVolume(localVolume.value)
}

function playTest() {
  if (isSpeaking.value) {
    stop()
  } else if (testText.value.trim()) {
    speak(testText.value, 0)
  }
}

function resetSettings() {
  settingsStore.resetToDefaults()
  // Sync local state
  selectedVoiceName.value = settingsStore.voiceName
  localRate.value = settingsStore.rate
  localPitch.value = settingsStore.pitch
  localVolume.value = settingsStore.volume
}

// Handle Escape key to close
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  loadVoices()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  stop()
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.settings-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.settings-modal {
  background: var(--color-background);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid var(--color-border);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--vt-c-deep-sea);
  border-bottom: 1px solid var(--color-border);
  border-radius: 12px 12px 0 0;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--vt-c-white);
}

.btn-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--vt-c-white);
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.15);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Settings Sections */
.settings-section {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.settings-section.expanded {
  border-color: var(--vt-c-ink-green-light);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--color-background-soft);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.section-header:hover {
  background: var(--color-background-mute);
}

.section-icon {
  font-size: 10px;
  color: var(--vt-c-fog);
  width: 12px;
}

.section-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-heading);
}

.section-content {
  padding: 16px;
  background: var(--color-background);
  border-top: 1px solid var(--color-border);
}

/* Setting Rows */
.setting-row {
  margin-bottom: 16px;
}

.setting-row:last-child {
  margin-bottom: 0;
}

.setting-row label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 6px;
}

.setting-row select {
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
}

.setting-row select:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

/* Sliders */
.slider-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider-container input[type='range'] {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--color-border);
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.slider-container input[type='range']::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--vt-c-ink-green-light);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.slider-container input[type='range']::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--vt-c-ink-green-light);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.slider-value {
  min-width: 45px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
  color: var(--vt-c-metallic-accent);
}

/* Test Area */
.test-area {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.test-area label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}

.test-area textarea {
  width: 100%;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.5;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-background);
  color: var(--color-text);
  resize: vertical;
  font-family: inherit;
}

.test-area textarea:focus {
  outline: none;
  border-color: var(--vt-c-ink-green-light);
}

.test-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.btn-test {
  flex: 1;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  background: var(--vt-c-ink-green);
  color: var(--vt-c-white);
  cursor: pointer;
  transition: background 0.2s;
}

.btn-test:hover:not(:disabled) {
  background: var(--vt-c-deep-sea);
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-reset {
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 600;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.btn-reset:hover {
  background: var(--color-background-soft);
  border-color: var(--vt-c-fog);
}

/* Placeholder text */
.placeholder-text {
  color: var(--vt-c-fog);
  font-size: 13px;
  font-style: italic;
  margin: 0;
}
</style>
