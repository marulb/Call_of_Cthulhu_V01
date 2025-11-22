import { createRouter, createWebHistory } from 'vue-router'
import { useGameSessionStore } from '@/stores/gameSession'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/select/world',
      name: 'select-world',
      component: () => import('../views/WorldSelectView.vue'),
      meta: { requiresPlayerName: true }
    },
    {
      path: '/select/realm',
      name: 'select-realm',
      component: () => import('../views/RealmSelectView.vue'),
      meta: { requiresWorld: true }
    },
    {
      path: '/select/campaign',
      name: 'select-campaign',
      component: () => import('../views/CampaignSelectView.vue'),
      meta: { requiresRealm: true }
    },
    {
      path: '/select/characters',
      name: 'select-characters',
      component: () => import('../views/CharacterSelectView.vue'),
      meta: { requiresCampaign: true }
    },
    {
      path: '/select/session',
      name: 'select-session',
      component: () => import('../views/SessionSelectView.vue'),
      meta: { requiresCharacters: true }
    },
    {
      path: '/game',
      name: 'game',
      component: () => import('../views/GameView.vue'),
      meta: { requiresSession: true }
    }
  ]
})

// Navigation guards to ensure proper flow
router.beforeEach((to, from, next) => {
  const sessionStore = useGameSessionStore()

  // Check if route requires player name
  if (to.meta.requiresPlayerName && !sessionStore.isPlayerNameSet) {
    return next({ name: 'login' })
  }

  // Check if route requires world selection
  if (to.meta.requiresWorld && !sessionStore.isWorldSelected) {
    return next({ name: 'select-world' })
  }

  // Check if route requires realm selection
  if (to.meta.requiresRealm && !sessionStore.isRealmSelected) {
    return next({ name: 'select-realm' })
  }

  // Check if route requires campaign selection
  if (to.meta.requiresCampaign && !sessionStore.isCampaignSelected) {
    return next({ name: 'select-campaign' })
  }

  // Check if route requires character selection
  if (to.meta.requiresCharacters && !sessionStore.hasCharactersSelected) {
    return next({ name: 'select-characters' })
  }

  // Check if route requires active session
  if (to.meta.requiresSession && !sessionStore.isSessionActive) {
    return next({ name: 'select-session' })
  }

  next()
})

export default router
