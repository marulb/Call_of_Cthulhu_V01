# Milestone: Phase 3 - Async Callback Architecture

> **Completed:** 2025-11-29  
> **Agent:** Claude Code (GitHub Copilot)

---

## Summary

Refactored turn processing from synchronous 60s-blocking pattern to async callback architecture. Reduced n8n DungeonMaster workflow from **34 nodes → 6 nodes** (82% reduction).

---

## Architecture Change

**Before:** Frontend → Backend → n8n (blocks 60s) → LLM → n8n writes MongoDB → returns  
**After:** Frontend → Backend (returns 202) → n8n → LLM → n8n POSTs callback → Backend writes MongoDB → Socket.IO

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/app/services/context_assembly.py` | Assembles context bundle for n8n |
| `backend/app/services/skill_check.py` | Detects skills + rolls d100 (CoC 7e) |
| `backend/app/services/transition.py` | Scene/chapter transition handling |
| `backend/app/config.py` | Feature flags, n8n API config |

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/routes_turns.py` | Added async submit + callback endpoint |
| `backend/app/socketio_manager.py` | New events: `turn_processing`, `turn_completed`, `turn_failed` |
| `n8n_workflows/DungeonMaster_Main.json` | Simplified 6-node workflow |
| `n8n_workflows/LLM_Synthesizer_SubWF.json` | Enhanced prompt + transition detection |
| `docker-compose.yml` | Added `USE_ASYNC_TURN_PROCESSING=true` |

---

## Key Endpoints

```
POST /api/v1/turns/{id}/submit     → 202 Accepted (async)
POST /api/v1/turns/internal/{id}/complete  → Callback from n8n
GET  /api/v1/turns/{id}/status     → Poll status (optional)
```

---

## Feature Flag

```python
USE_ASYNC_TURN_PROCESSING=true  # Enable new architecture
```

---

## Test Results

✅ Turn submission returns 202 immediately  
✅ n8n receives context bundle, calls LLM  
✅ LLM generates narrative with transition detection  
✅ Callback updates turn in MongoDB  
✅ Socket.IO emits `turn_completed` event  

---

## Bugs Fixed During Testing

1. `datetime not JSON serializable` → `.model_dump(mode='json')`
2. n8n validation error → Changed to top-level `actions` field
3. Wrong callback URL → Fixed path to `/api/v1/turns/internal/{id}/complete`
4. `agent_type` not detected → Fixed `$input.first()` → `$('Build Context Prompt')`
