"""OpenAI provider — the ONLY external API used.

research()  -> Responses API + web_search tool (real sources). Degrades to a
               plain text generation if web search is unavailable.
structure() -> Chat Completions JSON mode for the exact-schema object.
"""
from __future__ import annotations

import json
import re
from typing import List, Tuple

from .config import settings


class OpenAIError(RuntimeError):
    pass


def extract_json(text: str) -> dict:
    if not text:
        raise OpenAIError("Empty model response.")
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise OpenAIError("No JSON object found in response.")
        candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        cleaned = re.sub(r",(\s*[}\]])", r"\1", candidate)
        return json.loads(cleaned)


class OpenAIProvider:
    def __init__(self) -> None:
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.openai_api_key)

    # ---------------- Research (web search) --------------------------
    @staticmethod
    def _citations_from_response(resp) -> List[str]:
        urls: List[str] = []
        try:
            for item in getattr(resp, "output", []) or []:
                if getattr(item, "type", None) != "message":
                    continue
                for block in getattr(item, "content", []) or []:
                    for ann in getattr(block, "annotations", []) or []:
                        url = getattr(ann, "url", None)
                        if url and url not in urls:
                            urls.append(url)
        except Exception:  # noqa: BLE001 — never fail on citation parsing
            pass
        return urls

    def research(self, system: str, user: str) -> Tuple[str, List[str]]:
        if not settings.enable_web_search:
            text = self._plain_research(system, user)
            return text, []

        instructions = system
        prompt = user
        for tool_name in (settings.web_search_tool, "web_search_preview"):
            try:
                resp = self.client.responses.create(
                    model=settings.openai_research_model,
                    instructions=instructions,
                    input=prompt,
                    tools=[{"type": tool_name}],
                    max_output_tokens=settings.research_max_tokens,
                )
                text = getattr(resp, "output_text", "") or ""
                return text, self._citations_from_response(resp)
            except Exception:  # noqa: BLE001 — try next tool name / fallback
                continue
        # Last resort: no browsing.
        return self._plain_research(system, user), []

    def _plain_research(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=settings.openai_research_model,
            max_tokens=settings.research_max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",
                 "content": user + "\n\n(No web access — give best-effort, "
                                   "clearly-labelled estimates.)"},
            ],
        )
        return resp.choices[0].message.content or ""

    # ---------------- Structure (JSON mode) --------------------------
    def structure(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=settings.structure_max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""


_provider: OpenAIProvider | None = None


def get_provider() -> OpenAIProvider:
    global _provider
    if _provider is None:
        if not settings.has_openai:
            raise OpenAIError("OPENAI_API_KEY is not configured.")
        _provider = OpenAIProvider()
    return _provider
