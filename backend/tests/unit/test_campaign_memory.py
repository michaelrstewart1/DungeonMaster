"""Campaign memory service — extraction merge + retrieval ranking."""
from app.services.game.memory import (
    _parse_extraction,
    build_memory_context,
    merge_extraction,
)


def _empty_memory() -> dict:
    return {"campaign_id": "c1", "events": [], "quests": [], "npcs": [], "locations": []}


class TestParseExtraction:
    def test_plain_json(self):
        raw = '{"events": ["The party met Mira"]}'
        assert _parse_extraction(raw) == {"events": ["The party met Mira"]}

    def test_markdown_fenced(self):
        raw = '```json\n{"events": ["Fact"]}\n```'
        assert _parse_extraction(raw) == {"events": ["Fact"]}

    def test_json_with_prose(self):
        raw = 'Here is the memory update:\n{"quests": [{"title": "Find the amulet", "status": "active"}]}'
        assert _parse_extraction(raw)["quests"][0]["title"] == "Find the amulet"

    def test_garbage_returns_empty(self):
        assert _parse_extraction("no json here") == {}
        assert _parse_extraction("{broken json") == {}


class TestMergeExtraction:
    def test_adds_events_with_metadata(self):
        mem = _empty_memory()
        merge_extraction(mem, {"events": ["The dragon fled north"]}, "s1", 5)
        assert mem["events"][0]["fact"] == "The dragon fled north"
        assert mem["events"][0]["session_id"] == "s1"
        assert mem["events"][0]["turn"] == 5

    def test_deduplicates_events(self):
        mem = _empty_memory()
        merge_extraction(mem, {"events": ["The dragon fled north"]}, "s1", 1)
        merge_extraction(mem, {"events": ["the dragon fled NORTH"]}, "s1", 2)
        assert len(mem["events"]) == 1

    def test_quest_status_update(self):
        mem = _empty_memory()
        merge_extraction(mem, {"quests": [{"title": "Rescue Mira", "status": "active"}]}, "s1", 1)
        merge_extraction(mem, {"quests": [{"title": "rescue mira", "status": "completed"}]}, "s1", 9)
        assert len(mem["quests"]) == 1
        assert mem["quests"][0]["status"] == "completed"

    def test_npc_merge_and_death(self):
        mem = _empty_memory()
        merge_extraction(mem, {"npcs": [{"name": "Grim", "npc_type": "guard", "disposition": "neutral"}]}, "s1", 1)
        merge_extraction(mem, {"npcs": [{"name": "grim", "alive": False, "notes": "Killed by the wyvern"}]}, "s2", 3)
        assert len(mem["npcs"]) == 1
        npc = mem["npcs"][0]
        assert npc["alive"] is False
        assert npc["npc_type"] == "guard"  # earlier info retained
        assert "wyvern" in npc["notes"].lower()

    def test_locations_merge(self):
        mem = _empty_memory()
        merge_extraction(mem, {"locations": [{"name": "Duskhollow", "description": "A mining village"}]}, "s1", 1)
        merge_extraction(mem, {"locations": [{"name": "duskhollow", "description": "A mining village, now burned"}]}, "s1", 4)
        assert len(mem["locations"]) == 1
        assert "burned" in mem["locations"][0]["description"]

    def test_ignores_malformed_entries(self):
        mem = _empty_memory()
        merge_extraction(mem, {"events": [None, "", 42, "Valid fact"], "npcs": [{"no_name": True}]}, "s1", 1)
        assert len(mem["events"]) == 1
        assert mem["npcs"] == []


class TestBuildMemoryContext:
    def test_empty_memory_returns_empty(self):
        assert build_memory_context(_empty_memory(), "I attack") == ""
        assert build_memory_context({}, "I attack") == ""

    def test_active_quests_always_included(self):
        mem = _empty_memory()
        mem["quests"] = [
            {"title": "Rescue Mira", "status": "active", "notes": ""},
            {"title": "Old job", "status": "completed", "notes": ""},
        ]
        block = build_memory_context(mem, "I look around")
        assert "Rescue Mira" in block
        assert "Old job" not in block

    def test_relevant_events_ranked_by_overlap(self):
        mem = _empty_memory()
        mem["events"] = [
            {"fact": f"Filler fact number {i}", "turn": i} for i in range(20)
        ]
        mem["events"].insert(0, {"fact": "The party promised Grim the guard 50 gold", "turn": 0})
        block = build_memory_context(mem, "I go talk to Grim about the gold we owe him")
        assert "promised Grim" in block

    def test_npc_mentioned_by_name_included(self):
        mem = _empty_memory()
        mem["npcs"] = [
            {"name": f"Extra{i}", "npc_type": "villager", "alive": True} for i in range(10)
        ]
        mem["npcs"].insert(0, {"name": "Mira", "npc_type": "merchant", "disposition": "friendly",
                               "location": "Duskhollow", "notes": "Owes the party a favor", "alive": True})
        block = build_memory_context(mem, "I ask Mira about the amulet")
        assert "Mira" in block
        assert "merchant" in block

    def test_dead_npc_marked(self):
        mem = _empty_memory()
        mem["npcs"] = [{"name": "Grim", "npc_type": "guard", "alive": False}]
        block = build_memory_context(mem, "I look for Grim")
        assert "[DEAD]" in block

    def test_location_included_when_referenced(self):
        mem = _empty_memory()
        mem["locations"] = [{"name": "Duskhollow", "description": "A burned mining village", "visited": True}]
        assert "Duskhollow" in build_memory_context(mem, "We travel to Duskhollow")
        assert "Duskhollow" not in build_memory_context(mem, "I attack the goblin")
