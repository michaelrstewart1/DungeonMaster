"""Avatar State API routes."""
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from app.api import storage
from app.services.avatar.expressions import AvatarState, Expression, ExpressionMapper

router = APIRouter(prefix="/avatar", tags=["avatar"])

# In-memory storage for avatar states
_avatar_states: dict[str, AvatarState] = {}
_speaking_timers: dict[str, datetime] = {}  # Track when speaking ends
_expression_mapper = ExpressionMapper()


def reset() -> None:
    """Reset avatar states (for testing)."""
    _avatar_states.clear()
    _speaking_timers.clear()


def _get_or_create_state(session_id: str) -> AvatarState:
    """Get or create avatar state for a session."""
    if session_id not in _avatar_states:
        _avatar_states[session_id] = AvatarState()
    return _avatar_states[session_id]


def _update_speaking_state() -> None:
    """Update speaking states based on timers."""
    now = datetime.now()
    sessions_to_update = []
    
    for session_id, end_time in _speaking_timers.items():
        if now >= end_time:
            sessions_to_update.append(session_id)
    
    for session_id in sessions_to_update:
        state = _get_or_create_state(session_id)
        state.is_speaking = False
        del _speaking_timers[session_id]


@router.get("/{session_id}")
async def get_avatar_state(session_id: str) -> dict:
    """Get current avatar state.
    
    Returns:
        {
            "expression": str,
            "is_speaking": bool,
            "mouth_amplitude": float,
            "gaze": str
        }
    """
    _update_speaking_state()
    state = _get_or_create_state(session_id)
    return state.to_dict()


@router.put("/{session_id}/expression")
async def set_expression(session_id: str, body: dict) -> dict:
    """Set avatar expression.
    
    Body:
        {
            "expression": str (must be valid Expression value)
        }
    
    Returns:
        Updated avatar state
    """
    expression_str = body.get("expression")
    
    if not expression_str:
        raise HTTPException(status_code=400, detail="expression is required")
    
    # Validate expression
    try:
        expression = Expression(expression_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid expression: {expression_str}"
        )
    
    state = _get_or_create_state(session_id)
    state.expression = expression
    
    return state.to_dict()


@router.post("/{session_id}/speak")
async def speak(session_id: str, body: dict) -> dict:
    """Trigger speaking animation.
    
    Body:
        {
            "text": str,
            "duration": float (seconds, optional, default 2.0)
        }
    
    Returns:
        Updated avatar state
    """
    text = body.get("text", "")
    duration = body.get("duration", 2.0)
    
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    
    state = _get_or_create_state(session_id)
    
    # Try to update expression based on text sentiment
    new_expression = _expression_mapper.from_text_sentiment(text)
    state.expression = new_expression
    
    # Set speaking state and timer
    state.is_speaking = True
    _speaking_timers[session_id] = datetime.now() + timedelta(seconds=float(duration))
    
    # Initialize mouth amplitude
    state.mouth_amplitude = 0.1
    
    return state.to_dict()


@router.get("/{session_id}/state")
async def get_full_state(session_id: str) -> dict:
    """Get full avatar state.
    
    Returns:
        {
            "expression": str,
            "is_speaking": bool,
            "mouth_amplitude": float,
            "gaze": str
        }
    """
    _update_speaking_state()
    state = _get_or_create_state(session_id)
    return state.to_dict()
