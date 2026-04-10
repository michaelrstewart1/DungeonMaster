"""
Narrative Summary for D&D 5e AI Dungeon Master.

Compresses old narrative into summaries to maintain game context
while reducing token usage for LLM interactions.
"""

from typing import Optional


class NarrativeSummary:
    """Manages and compresses game narration history."""

    def __init__(self, max_entries: int = 50):
        """
        Initialize the NarrativeSummary.
        
        Args:
            max_entries: Maximum number of narration entries before compression
        """
        self.max_entries = max_entries
        self._entries: list[tuple[int, str]] = []  # List of (turn_number, narration) tuples
        self._compressed_summary: Optional[str] = None

    def add_narration(self, turn_number: int, text: str) -> None:
        """
        Add a narration entry.
        
        Args:
            turn_number: Turn number this narration occurred on
            text: Narration text
        """
        self._entries.append((turn_number, text))

        # Check if we need to compress
        if len(self._entries) > self.max_entries:
            self._compress_old_entries()

    def get_recent(self, n: int = 5) -> list[str]:
        """
        Get the last n narrations.
        
        Args:
            n: Number of recent narrations to return
            
        Returns:
            List of narration strings
        """
        if self._compressed_summary:
            # If we have a compressed summary, include it
            entries = [self._compressed_summary] + [text for _, text in self._entries]
        else:
            entries = [text for _, text in self._entries]

        return entries[-n:] if len(entries) > 0 else []

    def get_full_history(self) -> list[str]:
        """
        Get all narrations in history.
        
        Returns:
            List of all narration strings
        """
        if self._compressed_summary:
            return [self._compressed_summary] + [text for _, text in self._entries]
        else:
            return [text for _, text in self._entries]

    def get_summary(self) -> str:
        """
        Get a compressed summary of the narrative.
        
        Returns:
            Summary string combining compressed and recent narrations
        """
        if not self._entries and not self._compressed_summary:
            return ""

        summary_parts = []

        if self._compressed_summary:
            summary_parts.append(self._compressed_summary)

        # Add recent entries
        if self._entries:
            recent_text = " ".join([text for _, text in self._entries])
            summary_parts.append(recent_text)

        return " ".join(summary_parts)

    def clear(self) -> None:
        """Clear all narration history."""
        self._entries = []
        self._compressed_summary = None

    def _compress_old_entries(self) -> None:
        """
        Compress old entries into a summary block.
        
        Keeps recent entries as-is and combines older ones into a summary.
        """
        if len(self._entries) <= self.max_entries:
            return

        # Keep the most recent entries separate
        keep_count = max(5, self.max_entries // 2)
        entries_to_compress = self._entries[:-keep_count]
        self._entries = self._entries[-keep_count:]

        # Create compressed summary
        if entries_to_compress:
            compressed = self._create_compression(entries_to_compress)
            if self._compressed_summary:
                self._compressed_summary = compressed
            else:
                self._compressed_summary = compressed

    def _create_compression(self, entries: list[tuple[int, str]]) -> str:
        """
        Create a compressed summary from entries.
        
        Args:
            entries: List of (turn_number, narration) tuples to compress
            
        Returns:
            Compressed summary string
        """
        if not entries:
            return ""

        # Extract key facts: character names, locations, important events
        narrations = [text for _, text in entries]
        combined = " ".join(narrations)

        # Create a brief summary
        # For now, just join and truncate key parts
        sentences = combined.split(".")
        
        # Keep important sentences (those with names, action words, etc)
        key_sentences = []
        for sentence in sentences[:len(sentences) // 2]:  # Keep first half
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in 
                   ["encounter", "defeat", "defeat", "meet", "discover", "find", 
                    "enter", "leave", "battle", "combat", "treasure", "trap"]):
                key_sentences.append(sentence)

        # If we don't have enough key sentences, just use the beginning
        if not key_sentences:
            key_sentences = [s.strip() for s in sentences[:3] if s.strip()]

        # Create compression
        compression = "Previously: " + ". ".join(key_sentences)
        if len(compression) > 500:
            compression = compression[:500] + "..."

        return compression
