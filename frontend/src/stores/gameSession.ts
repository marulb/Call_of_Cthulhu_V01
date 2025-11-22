/**
 * Pinia store for game session management.
 * Tracks player selections throughout the login/selection flow.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { World, Realm, Campaign, Character, Session } from '@/services/api'

export const useGameSessionStore = defineStore('gameSession', () => {
  // ============== STATE ==============

  // Player information
  const playerName = ref<string>('')

  // Selected entities
  const selectedWorld = ref<World | null>(null)
  const selectedRealm = ref<Realm | null>(null)
  const selectedCampaign = ref<Campaign | null>(null)
  const selectedCharacters = ref<Character[]>([])
  const currentSession = ref<Session | null>(null)

  // UI state
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // ============== GETTERS ==============

  const isPlayerNameSet = computed(() => playerName.value.trim().length > 0)
  const isWorldSelected = computed(() => selectedWorld.value !== null)
  const isRealmSelected = computed(() => selectedRealm.value !== null)
  const isCampaignSelected = computed(() => selectedCampaign.value !== null)
  const hasCharactersSelected = computed(() => selectedCharacters.value.length > 0)
  const isSessionActive = computed(() => currentSession.value !== null)

  const canProceedToRealm = computed(() => isPlayerNameSet.value && isWorldSelected.value)
  const canProceedToCampaign = computed(() => canProceedToRealm.value && isRealmSelected.value)
  const canProceedToCharacters = computed(() => canProceedToCampaign.value && isCampaignSelected.value)
  const canProceedToSession = computed(() => canProceedToCharacters.value && hasCharactersSelected.value)
  const canStartGame = computed(() => canProceedToSession.value && isSessionActive.value)

  // ============== ACTIONS ==============

  function setPlayerName(name: string) {
    playerName.value = name.trim()
    // Store in localStorage for convenience
    if (playerName.value) {
      localStorage.setItem('coc_player_name', playerName.value)
    }
  }

  function loadPlayerNameFromStorage() {
    const stored = localStorage.getItem('coc_player_name')
    if (stored) {
      playerName.value = stored
    }
  }

  function setWorld(world: World | null) {
    selectedWorld.value = world
    // Reset downstream selections
    selectedRealm.value = null
    selectedCampaign.value = null
    selectedCharacters.value = []
    currentSession.value = null
  }

  function setRealm(realm: Realm | null) {
    selectedRealm.value = realm
    // Reset downstream selections
    selectedCampaign.value = null
    selectedCharacters.value = []
    currentSession.value = null
  }

  function setCampaign(campaign: Campaign | null) {
    selectedCampaign.value = campaign
    // Reset downstream selections
    selectedCharacters.value = []
    currentSession.value = null
  }

  function setCharacters(characters: Character[]) {
    selectedCharacters.value = characters
    // Reset session
    currentSession.value = null
  }

  function toggleCharacter(character: Character) {
    const index = selectedCharacters.value.findIndex(c => c.id === character.id)
    if (index >= 0) {
      // Remove character
      selectedCharacters.value.splice(index, 1)
    } else {
      // Add character
      selectedCharacters.value.push(character)
    }
  }

  function isCharacterSelected(characterId: string): boolean {
    return selectedCharacters.value.some(c => c.id === characterId)
  }

  function setSession(session: Session | null) {
    currentSession.value = session
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function setError(err: string | null) {
    error.value = err
  }

  function clearError() {
    error.value = null
  }

  function resetSession() {
    playerName.value = ''
    selectedWorld.value = null
    selectedRealm.value = null
    selectedCampaign.value = null
    selectedCharacters.value = []
    currentSession.value = null
    error.value = null
    localStorage.removeItem('coc_player_name')
  }

  // Save current session state to localStorage for resume
  function saveSessionState() {
    const state = {
      playerName: playerName.value,
      worldId: selectedWorld.value?.id,
      realmId: selectedRealm.value?.id,
      campaignId: selectedCampaign.value?.id,
      characterIds: selectedCharacters.value.map(c => c.id),
      sessionId: currentSession.value?.id
    }
    localStorage.setItem('coc_session_state', JSON.stringify(state))
  }

  function getSessionState() {
    const stored = localStorage.getItem('coc_session_state')
    if (stored) {
      return JSON.parse(stored)
    }
    return null
  }

  // ============== RETURN ==============

  return {
    // State
    playerName,
    selectedWorld,
    selectedRealm,
    selectedCampaign,
    selectedCharacters,
    currentSession,
    isLoading,
    error,

    // Getters
    isPlayerNameSet,
    isWorldSelected,
    isRealmSelected,
    isCampaignSelected,
    hasCharactersSelected,
    isSessionActive,
    canProceedToRealm,
    canProceedToCampaign,
    canProceedToCharacters,
    canProceedToSession,
    canStartGame,

    // Actions
    setPlayerName,
    loadPlayerNameFromStorage,
    setWorld,
    setRealm,
    setCampaign,
    setCharacters,
    toggleCharacter,
    isCharacterSelected,
    setSession,
    setLoading,
    setError,
    clearError,
    resetSession,
    saveSessionState,
    getSessionState
  }
})
