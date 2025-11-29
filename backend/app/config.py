"""
Application configuration and feature flags.

Centralized configuration for environment-based settings and feature toggles.
"""
import os


# ============== Feature Flags ==============

# Enable async turn processing with callback pattern (Phase 3 refactor)
# When True: Uses new hybrid architecture (backend assembles context, n8n calls back)
# When False: Uses old synchronous n8n workflow
USE_ASYNC_TURN_PROCESSING = os.getenv("USE_ASYNC_TURN_PROCESSING", "false").lower() == "true"


# ============== Service URLs ==============

# n8n webhook URLs
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://n8n:5678")
N8N_DUNGEONMASTER_WEBHOOK = f"{N8N_BASE_URL}/webhook/coc_dungeonmaster"
N8N_DUNGEONMASTER_V2_WEBHOOK = f"{N8N_BASE_URL}/webhook/coc_dungeonmaster_v2"
N8N_PROPHET_WEBHOOK = f"{N8N_BASE_URL}/webhook/coc_prophet"

# Backend callback URL (for n8n to call back)
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://backend:8000")


# ============== MongoDB Configuration ==============

MONGODB_SYSTEM_URL = os.getenv("MONGODB_SYSTEM_URL", "mongodb://localhost:27017/call_of_cthulhu_system")
MONGODB_GAMERECORDS_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/call_of_cthulhu_gamerecords")


# ============== Context Assembly Limits ==============

# Maximum number of previous turns to include in context bundle
MAX_PREVIOUS_TURNS = int(os.getenv("MAX_PREVIOUS_TURNS", "5"))

# Maximum number of characters to include in context
MAX_CHARACTERS = int(os.getenv("MAX_CHARACTERS", "10"))

# Maximum number of lore chunks from RAG
MAX_LORE_CHUNKS = int(os.getenv("MAX_LORE_CHUNKS", "3"))


# ============== Timeouts ==============

# Timeout for n8n webhook calls (seconds)
N8N_WEBHOOK_TIMEOUT = int(os.getenv("N8N_WEBHOOK_TIMEOUT", "60"))

# Timeout for n8n callback to backend (seconds)
CALLBACK_TIMEOUT = int(os.getenv("CALLBACK_TIMEOUT", "10"))


# ============== Logging ==============

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
