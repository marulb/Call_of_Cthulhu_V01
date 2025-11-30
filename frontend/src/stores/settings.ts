/**
 * Pinia store for application settings.
 * Persists TTS voice preferences and other settings to localStorage.
 */
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'coc_settings'

interface StoredSettings {
  voiceName: string
  rate: number
  pitch: number
  volume: number
}

const defaultSettings: StoredSettings = {
  voiceName: '',
  rate: 1.0,
  pitch: 1.0,
  volume: 1.0,
}

export const useSettingsStore = defineStore('settings', () => {
  // ============== STATE ==============

  // TTS / Narration settings
  const voiceName = ref<string>(defaultSettings.voiceName)
  const rate = ref<number>(defaultSettings.rate)
  const pitch = ref<number>(defaultSettings.pitch)
  const volume = ref<number>(defaultSettings.volume)

  // ============== ACTIONS ==============

  function setVoice(name: string) {
    voiceName.value = name
    saveToStorage()
  }

  function setRate(value: number) {
    // Clamp between 0.5 and 2.0
    rate.value = Math.max(0.5, Math.min(2.0, value))
    saveToStorage()
  }

  function setPitch(value: number) {
    // Clamp between 0.5 and 2.0
    pitch.value = Math.max(0.5, Math.min(2.0, value))
    saveToStorage()
  }

  function setVolume(value: number) {
    // Clamp between 0 and 1
    volume.value = Math.max(0, Math.min(1.0, value))
    saveToStorage()
  }

  function resetToDefaults() {
    voiceName.value = defaultSettings.voiceName
    rate.value = defaultSettings.rate
    pitch.value = defaultSettings.pitch
    volume.value = defaultSettings.volume
    saveToStorage()
  }

  // ============== PERSISTENCE ==============

  function loadFromStorage() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<StoredSettings>
        if (parsed.voiceName !== undefined) voiceName.value = parsed.voiceName
        if (parsed.rate !== undefined) rate.value = parsed.rate
        if (parsed.pitch !== undefined) pitch.value = parsed.pitch
        if (parsed.volume !== undefined) volume.value = parsed.volume
      }
    } catch (err) {
      console.warn('Failed to load settings from storage:', err)
    }
  }

  function saveToStorage() {
    try {
      const settings: StoredSettings = {
        voiceName: voiceName.value,
        rate: rate.value,
        pitch: pitch.value,
        volume: volume.value,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch (err) {
      console.warn('Failed to save settings to storage:', err)
    }
  }

  // Load settings on store initialization
  loadFromStorage()

  return {
    // State
    voiceName,
    rate,
    pitch,
    volume,

    // Actions
    setVoice,
    setRate,
    setPitch,
    setVolume,
    resetToDefaults,
    loadFromStorage,
    saveToStorage,
  }
})
