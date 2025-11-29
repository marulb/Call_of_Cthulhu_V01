"""
Skill check detection and dice rolling service.

Replaces n8n skill check nodes with Python-based detection and rolling.
Implements Call of Cthulhu 7th Edition dice mechanics.
"""
import logging
import random
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .context_assembly import SkillCheckContext, CharacterContext

logger = logging.getLogger(__name__)


# ============== Skill Check Models ==============

class DetectedSkillCheck(BaseModel):
    """Detected skill check from player actions."""
    character_id: str
    character_name: str
    skill_name: str
    difficulty: str = "Regular"  # Regular, Hard, Extreme
    reason: str = ""


class SkillCheckResult(BaseModel):
    """Result of a rolled skill check."""
    character_id: str
    character_name: str
    skill_name: str
    skill_value: int
    difficulty: str
    rolled: int
    target_regular: int
    target_hard: int
    target_extreme: int
    success_level: str  # Critical Success, Extreme Success, Hard Success, Regular Success, Failure, Fumble
    success: bool
    formatted: str


# ============== Skill Check Service ==============

class SkillCheckService:
    """Service for detecting and rolling skill checks."""

    # Call of Cthulhu 7e skill triggers (keyword → skill name)
    SKILL_TRIGGERS = {
        # Investigation
        r'\b(examine|inspect|search|look\s+for|find)\b': 'Spot Hidden',
        r'\b(listen|hear|eavesdrop)\b': 'Listen',
        r'\b(library|research|study|read|books)\b': 'Library Use',
        r'\b(track|follow\s+trail)\b': 'Track',

        # Knowledge
        r'\b(recall|remember|know|recognize)\b': 'INT',  # Generic knowledge check
        r'\b(mythos|elder\s+sign|ritual)\b': 'Cthulhu Mythos',
        r'\b(history|historical)\b': 'History',
        r'\b(occult|magic|supernatural)\b': 'Occult',

        # Social
        r'\b(convince|persuade|negotiate)\b': 'Persuade',
        r'\b(charm|seduce|flirt)\b': 'Charm',
        r'\b(intimidate|threaten)\b': 'Intimidate',
        r'\b(fast\s+talk|lie|deceive)\b': 'Fast Talk',
        r'\b(psychoanalyze|therapy)\b': 'Psychoanalysis',

        # Physical
        r'\b(sneak|hide|stealth)\b': 'Stealth',
        r'\b(climb)\b': 'Climb',
        r'\b(jump|leap)\b': 'Jump',
        r'\b(dodge|evade)\b': 'Dodge',
        r'\b(swim)\b': 'Swim',

        # Combat
        r'\b(shoot|fire|aim)\b': 'Firearms',
        r'\b(punch|hit|strike|brawl)\b': 'Fighting (Brawl)',
        r'\b(throw)\b': 'Throw',

        # Technical
        r'\b(repair|fix)\b': 'Mechanical Repair',
        r'\b(drive|pilot)\b': 'Drive Auto',
        r'\b(lockpick|pick\s+lock)\b': 'Locksmith',
        r'\b(operate\s+machinery)\b': 'Operate Heavy Machinery',

        # Medical
        r'\b(first\s+aid|bandage|treat\s+wound)\b': 'First Aid',
        r'\b(diagnose|medicine|surgery)\b': 'Medicine',
    }

    def __init__(self):
        """Initialize the skill check service."""
        self.compiled_triggers = {
            re.compile(pattern, re.IGNORECASE): skill
            for pattern, skill in self.SKILL_TRIGGERS.items()
        }

    def detect_skill_checks(
        self,
        actions: List[Dict[str, Any]],
        characters: List[CharacterContext]
    ) -> List[DetectedSkillCheck]:
        """
        Detect skill checks from player actions using keyword matching.

        Args:
            actions: List of player actions
            characters: List of characters involved

        Returns:
            List of detected skill checks
        """
        detected = []

        # Build character lookup
        char_map = {char.id: char for char in characters}

        for action in actions:
            actor_id = action.get("actor_id")
            if not actor_id or actor_id not in char_map:
                continue

            character = char_map[actor_id]

            # Combine action text for analysis
            text_parts = []
            if action.get("speak"):
                text_parts.append(action["speak"])
            if action.get("act"):
                text_parts.append(action["act"])
            if action.get("ooc"):
                text_parts.append(action["ooc"])

            combined_text = " ".join(text_parts)

            # Check against all triggers
            for pattern, skill_name in self.compiled_triggers.items():
                if pattern.search(combined_text):
                    # Determine difficulty based on context
                    difficulty = self._determine_difficulty(combined_text)

                    detected.append(DetectedSkillCheck(
                        character_id=character.id,
                        character_name=character.name,
                        skill_name=skill_name,
                        difficulty=difficulty,
                        reason=f"Action contains '{pattern.pattern}' trigger"
                    ))

                    logger.info(
                        f"Detected {skill_name} check for {character.name} "
                        f"(difficulty: {difficulty})"
                    )

        return detected

    def _determine_difficulty(self, text: str) -> str:
        """
        Determine difficulty level from action text.

        Looks for keywords like "carefully", "quickly", "in darkness", etc.
        """
        text_lower = text.lower()

        # Extreme difficulty keywords
        if any(word in text_lower for word in [
            "in darkness", "pitch black", "blindfolded", "while running",
            "under fire", "panic", "terrified"
        ]):
            return "Extreme"

        # Hard difficulty keywords
        if any(word in text_lower for word in [
            "quickly", "hurried", "dim light", "distracted",
            "carefully", "precisely", "hidden", "concealed"
        ]):
            return "Hard"

        # Default to regular
        return "Regular"

    async def roll_skill_checks(
        self,
        detected: List[DetectedSkillCheck],
        characters: List[CharacterContext]
    ) -> List[SkillCheckResult]:
        """
        Roll dice for detected skill checks.

        Implements CoC 7e success levels:
        - Fumble: 96-100
        - Failure: Above skill value
        - Regular Success: <= skill value
        - Hard Success: <= skill value / 2
        - Extreme Success: <= skill value / 5
        - Critical Success: 01
        """
        results = []

        # Build character lookup
        char_map = {char.id: char for char in characters}

        for check in detected:
            character = char_map.get(check.character_id)
            if not character:
                logger.warning(f"Character {check.character_id} not found for skill check")
                continue

            # Find skill value
            skill_value = self._find_skill_value(character, check.skill_name)

            if skill_value == 0:
                logger.warning(
                    f"Skill {check.skill_name} not found for {character.name}, "
                    f"using default value"
                )
                # Use default skill values for common skills
                skill_value = self._get_default_skill_value(check.skill_name)

            # Roll d100
            rolled = self.roll_d100()

            # Calculate thresholds
            target_regular = skill_value
            target_hard = skill_value // 2
            target_extreme = skill_value // 5

            # Determine success level
            success_level, success = self._determine_success(
                rolled, target_regular, target_hard, target_extreme
            )

            # Format result string
            formatted = (
                f"{character.name} rolled {check.skill_name}: "
                f"{rolled}/{skill_value} ({success_level})"
            )

            result = SkillCheckResult(
                character_id=character.id,
                character_name=character.name,
                skill_name=check.skill_name,
                skill_value=skill_value,
                difficulty=check.difficulty,
                rolled=rolled,
                target_regular=target_regular,
                target_hard=target_hard,
                target_extreme=target_extreme,
                success_level=success_level,
                success=success,
                formatted=formatted
            )

            results.append(result)

            logger.info(f"Rolled skill check: {formatted}")

        return results

    def _find_skill_value(
        self,
        character: CharacterContext,
        skill_name: str
    ) -> int:
        """Find skill value in character's skill list."""
        # Try exact match first
        for skill in character.skills:
            if skill.name.lower() == skill_name.lower():
                return skill.value

        # Try partial match (for skills with specializations)
        skill_base = skill_name.split("(")[0].strip().lower()
        for skill in character.skills:
            if skill.name.lower().startswith(skill_base):
                return skill.value

        return 0

    def _get_default_skill_value(self, skill_name: str) -> int:
        """Get default skill value for common skills (CoC 7e base values)."""
        defaults = {
            "Spot Hidden": 25,
            "Listen": 25,
            "Library Use": 25,
            "Persuade": 15,
            "Charm": 15,
            "Intimidate": 15,
            "Fast Talk": 5,
            "Stealth": 10,
            "Dodge": lambda dex: dex // 2,  # Would need DEX
            "Fighting (Brawl)": 25,
            "Firearms": 20,
            "First Aid": 30,
            "Psychoanalysis": 1,
            "Cthulhu Mythos": 0,
        }

        return defaults.get(skill_name, 20)  # Default base 20

    def roll_d100(self) -> int:
        """Roll a d100 (1-100)."""
        return random.randint(1, 100)

    def _determine_success(
        self,
        rolled: int,
        target_regular: int,
        target_hard: int,
        target_extreme: int
    ) -> tuple[str, bool]:
        """
        Determine success level based on roll and thresholds.

        Returns:
            Tuple of (success_level_string, is_success_bool)
        """
        # Critical Success
        if rolled == 1:
            return ("Critical Success", True)

        # Fumble
        if rolled >= 96:
            return ("Fumble", False)

        # Extreme Success
        if rolled <= target_extreme:
            return ("Extreme Success", True)

        # Hard Success
        if rolled <= target_hard:
            return ("Hard Success", True)

        # Regular Success
        if rolled <= target_regular:
            return ("Regular Success", True)

        # Failure
        return ("Failure", False)
