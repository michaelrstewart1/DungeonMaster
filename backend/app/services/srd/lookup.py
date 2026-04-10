"""
SRD lookup service for D&D 5e reference data.
"""
from typing import Optional
from app.services.srd.models import SRDSpell, SRDMonster, SRDEquipment, SRDClass, SRDRace
from app.services.srd.data import srd_spells, srd_monsters, srd_equipment, srd_classes, srd_races


class SRDLookupService:
    """Service for looking up D&D 5e SRD reference data."""

    # ========================================================================
    # SPELL LOOKUPS
    # ========================================================================

    async def get_spell(self, name: str) -> Optional[SRDSpell]:
        """
        Get a spell by name (case-insensitive).

        Args:
            name: The spell name to search for

        Returns:
            The SRDSpell if found, None otherwise
        """
        name_lower = name.lower()
        for spell in srd_spells:
            if spell.name.lower() == name_lower:
                return spell
        return None

    async def search_spells(
        self,
        query: Optional[str] = None,
        class_name: Optional[str] = None,
        level: Optional[int] = None,
    ) -> list[SRDSpell]:
        """
        Search spells with optional filtering.

        Args:
            query: Substring to search in spell name
            class_name: Filter by class that can learn this spell
            level: Filter by spell level (0-9)

        Returns:
            List of matching spells
        """
        results = srd_spells.copy()

        # Filter by query (substring search)
        if query:
            query_lower = query.lower()
            results = [s for s in results if query_lower in s.name.lower()]

        # Filter by class
        if class_name:
            results = [s for s in results if class_name in s.classes]

        # Filter by level
        if level is not None:
            results = [s for s in results if s.level == level]

        return results

    # ========================================================================
    # MONSTER LOOKUPS
    # ========================================================================

    async def get_monster(self, name: str) -> Optional[SRDMonster]:
        """
        Get a monster by name (case-insensitive).

        Args:
            name: The monster name to search for

        Returns:
            The SRDMonster if found, None otherwise
        """
        name_lower = name.lower()
        for monster in srd_monsters:
            if monster.name.lower() == name_lower:
                return monster
        return None

    async def search_monsters(
        self,
        query: Optional[str] = None,
        cr_min: Optional[float] = None,
        cr_max: Optional[float] = None,
    ) -> list[SRDMonster]:
        """
        Search monsters with optional filtering.

        Args:
            query: Substring to search in monster name
            cr_min: Minimum challenge rating (inclusive)
            cr_max: Maximum challenge rating (inclusive)

        Returns:
            List of matching monsters
        """
        results = srd_monsters.copy()

        # Filter by query (substring search)
        if query:
            query_lower = query.lower()
            results = [m for m in results if query_lower in m.name.lower()]

        # Filter by CR range
        if cr_min is not None:
            results = [m for m in results if m.challenge_rating >= cr_min]

        if cr_max is not None:
            results = [m for m in results if m.challenge_rating <= cr_max]

        return results

    # ========================================================================
    # EQUIPMENT LOOKUPS
    # ========================================================================

    async def get_equipment(self, name: str) -> Optional[SRDEquipment]:
        """
        Get equipment by name (case-insensitive).

        Args:
            name: The equipment name to search for

        Returns:
            The SRDEquipment if found, None otherwise
        """
        name_lower = name.lower()
        for equipment in srd_equipment:
            if equipment.name.lower() == name_lower:
                return equipment
        return None

    async def search_equipment(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[SRDEquipment]:
        """
        Search equipment with optional filtering.

        Args:
            query: Substring to search in equipment name
            category: Filter by category

        Returns:
            List of matching equipment
        """
        results = srd_equipment.copy()

        # Filter by query (substring search)
        if query:
            query_lower = query.lower()
            results = [e for e in results if query_lower in e.name.lower()]

        # Filter by category
        if category:
            results = [e for e in results if e.category == category]

        return results

    # ========================================================================
    # CLASS LOOKUPS
    # ========================================================================

    async def get_class_info(self, name: str) -> Optional[SRDClass]:
        """
        Get class information by name (case-insensitive).

        Args:
            name: The class name to search for

        Returns:
            The SRDClass if found, None otherwise
        """
        name_lower = name.lower()
        for cls in srd_classes:
            if cls.name.lower() == name_lower:
                return cls
        return None

    async def get_all_classes(self) -> list[SRDClass]:
        """
        Get all available classes.

        Returns:
            List of all SRD classes
        """
        return srd_classes.copy()

    # ========================================================================
    # RACE LOOKUPS
    # ========================================================================

    async def get_race_info(self, name: str) -> Optional[SRDRace]:
        """
        Get race information by name (case-insensitive).

        Args:
            name: The race name to search for

        Returns:
            The SRDRace if found, None otherwise
        """
        name_lower = name.lower()
        for race in srd_races:
            if race.name.lower() == name_lower:
                return race
        return None

    async def get_all_races(self) -> list[SRDRace]:
        """
        Get all available races.

        Returns:
            List of all SRD races
        """
        return srd_races.copy()
