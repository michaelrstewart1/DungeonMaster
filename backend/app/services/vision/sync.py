"""Vision state sync service — updates game map state based on board analysis."""
from dataclasses import dataclass
from typing import Dict, Set, Tuple

from app.services.vision.analyzer import BoardAnalysis, TokenDetection
from app.models.schemas import MapResponse, TokenPosition


@dataclass
class TokenMove:
    """Represents a token movement between two analyses."""

    token_id: str
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]


class VisionStateSync:
    """Service for syncing vision analysis results to game map state."""

    def sync_to_map(self, analysis: BoardAnalysis, map_data: MapResponse) -> MapResponse:
        """
        Update token positions on the map based on vision analysis.

        Args:
            analysis: BoardAnalysis with detected token positions
            map_data: Current map state

        Returns:
            Updated MapResponse with synchronized token positions
        """
        # Create a mapping of entity_id to new position from analysis
        analysis_tokens: Dict[str, Tuple[int, int]] = {
            token.entity_id: (token.x, token.y) for token in analysis.tokens
        }

        # Update token positions based on analysis
        new_token_positions = []
        for entity_id, pos in analysis_tokens.items():
            new_token_positions.append(TokenPosition(entity_id=entity_id, x=pos[0], y=pos[1]))

        # Create updated map with new token positions
        return MapResponse(
            id=map_data.id,
            width=map_data.width,
            height=map_data.height,
            terrain_grid=map_data.terrain_grid,
            token_positions=new_token_positions,
            fog_of_war=map_data.fog_of_war,
        )

    def detect_changes(
        self, old_analysis: BoardAnalysis, new_analysis: BoardAnalysis
    ) -> list[TokenMove]:
        """
        Detect which tokens moved between two analyses.

        Args:
            old_analysis: Previous BoardAnalysis
            new_analysis: New BoardAnalysis

        Returns:
            List of TokenMove objects representing movements
        """
        # Create mappings of token positions
        old_tokens: Dict[str, Tuple[int, int]] = {
            token.entity_id: (token.x, token.y) for token in old_analysis.tokens
        }
        new_tokens: Dict[str, Tuple[int, int]] = {
            token.entity_id: (token.x, token.y) for token in new_analysis.tokens
        }

        moves: list[TokenMove] = []

        # Check for token moves
        all_token_ids: Set[str] = set(old_tokens.keys()) | set(new_tokens.keys())

        for token_id in all_token_ids:
            old_pos = old_tokens.get(token_id, (-1, -1))
            new_pos = new_tokens.get(token_id, (-1, -1))

            if old_pos != new_pos:
                moves.append(TokenMove(token_id=token_id, from_pos=old_pos, to_pos=new_pos))

        return moves
