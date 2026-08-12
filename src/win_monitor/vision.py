from __future__ import annotations

import base64
import json
from typing import Any

from anthropic import Anthropic

from win_monitor.models import AnalysisResult
from win_monitor.prompt import PROMPT_ESTRATEGIA


class VisionAnalysisError(RuntimeError):
    pass


class AnthropicVisionAnalyzer:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def analyze(self, image_bytes: bytes) -> AnalysisResult:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = self.client.messages.create(model=self.model, max_tokens=1000, messages=[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":"image/png","data":image_b64}},{"type":"text","text":PROMPT_ESTRATEGIA}]}])
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
        return AnalysisResult.from_mapping(parse_json_response(text))


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                payload = json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError as nested_exc:
                raise VisionAnalysisError(f"Resposta do modelo nao contem JSON valido: {cleaned[:220]}") from nested_exc
        else:
            raise VisionAnalysisError(f"Resposta do modelo nao contem JSON valido: {cleaned[:220]}") from exc
    if not isinstance(payload, dict):
        raise VisionAnalysisError("Resposta JSON deve ser um objeto")
    return payload
