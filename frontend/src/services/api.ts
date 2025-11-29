/**
 * API service layer for backend communication.
 * Uses native fetch API for HTTP requests.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8093/api/v1'

// ============== TYPES ==============

export interface Player {
  id: string
  name: string
  email?: string
  created_at: string
  last_login: string
  realms: string[]
}

export interface World {
  id: string
  kind: string
  name: string
  ruleset?: string
  description?: string
  meta: { created_by: string; created_at: string }
  changes: Array<{ by: string; at: string; type?: string }>
}

export interface Realm {
  id: string
  kind: string
  world_id: string
  name: string
  description?: string
  players: Array<{ id: string; name: string }>
  characters: string[]
  campaigns: string[]
  meta: { created_by: string; created_at: string }
  changes: Array<{ by: string; at: string; type?: string }>
  setting?: any
}

export interface Campaign {
  id: string
  kind: string
  realm_id: string
  name: string
  description?: string
  status: 'planning' | 'running' | 'paused' | 'completed'
  story_arc?: any
  setting?: any
  meta: { created_by: string; created_at: string }
  changes: Array<{ by: string; at: string; type?: string }>
}

// ============== CHARACTER SHEET TYPES ==============

export interface InvestigatorInfo {
  name: string
  birthplace: string
  pronoun: string
  occupation: string
  residence: string
  age: string
}

export interface CharacteristicValue {
  reg: string
}

export interface Characteristics {
  STR: CharacteristicValue
  CON: CharacteristicValue
  DEX: CharacteristicValue
  APP: CharacteristicValue
  INT: CharacteristicValue
  POW: CharacteristicValue
  SIZ: CharacteristicValue
  EDU: CharacteristicValue
}

export interface PointPool {
  max: string
  current: string
}

export interface SanityPool extends PointPool {
  insane: string
}

export interface LuckPool {
  starting: string
  current: string
}

export interface CharacterStatus {
  temporary_insanity: boolean
  indefinite_insanity: boolean
  major_wound: boolean
  unconscious: boolean
  dying: boolean
}

export interface Skill {
  base: string
  reg: string
  used: boolean
}

export interface Weapon {
  name: string
  skill: string
  damage: string
  num_attacks: string
  range: string
  ammo: string
  malf: string
}

export interface Combat {
  weapons: Weapon[]
  move: number
  build: string
  damage_bonus: string
}

export interface Backstory {
  personal_description: string
  ideology_beliefs: string
  significant_people: string
  meaningful_locations: string
  treasured_possessions: string
  traits: string
  injuries_scars: string
  phobias_manias: string
  arcane_tomes_spells: string
  encounters_strange_entities: string
}

export interface Story {
  my_story: string
  backstory: Backstory
}

export interface Wealth {
  spending_level: string
  cash: string
  assets: string
}

export interface Relationship {
  object: string
  relation: string
}

export interface CharacterSheet {
  investigator: InvestigatorInfo
  characteristics: Characteristics
  hit_points: PointPool
  magic_points: PointPool
  luck: LuckPool
  sanity: SanityPool
  status: CharacterStatus
  skills: Record<string, Skill>
  combat: Combat
  story: Story
  gear_possessions: string
  wealth: Wealth
  relationships: Relationship[]
}

export interface Character {
  id: string
  uid?: string
  kind: string
  type?: string
  name: string
  realm_id: string
  description?: string
  controller: {
    owner: string
    mode: string
    agent?: string
  }
  data: CharacterSheet
  ooc_notes: string
  profile_completed: boolean
  ai_controlled: boolean
  ai_personality?: string | null
  meta: { created_by: string; created_at: string }
  visibility?: string
  changes: Array<{ by: string; at: string; type?: string }>
}

export interface NPC {
  id: string
  kind: string
  campaign_id: string
  name: string
  description: string
  role: string // "ally", "enemy", "neutral", "mysterious"
  personality: string
  goals: string[]
  knowledge: string[]
  current_location?: string
  status: string // "active", "dead", "missing", "unknown"
  meta: { created_by: string; created_at: string }
  changes: Array<{ by: string; at: string; type?: string }>
}

export interface Session {
  id: string
  kind: string
  realm_id: string
  campaign_id: string
  session_number: number
  master_player_id?: string
  attendance: {
    players_present: string[]
    players_absent: string[]
  }
  story_links?: any
  notes?: string
  meta: { created_by: string; created_at: string }
  changes: Array<{ by: string; at: string; type?: string }>
}

// ============== HELPER FUNCTIONS ==============

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers
    }
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`API Error: ${response.status} - ${error}`)
  }

  return response.json()
}

// ============== PLAYERS ==============

export const playersAPI = {
  list: (search?: string) => {
    const query = search ? `?search=${encodeURIComponent(search)}` : ''
    return fetchJSON<Player[]>(`/players${query}`)
  },
  get: (id: string) => fetchJSON<Player>(`/players/${id}`),
  getByName: (name: string) => fetchJSON<Player>(`/players/by-name/${encodeURIComponent(name)}`),
  createOrGet: (data: { name: string; email?: string }) =>
    fetchJSON<Player>('/players', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  update: (id: string, data: { name: string; email?: string }) =>
    fetchJSON<Player>(`/players/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  delete: (id: string) =>
    fetchJSON<{ message: string }>(`/players/${id}`, {
      method: 'DELETE'
    })
}

// ============== WORLDS ==============

export const worldsAPI = {
  list: () => fetchJSON<World[]>('/worlds'),
  get: (id: string) => fetchJSON<World>(`/worlds/${id}`),
  create: (data: { name: string; ruleset?: string; description?: string; created_by: string }) =>
    fetchJSON<World>('/worlds', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  update: (
    id: string,
    data: { name: string; ruleset?: string; description?: string; created_by: string }
  ) =>
    fetchJSON<World>(`/worlds/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  delete: (id: string) =>
    fetchJSON<{ message: string }>(`/worlds/${id}`, {
      method: 'DELETE'
    })
}

// ============== REALMS ==============

export const realmsAPI = {
  list: (worldId?: string) => {
    const query = worldId ? `?world_id=${worldId}` : ''
    return fetchJSON<Realm[]>(`/realms${query}`)
  },
  get: (id: string) => fetchJSON<Realm>(`/realms/${id}`),
  create: (data: { world_id: string; name: string; description?: string; created_by: string }) =>
    fetchJSON<Realm>('/realms', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  update: (
    id: string,
    data: { world_id: string; name: string; description?: string; created_by: string }
  ) =>
    fetchJSON<Realm>(`/realms/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  delete: (id: string) =>
    fetchJSON<{ message: string }>(`/realms/${id}`, {
      method: 'DELETE'
    })
}

// ============== CAMPAIGNS ==============

export interface CampaignSetting {
  tone?: string
  goal?: string
  story_elements?: string[]
  key_elements?: string[]
}

export const campaignsAPI = {
  list: (realmId?: string) => {
    const query = realmId ? `?realm_id=${realmId}` : ''
    return fetchJSON<Campaign[]>(`/campaigns${query}`)
  },
  get: (id: string) => fetchJSON<Campaign>(`/campaigns/${id}`),
  create: (data: {
    realm_id: string
    name: string
    description?: string
    status?: 'planning' | 'running' | 'paused' | 'completed'
    setting?: CampaignSetting
    generate_milestones?: boolean
    created_by: string
  }) =>
    fetchJSON<Campaign>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  update: (
    id: string,
    data: {
      realm_id: string
      name: string
      description?: string
      status?: 'planning' | 'running' | 'paused' | 'completed'
      created_by: string
    }
  ) =>
    fetchJSON<Campaign>(`/campaigns/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  delete: (id: string) =>
    fetchJSON<{ message: string }>(`/campaigns/${id}`, {
      method: 'DELETE'
    })
}

// ============== CHARACTERS ==============

export const charactersAPI = {
  list: (realmId?: string, player?: string) => {
    const params = new URLSearchParams()
    if (realmId) params.append('realm_id', realmId)
    if (player) params.append('player', player)
    const query = params.toString() ? `?${params.toString()}` : ''
    return fetchJSON<Character[]>(`/characters${query}`)
  },
  get: (id: string) => fetchJSON<Character>(`/characters/${id}`),
  create: (data: {
    realm_id: string
    name: string
    type?: string
    description?: string
    owner: string
    created_by: string
    data?: CharacterSheet
    ooc_notes?: string
    profile_completed?: boolean
  }) =>
    fetchJSON<Character>('/characters', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  update: (
    id: string,
    data: {
      realm_id: string
      name: string
      type?: string
      description?: string
      owner: string
      created_by: string
      data?: CharacterSheet
      ooc_notes?: string
      profile_completed?: boolean
    }
  ) =>
    fetchJSON<Character>(`/characters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  delete: (id: string) =>
    fetchJSON<{ message: string }>(`/characters/${id}`, {
      method: 'DELETE'
    })
}

// ============== SESSIONS ==============

export const sessionsAPI = {
  list: (realmId?: string, campaignId?: string) => {
    const params = new URLSearchParams()
    if (realmId) params.append('realm_id', realmId)
    if (campaignId) params.append('campaign_id', campaignId)
    const query = params.toString() ? `?${params.toString()}` : ''
    return fetchJSON<Session[]>(`/sessions${query}`)
  },
  getLatest: (realmId: string, campaignId: string) => {
    return fetchJSON<Session | null>(`/sessions/latest?realm_id=${realmId}&campaign_id=${campaignId}`)
  },
  get: (id: string) => fetchJSON<Session>(`/sessions/${id}`),
  create: (data: {
    realm_id: string
    campaign_id: string
    session_number: number
    players_present: string[]
    players_absent?: string[]
    notes?: string
    created_by: string
  }) =>
    fetchJSON<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  update: (
    id: string,
    data: {
      realm_id: string
      campaign_id: string
      session_number: number
      players_present: string[]
      players_absent?: string[]
      notes?: string
      created_by: string
    }
  ) =>
    fetchJSON<Session>(`/sessions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  delete: (id: string) =>
    fetchJSON<{ message: string }>(`/sessions/${id}`, {
      method: 'DELETE'
    })
}
