"""Síntese opcional e estritamente vinculada às evidências normalizadas."""
from itertools import islice
import json

from pydantic import BaseModel, ConfigDict, Field

from app.prompts.radar import RADAR_SUMMARY_SYSTEM
from app.schemas.radar import ResearchSnapshot, SummaryItem, SummaryResult
from app.services.ai_service import AIService
from app.services.json_helper import loads_json
from app.services.radar_collectors.base import text_excerpt

MAX_EVIDENCE_ITEMS = 40
MAX_RESPONSE_CHARS = 12_000


class SummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[SummaryItem] = Field(max_length=8)


def summary_error() -> SummaryResult:
    return SummaryResult(status="error", detail="Não foi possível gerar a síntese das evidências.")


async def summarize_research(ai: AIService, snapshot: ResearchSnapshot) -> SummaryResult:
    evidence = dict(islice(snapshot.citable_evidence().items(), MAX_EVIDENCE_ITEMS))
    if not evidence:
        return SummaryResult()

    prompt = json.dumps({"evidencias": [
        {
            "id": identifier,
            "rotulo": item.label,
            "trecho": item.data.excerpt,
            "tipo": item.kind,
            "data": item.observed_date.isoformat() if item.observed_date else None,
        }
        for identifier, item in evidence.items()
    ]}, ensure_ascii=False)
    try:
        response = await ai.generate_text(
            prompt=prompt, system_prompt=RADAR_SUMMARY_SYSTEM, max_tokens=1400,
            tools=[], auto_mcp=False, handle_tool_calls=False,
        )
        output = response.get("content")
        if not isinstance(output, str) or len(output) > MAX_RESPONSE_CHARS:
            return summary_error()
        parsed = SummaryOutput.model_validate(loads_json(output))
        items = []
        for item in parsed.items:
            if any(identifier not in evidence for identifier in item.evidence_ids):
                return summary_error()
            items.append(SummaryItem(
                text=text_excerpt(item.text), evidence_ids=list(dict.fromkeys(item.evidence_ids)),
            ))
        return SummaryResult(status="ok", items=items)
    except Exception:
        return summary_error()
