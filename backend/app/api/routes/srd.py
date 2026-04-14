"""
API routes for D&D 5e SRD reference data.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.srd.lookup import SRDLookupService
from app.services.srd.models import (
    SRDSpell, SRDMonster, SRDEquipment, SRDClass, SRDRace,
    SRDSubrace, SRDSubclass, SRDBackground, SRDSkill, SRDFeat,
)

router = APIRouter(tags=["srd"])
lookup_service = SRDLookupService()


# ============================================================================
# SPELL ROUTES
# ============================================================================


@router.get("/srd/spells", response_model=list[SRDSpell])
async def list_spells(
    q: Optional[str] = Query(None, description="Search by spell name substring"),
    class_name: Optional[str] = Query(None, description="Filter by class"),
    level: Optional[int] = Query(None, ge=0, le=9, description="Filter by spell level"),
) -> list[SRDSpell]:
    """
    List or search spells.

    Query parameters:
    - q: Search by name substring
    - class_name: Filter by class that can learn the spell
    - level: Filter by spell level (0-9)
    """
    return await lookup_service.search_spells(query=q, class_name=class_name, level=level)


@router.get("/srd/spells/{name}", response_model=SRDSpell)
async def get_spell(name: str) -> SRDSpell:
    """Get a spell by name (case-insensitive)."""
    spell = await lookup_service.get_spell(name)
    if spell is None:
        raise HTTPException(status_code=404, detail=f"Spell '{name}' not found")
    return spell


# ============================================================================
# MONSTER ROUTES
# ============================================================================


@router.get("/srd/monsters", response_model=list[SRDMonster])
async def list_monsters(
    q: Optional[str] = Query(None, description="Search by monster name substring"),
    cr_min: Optional[float] = Query(None, ge=0, description="Minimum challenge rating"),
    cr_max: Optional[float] = Query(None, ge=0, description="Maximum challenge rating"),
) -> list[SRDMonster]:
    """
    List or search monsters.

    Query parameters:
    - q: Search by name substring
    - cr_min: Minimum challenge rating
    - cr_max: Maximum challenge rating
    """
    return await lookup_service.search_monsters(query=q, cr_min=cr_min, cr_max=cr_max)


@router.get("/srd/monsters/{name}", response_model=SRDMonster)
async def get_monster(name: str) -> SRDMonster:
    """Get a monster by name (case-insensitive)."""
    monster = await lookup_service.get_monster(name)
    if monster is None:
        raise HTTPException(status_code=404, detail=f"Monster '{name}' not found")
    return monster


# ============================================================================
# EQUIPMENT ROUTES
# ============================================================================


@router.get("/srd/equipment", response_model=list[SRDEquipment])
async def list_equipment(
    q: Optional[str] = Query(None, description="Search by equipment name substring"),
    category: Optional[str] = Query(None, description="Filter by category"),
) -> list[SRDEquipment]:
    """
    List or search equipment.

    Query parameters:
    - q: Search by name substring
    - category: Filter by category (Weapons, Armor, Adventuring Gear)
    """
    return await lookup_service.search_equipment(query=q, category=category)


@router.get("/srd/equipment/{name}", response_model=SRDEquipment)
async def get_equipment(name: str) -> SRDEquipment:
    """Get equipment by name (case-insensitive)."""
    equipment = await lookup_service.get_equipment(name)
    if equipment is None:
        raise HTTPException(status_code=404, detail=f"Equipment '{name}' not found")
    return equipment


# ============================================================================
# CLASS ROUTES
# ============================================================================


@router.get("/srd/classes", response_model=list[SRDClass])
async def list_classes() -> list[SRDClass]:
    """Get all available D&D 5e classes."""
    return await lookup_service.get_all_classes()


@router.get("/srd/classes/{name}", response_model=SRDClass)
async def get_class(name: str) -> SRDClass:
    """Get class information by name (case-insensitive)."""
    cls = await lookup_service.get_class_info(name)
    if cls is None:
        raise HTTPException(status_code=404, detail=f"Class '{name}' not found")
    return cls


# ============================================================================
# RACE ROUTES
# ============================================================================


@router.get("/srd/races", response_model=list[SRDRace])
async def list_races() -> list[SRDRace]:
    """Get all available D&D 5e races."""
    return await lookup_service.get_all_races()


@router.get("/srd/races/{name}", response_model=SRDRace)
async def get_race(name: str) -> SRDRace:
    """Get race information by name (case-insensitive)."""
    race = await lookup_service.get_race_info(name)
    if race is None:
        raise HTTPException(status_code=404, detail=f"Race '{name}' not found")
    return race


# ============================================================================
# CHARACTER CREATION DATA ROUTES
# ============================================================================


@router.get("/srd/chargen/subraces", response_model=list[SRDSubrace])
async def list_subraces(
    race: Optional[str] = Query(None, description="Filter by parent race"),
) -> list[SRDSubrace]:
    """Get subraces, optionally filtered by parent race."""
    return await lookup_service.get_subraces(race=race)


@router.get("/srd/chargen/subclasses", response_model=list[SRDSubclass])
async def list_subclasses(
    class_name: Optional[str] = Query(None, description="Filter by parent class"),
) -> list[SRDSubclass]:
    """Get subclasses, optionally filtered by parent class."""
    return await lookup_service.get_subclasses(class_name=class_name)


@router.get("/srd/chargen/backgrounds", response_model=list[SRDBackground])
async def list_backgrounds() -> list[SRDBackground]:
    """Get all available backgrounds."""
    return await lookup_service.get_backgrounds()


@router.get("/srd/chargen/skills", response_model=list[SRDSkill])
async def list_skills() -> list[SRDSkill]:
    """Get all 18 D&D 5e skills."""
    return await lookup_service.get_skills()


@router.get("/srd/chargen/feats", response_model=list[SRDFeat])
async def list_feats() -> list[SRDFeat]:
    """Get all available feats."""
    return await lookup_service.get_feats()
