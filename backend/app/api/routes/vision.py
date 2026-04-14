"""Vision API routes for board image capture and analysis."""
from fastapi import APIRouter, HTTPException, File, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.services.vision.capture import FakeCamera
from app.services.vision.analyzer import FakeBoardAnalyzer, BoardAnalyzer
from app.services.vision.sync import VisionStateSync
from app.api import storage

router = APIRouter()

# Create instances — will use GPT-4o when API key is configured
fake_camera = FakeCamera()
fake_analyzer = FakeBoardAnalyzer()
vision_sync = VisionStateSync()


def _get_analyzer(app_state=None) -> BoardAnalyzer:
    """Get the best available analyzer (GPT-4o if API key set, else fake)."""
    if app_state and hasattr(app_state, "vision_analyzer") and app_state.vision_analyzer is not None:
        return app_state.vision_analyzer
    return fake_analyzer


def _serialize_analysis(analysis):
    """Serialize a BoardAnalysis to dict."""
    return {
        "grid_width": analysis.grid_width,
        "grid_height": analysis.grid_height,
        "tokens": [
            {"entity_id": t.entity_id, "x": t.x, "y": t.y, "confidence": t.confidence}
            for t in analysis.tokens
        ],
        "confidence": analysis.confidence,
        "raw_description": analysis.raw_description,
    }


@router.post("/vision/{session_id}/capture")
async def capture_board(session_id: str, request: Request) -> JSONResponse:
    """Trigger camera capture and board analysis."""
    capture_result = await fake_camera.capture()
    analyzer = _get_analyzer(request.app.state)
    analysis = await analyzer.analyze(capture_result.image_bytes)

    result = _serialize_analysis(analysis)
    storage.vision_analyses[session_id] = result
    return JSONResponse(status_code=200, content=result)


@router.post("/vision/{session_id}/upload")
async def upload_board_image(session_id: str, request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """Upload a board image, analyze it with GPT-4o vision, return grid positions."""
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    image_bytes = await file.read()
    analyzer = _get_analyzer(request.app.state)
    analysis = await analyzer.analyze(image_bytes)

    result = _serialize_analysis(analysis)
    storage.vision_analyses[session_id] = result

    # Broadcast token positions via WebSocket if available
    from app.api.websockets.game_ws import manager
    await manager.broadcast(session_id, {
        "type": "vision_update",
        "tokens": result["tokens"],
        "grid_width": result["grid_width"],
        "grid_height": result["grid_height"],
    })

    return JSONResponse(status_code=200, content=result)


@router.get("/vision/{session_id}/latest")
async def get_latest_analysis(session_id: str) -> JSONResponse:
    """
    Get the latest vision analysis result for a session.

    Args:
        session_id: Session identifier

    Returns:
        JSONResponse with latest analysis or 404 if not found

    Raises:
        HTTPException: If no analysis found for session
    """
    if session_id not in storage.vision_analyses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analysis found for session")

    analysis = storage.vision_analyses[session_id]

    return JSONResponse(status_code=200, content=analysis)
