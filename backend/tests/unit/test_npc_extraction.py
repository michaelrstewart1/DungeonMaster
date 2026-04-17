"""Unit tests for NPC extraction and scene detection from narration."""
import pytest
from app.api.routes.game import (
    _extract_npcs_from_narration,
    _detect_npc_type,
    _detect_scene_type,
    _merge_detected_npcs,
)


class TestExtractNPCsFromNarration:
    """Tests for _extract_npcs_from_narration."""

    def test_extracts_named_npc_from_speech_before_quote(self):
        """Pattern: Kaelrath says 'Hello' → extracts Kaelrath."""
        text = 'Kaelrath says "Welcome, traveler. What brings you to my domain?"'
        result = _extract_npcs_from_narration(text)
        assert len(result) == 1
        assert result[0]["name"] == "Kaelrath"

    def test_extracts_named_npc_from_speech_after_quote(self):
        """Pattern: 'Hello' replies Kaelrath → extracts Kaelrath."""
        text = '"I know nothing of this matter" replies Voss'
        result = _extract_npcs_from_narration(text)
        assert len(result) == 1
        assert result[0]["name"] == "Voss"

    def test_extracts_multiword_name(self):
        """Should handle two-word proper names."""
        text = 'Sister Elara whispers "Be careful in the crypt."'
        result = _extract_npcs_from_narration(text)
        assert len(result) == 1
        assert result[0]["name"] == "Sister Elara"

    def test_ignores_generic_roles(self):
        """Should not extract generic roles like 'Guard' or 'Merchant'."""
        text = 'The guard says "Move along, nothing to see here."'
        result = _extract_npcs_from_narration(text)
        assert len(result) == 0

    def test_extracts_introduction_pattern(self):
        """Pattern: introduces himself as Lord Voss."""
        text = "The cloaked figure introduces himself as Lord Varyn and beckons you closer."
        result = _extract_npcs_from_narration(text)
        assert any(n["name"] == "Lord Varyn" for n in result)

    def test_deduplicates_same_name(self):
        """Same NPC speaking twice should yield one entry."""
        text = (
            'Kaelrath says "Hello there." You respond. '
            'Kaelrath replies "Interesting."'
        )
        result = _extract_npcs_from_narration(text)
        assert len(result) == 1

    def test_extracts_multiple_npcs(self):
        """Multiple distinct NPCs in one narration."""
        text = (
            'Theron says "The road ahead is dangerous." '
            'Mirabel replies "We have no choice."'
        )
        result = _extract_npcs_from_narration(text)
        names = {n["name"] for n in result}
        assert "Theron" in names
        assert "Mirabel" in names

    def test_no_npcs_in_descriptive_text(self):
        """Pure description with no speech should return empty."""
        text = "The ancient forest stretches endlessly before you. Moss covers the crumbling stones."
        result = _extract_npcs_from_narration(text)
        assert len(result) == 0


class TestDetectNPCType:
    """Tests for _detect_npc_type."""

    def test_merchant_keywords(self):
        assert _detect_npc_type("the merchant shows you his wares") == "merchant"

    def test_guard_keywords(self):
        assert _detect_npc_type("the knight stands at the gate") == "guard"

    def test_wizard_keywords(self):
        assert _detect_npc_type("the sorcerer conjures a flame") == "wizard"

    def test_innkeeper_keywords(self):
        assert _detect_npc_type("the bartender pours you an ale") == "innkeeper"

    def test_noble_keywords(self):
        assert _detect_npc_type("the duchess gazes from her throne") == "noble"

    def test_default_fallback(self):
        assert _detect_npc_type("a figure stands in the doorway") == "default"


class TestDetectSceneType:
    """Tests for _detect_scene_type."""

    def test_tavern_detection(self):
        assert _detect_scene_type("You enter a dimly lit tavern. The barkeep nods.") == "tavern"

    def test_dungeon_detection(self):
        assert _detect_scene_type("The dungeon walls drip with moisture.") == "dungeon"

    def test_forest_detection(self):
        assert _detect_scene_type("Tall trees form a canopy overhead in the ancient forest.") == "forest"

    def test_castle_detection(self):
        assert _detect_scene_type("You approach the fortress gates. The battlements loom.") == "castle"

    def test_temple_detection(self):
        assert _detect_scene_type("The shrine glows with a faint sacred light.") == "temple"

    def test_none_for_generic_text(self):
        assert _detect_scene_type("You look around carefully.") is None

    def test_market_detection(self):
        assert _detect_scene_type("The bustling market square is full of vendors.") == "market"

    def test_cave_detection(self):
        assert _detect_scene_type("Stalactites hang from the cavern ceiling.") == "cave"


class TestMergeDetectedNPCs:
    """Tests for _merge_detected_npcs."""

    def test_adds_new_npcs_to_empty_session(self):
        session: dict = {}
        _merge_detected_npcs(session, [{"name": "Kaelrath", "npc_type": "default"}])
        assert len(session["npcs"]) == 1
        assert session["npcs"][0]["name"] == "Kaelrath"
        assert session["npcs"][0]["disposition"] == "neutral"

    def test_deduplicates_by_name_case_insensitive(self):
        session = {"npcs": [{"name": "Kaelrath", "npc_type": "default", "disposition": "hostile"}]}
        _merge_detected_npcs(session, [{"name": "kaelrath", "npc_type": "merchant"}])
        assert len(session["npcs"]) == 1  # no duplicate added

    def test_adds_only_new_npcs(self):
        session = {"npcs": [{"name": "Theron", "npc_type": "guard", "disposition": "neutral"}]}
        _merge_detected_npcs(session, [
            {"name": "Theron", "npc_type": "guard"},
            {"name": "Mirabel", "npc_type": "wizard"},
        ])
        assert len(session["npcs"]) == 2
        names = {n["name"] for n in session["npcs"]}
        assert names == {"Theron", "Mirabel"}

    def test_empty_detected_does_nothing(self):
        session = {"npcs": [{"name": "Kaelrath"}]}
        _merge_detected_npcs(session, [])
        assert len(session["npcs"]) == 1
