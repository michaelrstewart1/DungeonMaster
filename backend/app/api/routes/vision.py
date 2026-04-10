"""Vision API routes for board image capture and analysis."""
from fastapi import APIRouter, HTTPException, File, UploadFile, status
from fastapi.responses import JSONResponse

from app.services.vision.capture import FakeCamera
from app.services.vision.analyzer import FakeBoardAnalyzer
from app.api import storage

router = APIRouter()

# Create fake instances for testing
fake_camera = FakeCamera()
fake_analyzer = FakeBoardAnalyzer()


@router.post("/vision/{session_id}/capture")
async def capture_board(session_id: str) -> JSONResponse:
    """
    Trigger camera capture and board analysis.

    Returns analyzed grid positions as JSON.

    Args:
        session_id: Session identifier

    Returns:
        JSONResponse with analyzed board data
    """
    # Capture image from camera
    capture_result = await fake_camera.capture()

    # Analyze the board
    analysis = await fake_analyzer.analyze(capture_result.image_bytes)

    # Store the analysis in memory
    storage.vision_analyses[session_id] = {
        "grid_width": analysis.grid_width,
        "grid_height": analysis.grid_height,
        "tokens": [
            {"entity_id": token.entity_id, "x": token.x, "y": token.y, "confidence": token.confidence}
            for token in analysis.tokens
        ],
        "confidence": analysis.confidence,
        "raw_description": analysis.raw_description,
    }

    # Return the analysis
    return JSONResponse(
        status_code=200,
        content={
            "grid_width": analysis.grid_width,
            "grid_height": analysis.grid_height,
            "tokens": [
                {"entity_id": token.entity_id, "x": token.x, "y": token.y, "confidence": token.confidence}
                for token in analysis.tokens
            ],
            "confidence": analysis.confidence,
            "raw_description": analysis.raw_description,
        },
    )


@router.post("/vision/{session_id}/upload")
async def upload_board_image(session_id: str, file: UploadFile = File(...)) -> JSONResponse:
    """
    Upload a board image, analyze it, return grid positions.

    Args:
        session_id: Session identifier
        file: Image file to upload

    Returns:
        JSONResponse with analyzed board data

    Raises:
        HTTPException: If no file is provided
    """
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    # Read the uploaded file
    image_bytes = await file.read()

    # Analyze the board
    analysis = await fake_analyzer.analyze(image_bytes)

    # Store the analysis in memory
    storage.vision_analyses[session_id] = {
        "grid_width": analysis.grid_width,
        "grid_height": analysis.grid_height,
        "tokens": [
            {"entity_id": token.entity_id, "x": token.x, "y": token.y, "confidence": token.confidence}
            for token in analysis.tokens
        ],
        "confidence": analysis.confidence,
        "raw_description": analysis.raw_description,
    }

    # Return the analysis
    return JSONResponse(
        status_code=200,
        content={
            "grid_width": analysis.grid_width,
            "grid_height": analysis.grid_height,
            "tokens": [
                {"entity_id": token.entity_id, "x": token.x, "y": token.y, "confidence": token.confidence}
                for token in analysis.tokens
            ],
            "confidence": analysis.confidence,
            "raw_description": analysis.raw_description,
        },
    )


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
