"""Tests for vision state sync service."""
import pytest
from dataclasses import dataclass

from app.services.vision.analyzer import BoardAnalysis, TokenDetection
from app.models.schemas import MapResponse, TokenPosition
from app.services.vision.sync import VisionStateSync, TokenMove


class TestTokenMove:
    """Test TokenMove dataclass."""

    def test_token_move_creation(self):
        """Test creating a token move."""
        move = TokenMove(token_id="player1", from_pos=(0, 0), to_pos=(1, 1))
        assert move.token_id == "player1"
        assert move.from_pos == (0, 0)
        assert move.to_pos == (1, 1)


class TestVisionStateSync:
    """Test VisionStateSync service."""

    @pytest.fixture
    def sync_service(self):
        """Create a sync service."""
        return VisionStateSync()

    @pytest.fixture
    def sample_map(self):
        """Create a sample map."""
        return MapResponse(
            id="map1",
            width=10,
            height=10,
            terrain_grid=[],
            token_positions=[
                TokenPosition(entity_id="player1", x=0, y=0),
                TokenPosition(entity_id="player2", x=5, y=5),
            ],
            fog_of_war=[],
        )

    def test_sync_to_map_updates_token_positions(self, sync_service, sample_map):
        """Test syncing analysis results to map updates token positions."""
        analysis = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=1, y=1, confidence=0.95),
                TokenDetection(entity_id="player2", x=6, y=6, confidence=0.95),
            ],
            confidence=0.95,
        )

        updated_map = sync_service.sync_to_map(analysis, sample_map)

        assert len(updated_map.token_positions) == 2
        assert updated_map.token_positions[0].entity_id == "player1"
        assert updated_map.token_positions[0].x == 1
        assert updated_map.token_positions[0].y == 1
        assert updated_map.token_positions[1].entity_id == "player2"
        assert updated_map.token_positions[1].x == 6
        assert updated_map.token_positions[1].y == 6

    def test_sync_to_map_adds_new_tokens(self, sync_service, sample_map):
        """Test syncing adds new tokens that appear on the board."""
        analysis = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=1, y=1, confidence=0.95),
                TokenDetection(entity_id="player2", x=6, y=6, confidence=0.95),
                TokenDetection(entity_id="npc1", x=3, y=3, confidence=0.90),
            ],
            confidence=0.95,
        )

        updated_map = sync_service.sync_to_map(analysis, sample_map)

        assert len(updated_map.token_positions) == 3
        entity_ids = {token.entity_id for token in updated_map.token_positions}
        assert entity_ids == {"player1", "player2", "npc1"}

    def test_sync_to_map_removes_tokens_not_detected(self, sync_service, sample_map):
        """Test syncing removes tokens that are no longer on the board."""
        analysis = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=1, y=1, confidence=0.95),
            ],
            confidence=0.95,
        )

        updated_map = sync_service.sync_to_map(analysis, sample_map)

        # Only player1 should remain
        assert len(updated_map.token_positions) == 1
        assert updated_map.token_positions[0].entity_id == "player1"

    def test_sync_to_map_preserves_map_dimensions(self, sync_service, sample_map):
        """Test that syncing preserves map dimensions."""
        analysis = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[],
            confidence=0.95,
        )

        updated_map = sync_service.sync_to_map(analysis, sample_map)

        assert updated_map.width == sample_map.width
        assert updated_map.height == sample_map.height

    def test_detect_changes_no_changes(self, sync_service):
        """Test detecting no changes when analyses are identical."""
        analysis1 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=0, y=0, confidence=0.95),
                TokenDetection(entity_id="player2", x=5, y=5, confidence=0.95),
            ],
            confidence=0.95,
        )
        analysis2 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=0, y=0, confidence=0.95),
                TokenDetection(entity_id="player2", x=5, y=5, confidence=0.95),
            ],
            confidence=0.95,
        )

        changes = sync_service.detect_changes(analysis1, analysis2)

        assert len(changes) == 0

    def test_detect_changes_token_moves(self, sync_service):
        """Test detecting token moves between two analyses."""
        analysis1 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=0, y=0, confidence=0.95),
                TokenDetection(entity_id="player2", x=5, y=5, confidence=0.95),
            ],
            confidence=0.95,
        )
        analysis2 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=1, y=1, confidence=0.95),
                TokenDetection(entity_id="player2", x=5, y=5, confidence=0.95),
            ],
            confidence=0.95,
        )

        changes = sync_service.detect_changes(analysis1, analysis2)

        assert len(changes) == 1
        assert changes[0].token_id == "player1"
        assert changes[0].from_pos == (0, 0)
        assert changes[0].to_pos == (1, 1)

    def test_detect_changes_multiple_moves(self, sync_service):
        """Test detecting multiple token moves."""
        analysis1 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=0, y=0, confidence=0.95),
                TokenDetection(entity_id="player2", x=5, y=5, confidence=0.95),
            ],
            confidence=0.95,
        )
        analysis2 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=1, y=1, confidence=0.95),
                TokenDetection(entity_id="player2", x=6, y=6, confidence=0.95),
            ],
            confidence=0.95,
        )

        changes = sync_service.detect_changes(analysis1, analysis2)

        assert len(changes) == 2
        move_ids = {change.token_id for change in changes}
        assert move_ids == {"player1", "player2"}

    def test_detect_changes_token_added(self, sync_service):
        """Test detecting when a new token appears."""
        analysis1 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=0, y=0, confidence=0.95),
            ],
            confidence=0.95,
        )
        analysis2 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=0, y=0, confidence=0.95),
                TokenDetection(entity_id="player2", x=5, y=5, confidence=0.95),
            ],
            confidence=0.95,
        )

        changes = sync_service.detect_changes(analysis1, analysis2)

        # When a token appears, it's treated as a move from (-1, -1)
        assert len(changes) == 1
        assert changes[0].token_id == "player2"

    def test_detect_changes_token_removed(self, sync_service):
        """Test detecting when a token disappears."""
        analysis1 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=0, y=0, confidence=0.95),
                TokenDetection(entity_id="player2", x=5, y=5, confidence=0.95),
            ],
            confidence=0.95,
        )
        analysis2 = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[
                TokenDetection(entity_id="player1", x=0, y=0, confidence=0.95),
            ],
            confidence=0.95,
        )

        changes = sync_service.detect_changes(analysis1, analysis2)

        # When a token disappears, it's treated as a move to (-1, -1)
        assert len(changes) == 1
        assert changes[0].token_id == "player2"
