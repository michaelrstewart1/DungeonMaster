"""
Game Manager for D&D 5e AI Dungeon Master.

Top-level orchestrator that ties together rules engine, turn manager,
narrative summary, and game state for managing complete game sessions.
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid
from app.services.dice import DiceRoller
from app.services.llm.base import LLMProvider
from app.services.llm.narrator import DMNarrator
from app.services.rules.engine import RulesEngine
from app.services.rules.combat import Combatant
from app.services.game.turns import TurnManager, TurnResult
from app.services.game.summary import NarrativeSummary
from app.services.game.state import GameStateMachine, GamePhase


@dataclass
class GameSession:
    """Represents a single game session."""
    id: str
    players: list[dict]
    enemies: list[Combatant]
    phase: GamePhase
    turn_count: int
    narrative: NarrativeSummary
    state_machine: GameStateMachine = field(default_factory=lambda: GameStateMachine(GamePhase.LOBBY))


class GameManager:
    """Top-level orchestrator for game sessions."""

    def __init__(self, llm_provider: LLMProvider, dice_seed: Optional[int] = None):
        """
        Initialize the GameManager.
        
        Args:
            llm_provider: LLMProvider for narrator
            dice_seed: Optional seed for deterministic dice rolls
        """
        self.llm_provider = llm_provider
        self.dice_seed = dice_seed

        # Create core components
        self.dice_roller = DiceRoller(seed=dice_seed)
        self.rules_engine = RulesEngine(self.dice_roller)
        self.narrator = DMNarrator(llm_provider)

        # Session management
        self._sessions: dict[str, GameSession] = {}

    # Keep state_machine property for backwards compatibility with tests
    @property
    def state_machine(self) -> GameStateMachine:
        """Return a reference to the first active session's state machine, or a dummy one."""
        if self._sessions:
            return list(self._sessions.values())[0].state_machine
        return GameStateMachine(GamePhase.LOBBY)

    def create_session(self, campaign_name: str) -> GameSession:
        """
        Create a new game session.
        
        Args:
            campaign_name: Name of the campaign
            
        Returns:
            New GameSession
        """
        session_id = str(uuid.uuid4())

        session = GameSession(
            id=session_id,
            players=[],
            enemies=[],
            phase=GamePhase.LOBBY,
            turn_count=0,
            narrative=NarrativeSummary(max_entries=50),
            state_machine=GameStateMachine(initial_phase=GamePhase.LOBBY)
        )

        self._sessions[session_id] = session
        return session

    def add_player(self, session_id: str, character: dict) -> None:
        """
        Add a player character to a session.
        
        Args:
            session_id: Session ID
            character: Character data dict
            
        Raises:
            KeyError: If session not found
        """
        session = self._sessions[session_id]
        session.players.append(character)

    def start_combat(self, session_id: str, enemies: list[dict]) -> None:
        """
        Start combat in a session.
        
        Args:
            session_id: Session ID
            enemies: List of enemy data dicts
        """
        session = self._sessions[session_id]

        # Transition to combat phase
        session.state_machine.transition_to(GamePhase.COMBAT)
        session.phase = GamePhase.COMBAT

        # Roll initiative for enemies
        combatant_list = self.rules_engine.start_combat(enemies)
        session.enemies = combatant_list

    def end_combat(self, session_id: str) -> None:
        """
        End combat in a session.
        
        Args:
            session_id: Session ID
        """
        session = self._sessions[session_id]

        # Transition back to exploration
        session.state_machine.transition_to(GamePhase.EXPLORATION)
        session.phase = GamePhase.EXPLORATION

        # Clear enemies
        session.enemies = []

    async def process_action(
        self,
        session_id: str,
        player_id: str,
        action: dict
    ) -> TurnResult:
        """
        Process a player action in a session.
        
        Args:
            session_id: Session ID
            player_id: Player character ID
            action: Action dict
            
        Returns:
            TurnResult with action resolution
        """
        session = self._sessions[session_id]
        session.turn_count += 1

        # Create turn manager for this action
        turn_manager = TurnManager(self.rules_engine, self.narrator)

        # If in combat, set up combatants
        if session.phase == GamePhase.COMBAT:
            # Combine players and enemies into combatant list
            combatants = []

            # Add player characters as combatants
            for player in session.players:
                combatant = Combatant(
                    id=player.get("id", "player-unknown"),
                    name=player.get("name", "Unknown"),
                    initiative=player.get("initiative", 0),
                    initiative_modifier=player.get("initiative_modifier", 0),
                    hp=player.get("hp", 30),
                    max_hp=player.get("max_hp", 30),
                    ac=player.get("ac", 10)
                )
                combatants.append(combatant)

            # Add enemies
            combatants.extend(session.enemies)

            turn_manager.combatants = combatants

        # Process the action
        result = await turn_manager.process_player_action(action)
        result.turn_number = session.turn_count

        # Add to narrative
        session.narrative.add_narration(session.turn_count, result.narration)

        return result

    def get_session_state(self, session_id: str) -> dict:
        """
        Get current state snapshot of a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with session state
        """
        session = self._sessions[session_id]

        state = {
            "id": session.id,
            "phase": session.phase.value,
            "turn_count": session.turn_count,
            "players": session.players,
            "enemies": [
                {
                    "id": e.id,
                    "name": e.name,
                    "hp": e.hp,
                    "max_hp": e.max_hp,
                    "ac": e.ac,
                    "is_alive": e.is_alive
                }
                for e in session.enemies
            ] if session.enemies else [],
            "narrative_recent": session.narrative.get_recent(n=3),
        }

        return state
