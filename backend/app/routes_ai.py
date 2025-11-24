"""
Mock AI endpoints for Keeper AI and Rules AI.
These will be replaced with n8n workflows later.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random
import httpx

router = APIRouter(prefix="/ai", tags=["ai"])

# n8n webhook URLs (from docker-compose network)
N8N_PROPHET_WEBHOOK_URL = "http://n8n:5678/webhook/coc_prophet"
N8N_DUNGEONMASTER_WEBHOOK_URL = "http://n8n:5678/webhook/coc_dungeonmaster"


class KeeperRequest(BaseModel):
    """Request for Keeper AI to process turn."""
    turn_id: str
    scene_id: str
    actions: List[dict]
    context: Optional[dict] = None


class KeeperResponse(BaseModel):
    """Response from Keeper AI."""
    turn_id: str
    reaction: dict
    scene_summary: Optional[str] = None
    chapter_transition: Optional[bool] = False
    scene_transition: Optional[bool] = False


class RulesRequest(BaseModel):
    """Request for Rules AI."""
    player_id: str
    question: str
    context: Optional[dict] = None


class RulesResponse(BaseModel):
    """Response from Rules AI."""
    answer: str
    rules_references: Optional[List[str]] = None


class ProphetRequest(BaseModel):
    """Request for Prophet AI (knowledge base assistant)."""
    player_id: str
    question: str
    context: Optional[dict] = None


class ProphetResponse(BaseModel):
    """Response from Prophet AI."""
    answer: str
    references: Optional[List[str]] = None


class DungeonMasterRequest(BaseModel):
    """Request for DungeonMaster AI (turn processing)."""
    turn_id: str
    scene_id: str
    actions: List[dict]  # List of action drafts with character_id, speak, act, etc.
    context: Optional[dict] = None


class DungeonMasterResponse(BaseModel):
    """Response from DungeonMaster AI."""
    description: str
    summary: Optional[str] = None


# ============== KEEPER AI ENDPOINTS ==============

@router.post("/keeper/process-turn", response_model=KeeperResponse)
async def process_turn(request: KeeperRequest):
    """
    Mock Keeper AI endpoint - processes player actions and returns narrative response.

    In production, this will:
    1. Receive turn actions
    2. Call n8n workflow with LLM integration
    3. Return narrative description and scene updates
    """

    # Mock responses based on action content
    action_descriptions = []
    for action in request.actions:
        if action.get('speak'):
            action_descriptions.append(f"{action.get('actor_id', 'Someone')} says something")
        if action.get('act'):
            action_descriptions.append(f"{action.get('actor_id', 'Someone')} takes action")

    mock_responses = [
        {
            "description": f"As the characters move forward, the dim candlelight flickers against the stone walls. The air grows colder, and a faint scraping sound echoes from the darkness ahead. {', '.join(action_descriptions[:2]) if action_descriptions else 'The tension builds...'}",
            "summary": "Characters investigate the dark corridor; strange sounds detected"
        },
        {
            "description": f"The ancient tome reveals cryptic symbols that seem to shift in the lamplight. {', '.join(action_descriptions[:2]) if action_descriptions else 'Someone examines it closely'}, and for a moment, the temperature in the room drops noticeably. A sense of unease settles over the group.",
            "summary": "Investigation of mysterious tome; unsettling atmosphere intensifies"
        },
        {
            "description": f"The door creaks open slowly, revealing a chamber filled with dust-covered furniture. {', '.join(action_descriptions[:2]) if action_descriptions else 'The group proceeds cautiously'}. In the corner, a portrait hangs askew, its painted eyes seeming to follow your movements.",
            "summary": "Discovery of abandoned chamber; eerie portrait observed"
        }
    ]

    selected_response = random.choice(mock_responses)

    return KeeperResponse(
        turn_id=request.turn_id,
        reaction={
            "description": selected_response["description"],
            "summary": selected_response["summary"]
        },
        scene_summary=selected_response["summary"],
        chapter_transition=False,
        scene_transition=False
    )


@router.post("/keeper/generate-scene", response_model=dict)
async def generate_scene(campaign_id: str, chapter_id: str, previous_scene_summary: Optional[str] = None):
    """
    Mock endpoint - generates new scene.

    In production, this will:
    1. Analyze campaign context and previous scenes
    2. Generate scene description via LLM
    3. Return scene data
    """

    scene_templates = [
        {
            "name": "The Abandoned Library",
            "description": "Rows of dust-covered shelves stretch into darkness. The smell of old parchment and decay fills the air.",
        },
        {
            "name": "The Ritual Chamber",
            "description": "Strange symbols cover the walls of this circular room. Candles flicker despite the absence of any breeze.",
        },
        {
            "name": "The Foggy Docks",
            "description": "Thick fog rolls off the water, obscuring the rotting pier. The sound of lapping water mingles with distant, unidentifiable cries.",
        }
    ]

    selected_scene = random.choice(scene_templates)

    return {
        "name": selected_scene["name"],
        "description": selected_scene["description"],
        "suggested_atmosphere": "tense and mysterious",
        "ai_generated": True,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============== RULES AI ENDPOINTS ==============

@router.post("/rules/ask", response_model=RulesResponse)
async def ask_rules_question(request: RulesRequest):
    """
    Mock Rules AI endpoint - answers rules questions.

    In production, this will:
    1. Receive player's rules question
    2. Query rules database/RAG system
    3. Return answer with rulebook references
    """

    question_lower = request.question.lower()

    # Simple keyword-based mock responses
    if any(word in question_lower for word in ['skill', 'roll', 'check']):
        return RulesResponse(
            answer="To make a skill check, roll 1d100 and compare against your skill rating. If you roll equal to or under your skill rating, you succeed. A roll of 01 is always a critical success, while a roll of 100 is always a fumble.",
            rules_references=["Rulebook p.92", "Quick Reference: Skill Checks"]
        )

    elif any(word in question_lower for word in ['combat', 'fight', 'attack']):
        return RulesResponse(
            answer="Combat proceeds in DEX order (highest to lowest). To attack, make a Fighting skill check. If successful, the defender may attempt a Dodge or Fight Back. Successful attacks deal damage based on the weapon used.",
            rules_references=["Rulebook p.115", "Combat Chapter"]
        )

    elif any(word in question_lower for word in ['sanity', 'san', 'madness']):
        return RulesResponse(
            answer="When encountering horrific events, you must make a Sanity roll (1d100 vs current SAN). Failure results in SAN loss as specified by the encounter. Major SAN loss can trigger temporary or indefinite insanity.",
            rules_references=["Rulebook p.167", "Sanity Chapter"]
        )

    else:
        return RulesResponse(
            answer=f"Regarding '{request.question}': In Call of Cthulhu, most actions are resolved with a percentile roll (1d100) against an appropriate skill. The Keeper has final say on difficulty and consequences. (This is a mock response - the full Rules AI will provide detailed answers.)",
            rules_references=["Rulebook: General Gameplay", "Keeper's Guide"]
        )


@router.get("/rules/search")
async def search_rules(query: str):
    """
    Mock endpoint - searches rules database.

    In production, this will:
    1. Query vector database of rulebook content
    2. Return relevant rules sections
    """

    return {
        "query": query,
        "results": [
            {
                "section": "Skills",
                "page": 92,
                "excerpt": f"Search results for '{query}' would appear here...",
                "relevance": 0.85
            }
        ],
        "mock": True
    }


# ============== PROPHET AI ENDPOINTS (n8n integration) ==============

@router.post("/prophet/ask", response_model=ProphetResponse)
async def ask_prophet_question(request: ProphetRequest):
    """
    Prophet AI endpoint - answers questions using the knowledge base via n8n workflow.
    
    This endpoint:
    1. Receives player's question
    2. Sends to n8n Keeper workflow with {"Prophet": "question"} format
    3. Returns AI response with references
    """
    
    try:
        # Prepare payload for n8n webhook
        payload = {"Prophet": request.question}
        
        # Call n8n prophet webhook
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                N8N_PROPHET_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"n8n webhook returned status {response.status_code}"
                )
            
            # Parse n8n response
            n8n_data = response.json()
            
            # Extract answer from n8n response
            # The AI Agent returns the response in the body field
            answer = n8n_data.get("output", n8n_data.get("body", ""))
            
            # If answer is still empty, try to get it from nested structure
            if not answer and isinstance(n8n_data, dict):
                # Try various possible response structures
                answer = (
                    n8n_data.get("text") or 
                    n8n_data.get("response") or 
                    str(n8n_data)
                )
            
            return ProphetResponse(
                answer=answer if answer else "The Prophet is silent...",
                references=None  # TODO: Extract references if n8n provides them
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to Prophet AI timed out"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Prophet AI: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Prophet request: {str(e)}"
        )


# ============== DUNGEONMASTER AI ENDPOINTS (n8n integration) ==============

@router.post("/dungeonmaster/process", response_model=DungeonMasterResponse)
async def process_dungeonmaster_turn(request: DungeonMasterRequest):
    """
    DungeonMaster AI endpoint - processes player actions and generates scene narrative via n8n workflow.
    
    This endpoint:
    1. Receives the full action list from players
    2. Sends to n8n Keeper workflow with {"DungeonMaster": actions} format
    3. Returns AI-generated scene description and summary
    """
    
    try:
        # Prepare payload for n8n webhook
        payload = {"DungeonMaster": request.actions}
        
        # Call n8n dungeonmaster webhook
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for scene generation
            response = await client.post(
                N8N_DUNGEONMASTER_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"n8n webhook returned status {response.status_code}"
                )
            
            # Parse n8n response
            n8n_data = response.json()
            
            # Extract description from n8n response
            description = n8n_data.get("output", n8n_data.get("body", ""))
            
            # If description is still empty, try to get it from nested structure
            if not description and isinstance(n8n_data, dict):
                description = (
                    n8n_data.get("text") or 
                    n8n_data.get("response") or 
                    n8n_data.get("description") or
                    str(n8n_data)
                )
            
            # Try to extract a summary (first sentence or first 100 chars)
            summary = None
            if description:
                sentences = description.split('. ')
                if len(sentences) > 1:
                    summary = sentences[0] + '.'
                elif len(description) > 100:
                    summary = description[:97] + '...'
            
            return DungeonMasterResponse(
                description=description if description else "The Keeper observes in silence...",
                summary=summary
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to DungeonMaster AI timed out"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to DungeonMaster AI: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing DungeonMaster request: {str(e)}"
        )


# ============== AI STATUS ENDPOINTS ==============

@router.get("/status")
async def ai_status():
    """Check AI services status."""
    return {
        "keeper_ai": {
            "status": "mock",
            "message": "Using mock responses - will be replaced with n8n workflow"
        },
        "rules_ai": {
            "status": "mock",
            "message": "Using mock responses - will be replaced with n8n workflow"
        },
        "prophet_ai": {
            "status": "active",
            "message": "Connected to n8n Prophet workflow",
            "webhook_url": N8N_PROPHET_WEBHOOK_URL
        },
        "dungeonmaster_ai": {
            "status": "active",
            "message": "Connected to n8n DungeonMaster workflow",
            "webhook_url": N8N_DUNGEONMASTER_WEBHOOK_URL
        },
        "timestamp": datetime.utcnow().isoformat()
    }
