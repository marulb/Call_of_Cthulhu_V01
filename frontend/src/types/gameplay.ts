/**
 * TypeScript types for gameplay entities
 */

export interface ActionDraft {
  id: string
  session_id: string
  player_id: string
  character_id: string
  speak?: string
  act?: string
  appearance?: string
  emotion?: string
  ooc?: string
  order: number
  ready: boolean
  updated_at: string
}

export interface Action {
  actor_id: string
  speak?: string
  act?: string
  appearance?: string
  emotion?: string
  ooc?: string
}

export interface Reaction {
  description: string
  summary?: string
}

export interface Turn {
  id: string
  kind: 'turn'
  scene_id: string
  order: number
  actions: Action[]
  reaction?: Reaction
  status: 'draft' | 'ready_for_agents' | 'processing' | 'completed'
  meta: {
    created_at: string
    created_by: string
  }
  changes: Array<{
    by: string
    at: string
    type: string
  }>
}

export interface Scene {
  id: string
  kind: 'scene'
  chapter_id: string
  name: string
  description?: string
  turns: string[]
  status: 'active' | 'completed'
  meta: {
    created_at: string
    created_by: string
  }
  changes: Array<{
    by: string
    at: string
    type: string
  }>
}

export interface Chapter {
  id: string
  kind: 'chapter'
  campaign_id: string
  name: string
  description?: string
  summary?: string
  scenes: string[]
  status: 'active' | 'completed'
  meta: {
    created_at: string
    created_by: string
  }
  changes: Array<{
    by: string
    at: string
    type: string
  }>
}

export interface ChatMessage {
  player_id: string
  player_name: string
  message: string
  timestamp: string
}

export interface PlayerPresence {
  player_id: string
  player_name: string
  online: boolean
  ready?: boolean
  character_id?: string
}
