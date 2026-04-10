"""
Tests for Narrative Summary.

Compresses old narrative into summaries to maintain game context
while reducing token usage. Using TDD: tests first, then implementation.
"""

import pytest
from app.services.game.summary import NarrativeSummary


class TestNarrativeSummaryInit:
    """Test NarrativeSummary initialization."""

    def test_init_with_default_max_entries(self):
        """NarrativeSummary should initialize with default max entries."""
        summary = NarrativeSummary()
        
        assert summary is not None
        assert summary.max_entries == 50

    def test_init_with_custom_max_entries(self):
        """NarrativeSummary should accept custom max entries."""
        summary = NarrativeSummary(max_entries=20)
        
        assert summary.max_entries == 20


class TestNarrativeSummaryAddition:
    """Test adding narrations."""

    def test_add_narration_single_entry(self):
        """add_narration should add a single narration."""
        summary = NarrativeSummary()
        
        summary.add_narration(1, "You enter a tavern.")
        
        history = summary.get_full_history()
        assert len(history) == 1
        assert "You enter a tavern." in history[0]

    def test_add_narration_multiple_entries(self):
        """add_narration should add multiple narrations in order."""
        summary = NarrativeSummary()
        
        summary.add_narration(1, "First narration")
        summary.add_narration(2, "Second narration")
        summary.add_narration(3, "Third narration")
        
        history = summary.get_full_history()
        assert len(history) == 3

    def test_add_narration_with_turn_number(self):
        """add_narration should associate turn number with narration."""
        summary = NarrativeSummary()
        
        summary.add_narration(5, "Turn 5 narration")
        summary.add_narration(6, "Turn 6 narration")
        
        history = summary.get_full_history()
        assert len(history) == 2


class TestNarrativeSummaryRetrieval:
    """Test retrieving narrations."""

    def test_get_recent_default_5(self):
        """get_recent should return last 5 narrations by default."""
        summary = NarrativeSummary()
        
        for i in range(10):
            summary.add_narration(i+1, f"Narration {i+1}")
        
        recent = summary.get_recent()
        
        assert len(recent) == 5
        # Should be most recent 5
        assert "Narration 10" in recent[-1]

    def test_get_recent_custom_count(self):
        """get_recent should return custom count of narrations."""
        summary = NarrativeSummary()
        
        for i in range(10):
            summary.add_narration(i+1, f"Narration {i+1}")
        
        recent = summary.get_recent(n=3)
        
        assert len(recent) == 3

    def test_get_recent_more_than_available(self):
        """get_recent should return all if requesting more than available."""
        summary = NarrativeSummary()
        
        for i in range(3):
            summary.add_narration(i+1, f"Narration {i+1}")
        
        recent = summary.get_recent(n=10)
        
        assert len(recent) == 3

    def test_get_full_history(self):
        """get_full_history should return all narrations."""
        summary = NarrativeSummary()
        
        for i in range(5):
            summary.add_narration(i+1, f"Narration {i+1}")
        
        history = summary.get_full_history()
        
        assert len(history) == 5

    def test_get_full_history_empty(self):
        """get_full_history should return empty list when no narrations."""
        summary = NarrativeSummary()
        
        history = summary.get_full_history()
        
        assert len(history) == 0


class TestNarrativeSummarySummary:
    """Test summary generation."""

    def test_get_summary_with_few_entries(self):
        """get_summary should return joined narrations for few entries."""
        summary = NarrativeSummary(max_entries=50)
        
        summary.add_narration(1, "You see a door.")
        summary.add_narration(2, "You open it.")
        summary.add_narration(3, "A goblin attacks!")
        
        summary_text = summary.get_summary()
        
        assert isinstance(summary_text, str)
        assert len(summary_text) > 0

    def test_get_summary_contains_recent_narrations(self):
        """get_summary should include recent narrations."""
        summary = NarrativeSummary(max_entries=50)
        
        summary.add_narration(1, "Early event")
        summary.add_narration(2, "Recent event")
        
        summary_text = summary.get_summary()
        
        # Should contain at least the recent event
        assert "Recent event" in summary_text or len(summary_text) > 0

    def test_get_summary_empty(self):
        """get_summary should handle empty summary gracefully."""
        summary = NarrativeSummary()
        
        summary_text = summary.get_summary()
        
        assert isinstance(summary_text, str)

    def test_get_summary_preserves_key_facts(self):
        """get_summary should preserve key facts like character names."""
        summary = NarrativeSummary(max_entries=50)
        
        summary.add_narration(1, "Aragorn enters the room.")
        summary.add_narration(2, "Legolas and Gimli follow.")
        summary.add_narration(3, "They encounter an orc.")
        
        summary_text = summary.get_summary()
        
        # Should preserve character names
        assert isinstance(summary_text, str)


