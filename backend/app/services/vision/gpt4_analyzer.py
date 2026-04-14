"""GPT-4o Vision board analyzer — sends board images to OpenAI for grid analysis."""
import json
import base64
from app.services.vision.analyzer import BoardAnalyzer, BoardAnalysis, TokenDetection


class GPT4VisionAnalyzer(BoardAnalyzer):
    """Uses OpenAI GPT-4o vision to analyze a physical D&D board photo."""

    SYSTEM_PROMPT = """You are analyzing a photograph of a physical D&D battle map / game board taken from overhead.
Your job is to identify:
1. The grid dimensions (width x height in squares)
2. The positions of miniatures/tokens on the board
3. Any notable terrain features

Return ONLY valid JSON in this exact format:
{
  "grid_width": 10,
  "grid_height": 10,
  "tokens": [
    {"entity_id": "token_1", "x": 3, "y": 5, "label": "fighter miniature", "confidence": 0.9},
    {"entity_id": "token_2", "x": 7, "y": 2, "label": "goblin miniature", "confidence": 0.85}
  ],
  "description": "A stone dungeon corridor with two miniatures visible..."
}

Rules:
- Grid coordinates start at (0,0) top-left
- entity_id should be "token_1", "token_2", etc.
- label should describe what the miniature looks like
- confidence is 0.0-1.0 for how sure you are about the position
- If you can't see a clear grid, estimate based on the board size"""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import httpx
                self._client = httpx.AsyncClient(
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30,
                )
            except ImportError as exc:
                raise ImportError("httpx required: pip install httpx") from exc
        return self._client

    async def analyze(self, image_bytes: bytes) -> BoardAnalysis:
        """Send board image to GPT-4o and parse the grid analysis."""
        client = self._get_client()

        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this D&D board photo. Return JSON only."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                "max_tokens": 1000,
                "temperature": 0.1,
            },
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        parsed = json.loads(content)

        tokens = [
            TokenDetection(
                entity_id=t.get("entity_id", f"token_{i}"),
                x=t.get("x", 0),
                y=t.get("y", 0),
                confidence=t.get("confidence", 0.5),
            )
            for i, t in enumerate(parsed.get("tokens", []))
        ]

        avg_confidence = sum(t.confidence for t in tokens) / max(len(tokens), 1)

        return BoardAnalysis(
            grid_width=parsed.get("grid_width", 10),
            grid_height=parsed.get("grid_height", 10),
            tokens=tokens,
            confidence=avg_confidence,
            raw_description=parsed.get("description", ""),
        )
