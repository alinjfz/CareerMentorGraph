"""LLM extraction boundary for CareerGraph."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import replace
from typing import Any

from careergraph.config import LLMConfig, get_llm_config
from careergraph.fallback_demo import build_fallback_demo
from careergraph.schema import CareerGraphPlan
from careergraph.validation import GraphPlanValidationError, graph_plan_from_payload


SYSTEM_PROMPT = """You are careergraph-mentor.
Return JSON only. Convert messy learner text into a graph-safe career plan.
Prefer concrete evidence over vague self-claims. Recommend prerequisite-aware
steps and justify recommendations through skills, projects, resources, and
mentor personas. Do not include markdown."""

LLM_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "person": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "targetCareer": {"type": "string"},
            },
            "required": ["name", "targetCareer"],
        },
        "knownEvidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "description": {"type": "string"},
                    "provesSkills": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["description", "provesSkills"],
            },
        },
        "missingSkills": {"type": "array", "items": {"type": "string"}},
        "careerRequires": {"type": "array", "items": {"type": "string"}},
        "prerequisites": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "provesSkills": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "description", "provesSkills"],
            },
        },
        "resources": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "type": {"type": "string"},
                    "url": {"type": "string"},
                    "teachesSkills": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "type", "url", "teachesSkills"],
            },
        },
        "helpPersonas": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "canHelpWith": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "canHelpWith"],
            },
        },
        "nextBestSkill": {"type": "string"},
        "helpPersona": {"type": "string"},
    },
    "required": [
        "person",
        "knownEvidence",
        "missingSkills",
        "careerRequires",
        "prerequisites",
        "projects",
        "resources",
        "helpPersonas",
        "nextBestSkill",
        "helpPersona",
    ],
}


def build_graph_plan(
    profile: str,
    target_career: str,
    use_llm: bool = False,
    model: str | None = None,
) -> CareerGraphPlan:
    if not use_llm:
        return build_fallback_demo(profile=profile, target_career=target_career)

    config = get_llm_config(model_override=model)
    if config is None:
        fallback = build_fallback_demo(profile=profile, target_career=target_career)
        return replace_source(fallback, "fallback_demo:no_openai_key")

    try:
        return build_graph_plan_with_openai(profile, target_career, config)
    except (GraphPlanValidationError, OpenAIExtractionError, json.JSONDecodeError):
        fallback = build_fallback_demo(profile=profile, target_career=target_career)
        return replace_source(fallback, "fallback_demo:llm_failed")


class OpenAIExtractionError(RuntimeError):
    """Raised when the OpenAI API response cannot be read."""


def build_graph_plan_with_openai(
    profile: str,
    target_career: str,
    config: LLMConfig,
) -> CareerGraphPlan:
    user_prompt = build_user_prompt(profile, target_career)
    last_error: Exception | None = None

    for attempt in range(2):
        prompt = user_prompt
        if attempt == 1 and last_error is not None:
            prompt = (
                f"{user_prompt}\n\nThe previous response failed validation with: {last_error}. "
                "Return corrected JSON matching the schema exactly."
            )

        payload = call_openai_responses(prompt=prompt, config=config)
        try:
            raw_json = extract_output_text(payload)
            return graph_plan_from_payload(json.loads(raw_json), fallback_target=target_career)
        except (GraphPlanValidationError, json.JSONDecodeError) as exc:
            last_error = exc

    assert last_error is not None
    raise last_error


def build_user_prompt(profile: str, target_career: str) -> str:
    return (
        "Create a CareerGraph plan from this learner profile.\n\n"
        f"Target career: {target_career}\n\n"
        f"Learner profile: {profile}\n\n"
        "Return concrete evidence, missing skills, prerequisite links, portfolio projects, "
        "resources, and help personas. Use JSON only."
    )


def call_openai_responses(prompt: str, config: LLMConfig) -> dict[str, Any]:
    request_body = {
        "model": config.model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "career_graph_plan",
                "strict": True,
                "schema": LLM_JSON_SCHEMA,
            }
        },
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise OpenAIExtractionError(str(exc)) from exc


def extract_output_text(response_payload: dict[str, Any]) -> str:
    output_text = response_payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for output_item in response_payload.get("output", []):
        for content in output_item.get("content", []):
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text

    raise OpenAIExtractionError("OpenAI response did not contain output text")


def replace_source(graph_plan: CareerGraphPlan, source: str) -> CareerGraphPlan:
    return replace(graph_plan, source=source)