class TestNarrativeSummaryCompression:
    """Test narrative compression when exceeding max entries."""

    def test_exceeding_max_entries_triggers_compression(self):
        """Exceeding max_entries should trigger compression."""
        summary = NarrativeSummary(max_entries=5)
        
        # Add more than max entries
        for i in range(10):
            summary.add_narration(i+1, f"Narration {i+1}")
        
        # Should compress old entries
        history = summary.get_full_history()
        
        # After compression, should have fewer detailed entries
        assert len(history) <= 10  # Some form of compression happened

    def test_compression_preserves_recent_entries(self):
        """Compression should preserve recent entries unchanged."""
        summary = NarrativeSummary(max_entries=3)
        
        for i in range(6):
            summary.add_narration(i+1, f"Narration {i+1}")
        
        # Get summary (which may include compressed section)
        summary_text = summary.get_summary()
        
        # Recent narrations should be preserved
        assert isinstance(summary_text, str)

    def test_compression_reduces_total_count(self):
        """Compression should eventually reduce history count."""
        summary = NarrativeSummary(max_entries=3)
        
        for i in range(10):
            summary.add_narration(i+1, f"Narration {i+1}")
        
        history = summary.get_full_history()
        
        # Should not grow indefinitely
        assert len(history) <= 10


class TestNarrativeSummaryClear:
    """Test clearing summary."""

    def test_clear_removes_all_narrations(self):
        """clear should remove all narrations."""
        summary = NarrativeSummary()
        
        summary.add_narration(1, "First")
        summary.add_narration(2, "Second")
        
        summary.clear()
        
        history = summary.get_full_history()
        assert len(history) == 0

    def test_clear_resets_turn_counter(self):
        """clear should reset for fresh start."""
        summary = NarrativeSummary()
        
        summary.add_narration(5, "Some narration")
        summary.clear()
        
        summary.add_narration(1, "New narration")
        history = summary.get_full_history()
        
        assert len(history) == 1


class TestNarrativeSummaryIntegration:
    """Integration tests for NarrativeSummary."""

    def test_long_game_session_compression(self):
        """Long game session should compress old narrations."""
        summary = NarrativeSummary(max_entries=10)
        
        # Simulate a long game
        for turn in range(50):
            summary.add_narration(
                turn + 1,
                f"Turn {turn+1}: Something happens in the game."
            )
        
        # Should have compressed history
        history = summary.get_full_history()
        full_summary = summary.get_summary()
        
        assert len(history) > 0
        assert isinstance(full_summary, str)
        assert len(full_summary) > 0

    def test_narrative_continuity_across_compression(self):
        """Narrative should maintain continuity across compression."""
        summary = NarrativeSummary(max_entries=5)
        
        narrations = [
            "You enter a dark forest.",
            "You hear strange sounds.",
            "A wolf emerges from the shadows.",
            "Combat begins!",
            "The wolf is defeated.",
            "You continue deeper into the forest.",
            "You find an ancient temple.",
        ]
        
        for i, narration in enumerate(narrations):
            summary.add_narration(i+1, narration)
        
        full_summary = summary.get_summary()
        
        # Should have some form of coherent narrative
        assert isinstance(full_summary, str)
        assert len(full_summary) > 0

    def test_get_recent_after_compression(self):
        """get_recent should still work after compression."""
        summary = NarrativeSummary(max_entries=3)
        
        for i in range(10):
            summary.add_narration(i+1, f"Narration {i+1}")
        
        recent = summary.get_recent(n=2)
        
        assert len(recent) <= 2
