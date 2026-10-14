"""Absent heroes stay out of the DM prompt and out of the narration."""
from app.services.game.party import absent_party_notice, uncredit_absent_heroes
from app.services.llm.prompts import PromptTemplates


def test_prompt_credits_only_heroes_at_the_table():
    notice = absent_party_notice([
        {"name": "Lyra Moonwhisper"},
        {"name": "Kael Shadowstep"},
    ])
    present = [{"name": "Ashara Brightscale", "class": "Paladin", "level": 3}]
    full = PromptTemplates.dm_system_prompt(
        world_context=f"A sealed ward.\n\n{notice}",
        characters=present,
        game_state={},
        absent_characters=[{"name": "Lyra Moonwhisper"}, {"name": "Kael Shadowstep"}],
    )
    compact = PromptTemplates.dm_system_prompt(
        world_context=f"A sealed ward.\n\n{notice}",
        characters=present,
        game_state={},
        compact=True,
        absent_characters=[{"name": "Lyra Moonwhisper"}, {"name": "Kael Shadowstep"}],
    )
    for prompt in (full, compact):
        assert "Ashara Brightscale" in prompt
        assert "do not narrate them as acting" in prompt.lower()
        assert "Lyra Moonwhisper" in prompt
        assert "(absent)" in prompt
    party = full.split("## Player Characters", 1)[1].split("## Not at the table", 1)[0]
    assert "Ashara Brightscale" in party
    assert "Lyra" not in party
    assert "Kael" not in party


def test_narration_does_not_credit_an_absent_hero():
    text = uncredit_absent_heroes(
        "Ashara, observing Lyra's findings, steps forward. "
        "The abjuration magic Lyra detected earlier still hums. "
        "Kael Shadowstep would have known the glyph.",
        ["Lyra Moonwhisper", "Kael Shadowstep"],
    )
    assert "Lyra" not in text
    assert "Kael" not in text
    assert "Ashara" in text
    assert "steps forward" in text
    assert "the earlier findings" in text
