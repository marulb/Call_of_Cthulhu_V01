/**
 * Web Speech Synthesis composable for TTS narration.
 * Provides play/stop controls with text selection support.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'

export function useSpeechSynthesis() {
  const settingsStore = useSettingsStore()

  // State
  const voices = ref<SpeechSynthesisVoice[]>([])
  const isSpeaking = ref(false)
  const currentUtterance = ref<SpeechSynthesisUtterance | null>(null)

  // Preferred voice order for fallback
  const preferredVoices = [
    'Google UK English Male',
    'Microsoft George - English (United Kingdom)',
    'Daniel', // macOS UK English
  ]

  // Load available voices
  function loadVoices() {
    if (typeof window === 'undefined' || !window.speechSynthesis) return

    const available = window.speechSynthesis.getVoices()
    if (available.length > 0) {
      voices.value = available

      // Auto-select preferred voice if not already set
      if (!settingsStore.voiceName) {
        const preferred = findPreferredVoice(available)
        if (preferred) {
          settingsStore.setVoice(preferred.name)
        }
      }
    }
  }

  // Find the best available voice from preferences
  function findPreferredVoice(available: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
    // Try preferred voices in order
    for (const name of preferredVoices) {
      const voice = available.find((v) => v.name === name)
      if (voice) return voice
    }

    // Fallback: first British English voice
    const ukVoice = available.find((v) => v.lang === 'en-GB')
    if (ukVoice) return ukVoice

    // Fallback: first English voice
    const enVoice = available.find((v) => v.lang.startsWith('en'))
    if (enVoice) return enVoice

    // Last resort: first available voice
    return available[0] || null
  }

  // Get the currently selected voice object
  const selectedVoice = computed(() => {
    if (!settingsStore.voiceName) return null
    return voices.value.find((v) => v.name === settingsStore.voiceName) || null
  })

  // English voices for the dropdown
  const englishVoices = computed(() => {
    return voices.value.filter((v) => v.lang.startsWith('en'))
  })

  /**
   * Start speaking the given text.
   * @param text - The full text to speak
   * @param startOffset - Character offset to start from (for selection-based start)
   */
  function speak(text: string, startOffset = 0) {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      console.warn('Speech synthesis not supported')
      return
    }

    // Stop any current speech
    stop()

    // Trim text to start from offset
    const textToSpeak = startOffset > 0 ? text.slice(startOffset) : text

    if (!textToSpeak.trim()) {
      return
    }

    const utterance = new SpeechSynthesisUtterance(textToSpeak)

    // Apply settings
    if (selectedVoice.value) {
      utterance.voice = selectedVoice.value
    }
    utterance.rate = settingsStore.rate
    utterance.pitch = settingsStore.pitch
    utterance.volume = settingsStore.volume

    // Event handlers
    utterance.onstart = () => {
      isSpeaking.value = true
    }

    utterance.onend = () => {
      isSpeaking.value = false
      currentUtterance.value = null
    }

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event.error)
      isSpeaking.value = false
      currentUtterance.value = null
    }

    currentUtterance.value = utterance
    window.speechSynthesis.speak(utterance)
  }

  /**
   * Stop speaking immediately.
   */
  function stop() {
    if (typeof window === 'undefined' || !window.speechSynthesis) return

    window.speechSynthesis.cancel()
    isSpeaking.value = false
    currentUtterance.value = null
  }

  /**
   * Toggle speaking on/off.
   * @param text - The full text to speak
   * @param startOffset - Character offset to start from
   */
  function toggle(text: string, startOffset = 0) {
    if (isSpeaking.value) {
      stop()
    } else {
      speak(text, startOffset)
    }
  }

  /**
   * Get the selection start offset within a container element.
   * Returns 0 if no selection or selection is outside container.
   */
  function getSelectionOffset(containerEl: HTMLElement): number {
    const selection = window.getSelection()
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
      return 0
    }

    const range = selection.getRangeAt(0)
    const anchorNode = selection.anchorNode

    // Check if selection is within our container
    if (!containerEl.contains(anchorNode)) {
      return 0
    }

    // Calculate offset by getting text content up to selection start
    const preRange = document.createRange()
    preRange.setStart(containerEl, 0)
    preRange.setEnd(range.startContainer, range.startOffset)

    const textBeforeSelection = preRange.toString()
    return textBeforeSelection.length
  }

  /**
   * Extract all text content from a container element.
   */
  function getTextContent(containerEl: HTMLElement): string {
    // Get text content, normalize whitespace
    return containerEl.textContent?.replace(/\s+/g, ' ').trim() || ''
  }

  // Initialize voices on mount
  onMounted(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return

    // Load voices immediately if available
    loadVoices()

    // Chrome loads voices asynchronously
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices
    }
  })

  // Cleanup on unmount
  onUnmounted(() => {
    stop()
  })

  return {
    // State
    voices,
    englishVoices,
    selectedVoice,
    isSpeaking,

    // Settings (from store)
    voiceName: computed(() => settingsStore.voiceName),
    rate: computed(() => settingsStore.rate),
    pitch: computed(() => settingsStore.pitch),
    volume: computed(() => settingsStore.volume),

    // Actions
    speak,
    stop,
    toggle,
    loadVoices,
    getSelectionOffset,
    getTextContent,

    // Settings setters (delegate to store)
    setVoice: settingsStore.setVoice,
    setRate: settingsStore.setRate,
    setPitch: settingsStore.setPitch,
    setVolume: settingsStore.setVolume,
  }
}
