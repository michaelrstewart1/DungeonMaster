"""Board analyzer — uses Vision LLM to interpret physical game board images."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TokenDetection:
    entity_id: str
    x: int
    y: int
    confidence: float


@dataclass
class BoardAnalysis:
    grid_width: int
    grid_height: int
    tokens: list[TokenDetection]
    confidence: float = 0.0
    raw_description: str = ""


class BoardAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, image_bytes: bytes) -> BoardAnalysis:
        """Analyze a board image and return structured grid data."""


class FakeBoardAnalyzer(BoardAnalyzer):
    """Test double for board analysis."""

    def __init__(
        self,
        grid_size: tuple[int, int] = (10, 10),
        tokens: list[TokenDetection] | None = None,
    ):
        self._grid_size = grid_size
        self._tokens = tokens or []
        self.call_count = 0
        self.received_images: list[bytes] = []

    async def analyze(self, image_bytes: bytes) -> BoardAnalysis:
        self.call_count += 1
        self.received_images.append(image_bytes)
        return BoardAnalysis(
            grid_width=self._grid_size[0],
            grid_height=self._grid_size[1],
            tokens=self._tokens,
            confidence=0.95,
            raw_description=f"Analyzed board: {self._grid_size[0]}x{self._grid_size[1]}",
        )
