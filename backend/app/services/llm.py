"""
Direct LLM service for backend operations.

Used for:
- Scene summarization (M4)
- Chapter summarization (M5)
- Campaign milestone generation (M2)

This bypasses n8n for simpler, synchronous LLM calls.
"""
import logging
import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_URL = "http://host.docker.internal:11434/api/chat"
OLLAMA_MODEL = "gpt-oss:20b"
OLLAMA_TIMEOUT = 120.0  # seconds


class LLMService:
    """Direct LLM service for backend operations."""

    def __init__(self):
        self.url = OLLAMA_URL
        self.model = OLLAMA_MODEL
        self.timeout = OLLAMA_TIMEOUT

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Make a direct call to Ollama LLM.
        
        Returns the LLM response text, or None if call fails.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.url,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("message", {}).get("content", "")
                else:
                    logger.error(f"LLM call failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"LLM call exception: {e}")
            return None

    async def summarize_scene(
        self,
        scene_name: str,
        turns: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a summary of a scene from its turns.
        
        Args:
            scene_name: Name of the scene
            turns: List of turn documents with actions and reactions
            
        Returns:
            Markdown-formatted summary
        """
        if not turns:
            return f"*{scene_name}* - No events recorded."

        # Build turn descriptions
        turn_descriptions = []
        for turn in turns:
            parts = []
            
            # Extract actions
            actions = turn.get("actions", [])
            for action in actions:
                char_name = action.get("character_name", "Someone")
                if action.get("speak"):
                    parts.append(f'{char_name} said: "{action["speak"]}"')
                if action.get("act"):
                    parts.append(f"{char_name} {action['act']}")
            
            # Extract reaction
            reaction = turn.get("reaction", {})
            if reaction.get("description"):
                parts.append(f"Result: {reaction['description'][:200]}...")
            
            if parts:
                turn_descriptions.append(" ".join(parts))

        system_prompt = """You are a narrative summarizer for a Call of Cthulhu RPG. 
Create concise, atmospheric summaries in Markdown format.

Rules:
- Use past tense
- Keep the dark, mysterious tone
- Focus on key events and discoveries
- Use **bold** for important items/names
- Use *italics* for atmosphere
- 2-3 sentences maximum"""

        user_prompt = f"""Summarize this scene: "{scene_name}"

Events:
{chr(10).join(f"- {desc}" for desc in turn_descriptions[:10])}

Write a brief Markdown summary (2-3 sentences):"""

        summary = await self._call_llm(system_prompt, user_prompt, temperature=0.4, max_tokens=200)
        
        if summary:
            return summary.strip()
        else:
            # Fallback to simple summary
            return f"*{scene_name}* - {len(turns)} turns occurred."

    async def summarize_chapter(
        self,
        chapter_name: str,
        scenes: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a summary of a chapter from its scenes.
        
        Args:
            chapter_name: Name of the chapter
            scenes: List of scene documents with summaries
            
        Returns:
            Markdown-formatted summary
        """
        if not scenes:
            return f"**{chapter_name}** - No scenes recorded."

        # Extract scene summaries
        scene_summaries = []
        for scene in scenes:
            name = scene.get("name", "Unnamed Scene")
            summary = scene.get("summary", "No summary")
            scene_summaries.append(f"**{name}**: {summary}")

        system_prompt = """You are a narrative summarizer for a Call of Cthulhu RPG.
Create chapter summaries that capture the story arc in Markdown format.

Rules:
- Use past tense
- Highlight key plot points and character developments
- Maintain the dark, mysterious atmosphere
- Use **bold** for chapter-defining moments
- Use bullet points for multiple key events
- 3-5 sentences maximum"""

        user_prompt = f"""Summarize this chapter: "{chapter_name}"

Scenes:
{chr(10).join(scene_summaries)}

Write a Markdown summary of the chapter (3-5 sentences):"""

        summary = await self._call_llm(system_prompt, user_prompt, temperature=0.4, max_tokens=300)
        
        if summary:
            return summary.strip()
        else:
            # Fallback to simple summary
            return f"**{chapter_name}** - {len(scenes)} scenes completed."

    async def generate_campaign_milestones(
        self,
        campaign_name: str,
        setting: Dict[str, Any],
        num_milestones: int = 5
    ) -> List[str]:
        """
        Generate story milestones for a new campaign.
        
        Args:
            campaign_name: Name of the campaign
            setting: Campaign setting dict (tone, goal, story_elements, etc.)
            num_milestones: Number of milestones to generate
            
        Returns:
            List of milestone descriptions
        """
        tone = setting.get("tone", "dark and mysterious")
        goal = setting.get("goal", "uncover the truth")
        story_elements = setting.get("story_elements", [])
        key_elements = setting.get("key_elements", [])

        system_prompt = """You are a Call of Cthulhu campaign designer.
Create story milestones that form a compelling narrative arc.

Rules:
- Each milestone should be a key story beat
- Progress from introduction to climax
- Include investigation, horror, and revelation moments
- Keep each milestone to 1-2 sentences
- Number each milestone"""

        user_prompt = f"""Design {num_milestones} story milestones for:

Campaign: "{campaign_name}"
Tone: {tone}
Goal: {goal}
Story Elements: {', '.join(story_elements) if story_elements else 'Not specified'}
Key Elements: {', '.join(key_elements) if key_elements else 'Not specified'}

List {num_milestones} milestones:"""

        response = await self._call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=500)
        
        if response:
            # Parse numbered list
            lines = response.strip().split("\n")
            milestones = []
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Remove numbering/bullets
                    cleaned = line.lstrip("0123456789.-) ").strip()
                    if cleaned:
                        milestones.append(cleaned)
            
            if milestones:
                return milestones[:num_milestones]
        
        # Fallback milestones
        return [
            "The investigators discover the first clue",
            "A dark secret is revealed",
            "Confrontation with the unknown",
            "The truth becomes clear",
            "Final resolution"
        ][:num_milestones]

    async def generate_character_action(
        self,
        character_name: str,
        character_data: Dict[str, Any],
        scene_context: Dict[str, Any],
        existing_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate an action for an AI-controlled character.

        Args:
            character_name: Name of the character
            character_data: Character sheet data (personality, occupation, skills, backstory)
            scene_context: Current scene info (name, location, previous turns)
            existing_actions: Other player actions this turn (so AI can react)

        Returns:
            Action dict with {speak, act, appearance, emotion, ooc}
        """
        # Extract character details
        personality = character_data.get("ai_personality", "analytical")
        occupation = character_data.get("occupation", "Investigator")
        backstory = character_data.get("backstory", "")

        # Extract top skills
        skills_data = character_data.get("skills", {})
        top_skills = []
        if isinstance(skills_data, dict):
            # Extract skills with values > 50
            for skill_name, skill_value in skills_data.items():
                if isinstance(skill_value, dict):
                    reg_value = skill_value.get("reg", 0)
                    try:
                        value = int(reg_value) if reg_value else 0
                    except (ValueError, TypeError):
                        value = 0
                    if value > 50:
                        top_skills.append(f"{skill_name} ({value}%)")
                elif isinstance(skill_value, (int, str)):
                    try:
                        value = int(skill_value)
                        if value > 50:
                            top_skills.append(f"{skill_name} ({value}%)")
                    except (ValueError, TypeError):
                        pass

        # Limit to top 5 skills
        top_skills = top_skills[:5]

        # Extract scene context
        scene_name = scene_context.get("name", "Unknown Location")
        scene_location = scene_context.get("location", "")
        scene_description = scene_context.get("description", "")

        # Format existing actions
        other_actions_text = ""
        if existing_actions:
            action_lines = []
            for action in existing_actions:
                char = action.get("character_name", "Someone")
                if action.get("speak"):
                    action_lines.append(f'- {char} says: "{action["speak"]}"')
                if action.get("act"):
                    action_lines.append(f'- {char} does: {action["act"]}')
            other_actions_text = "\n".join(action_lines)

        system_prompt = f"""You are roleplaying as {character_name}, an AI-controlled character in a Call of Cthulhu RPG.

CHARACTER PROFILE:
- Name: {character_name}
- Occupation: {occupation}
- Personality: {personality}
- Top Skills: {', '.join(top_skills) if top_skills else 'General investigator skills'}
{f"- Background: {backstory[:200]}" if backstory else ""}

BEHAVIOR GUIDELINES:
- Act according to your personality type: {personality}
- Use your skills and occupation to inform your actions
- Respond naturally to what other characters are doing
- Stay in character - you are not the Keeper/narrator
- Be concise and focused on your character's immediate actions
- Show emotion and personality through dialogue and actions

RESPONSE FORMAT:
Return ONLY a JSON object with these fields (all optional):
{{
  "speak": "What your character says (dialogue)",
  "act": "What your character does (physical action)",
  "appearance": "How your character looks/appears",
  "emotion": "Your character's emotional state",
  "ooc": "Out-of-character notes (rarely needed)"
}}

Example response:
{{
  "speak": "We should examine that bookshelf more closely.",
  "act": "cautiously approaches the dusty shelves, flashlight in hand",
  "emotion": "curious but wary"
}}"""

        user_prompt = f"""CURRENT SCENE: {scene_name}
{f"Location: {scene_location}" if scene_location else ""}
{f"Description: {scene_description[:300]}" if scene_description else ""}

OTHER PLAYER ACTIONS THIS TURN:
{other_actions_text if other_actions_text else "No other actions yet - you're acting first"}

As {character_name}, what do you do? Respond with JSON only:"""

        response = await self._call_llm(
            system_prompt,
            user_prompt,
            temperature=0.8,  # Higher temperature for more varied responses
            max_tokens=300
        )

        if response:
            # Try to parse JSON response
            import json
            try:
                # Clean up potential markdown formatting
                cleaned = response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                action_data = json.loads(cleaned)

                # Validate and return
                return {
                    "speak": action_data.get("speak", ""),
                    "act": action_data.get("act", ""),
                    "appearance": action_data.get("appearance", ""),
                    "emotion": action_data.get("emotion", ""),
                    "ooc": action_data.get("ooc", "")
                }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM JSON response: {response}")
                # Fallback: treat response as action text
                return {
                    "speak": "",
                    "act": response[:200],
                    "appearance": "",
                    "emotion": "",
                    "ooc": ""
                }

        # Fallback action if LLM fails
        return {
            "speak": "I'm observing the situation carefully.",
            "act": "stays alert and ready",
            "appearance": "",
            "emotion": "cautious",
            "ooc": ""
        }


# Singleton instance
llm_service = LLMService()
