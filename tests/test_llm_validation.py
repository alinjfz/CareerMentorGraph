from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from careergraph.config import LLMConfig
from careergraph.llm import build_graph_plan, build_graph_plan_with_openai
from careergraph.validation import GraphPlanValidationError, graph_plan_from_payload


def valid_payload() -> dict:
    return {
        "person": {"name": "Demo Learner", "targetCareer": "Full-stack Developer"},
        "knownEvidence": [
            {"description": "Built small scripts", "provesSkills": ["Python Basics"]},
            {"description": "Built a static portfolio page", "provesSkills": ["HTML", "CSS"]},
        ],
        "missingSkills": ["HTTP/API Basics", "Backend Routing"],
        "careerRequires": ["HTML", "CSS", "HTTP/API Basics", "Backend Routing"],
        "prerequisites": [["HTTP/API Basics", "Backend Routing"], ["Backend Routing", "Full-stack Developer"]],
        "projects": [
            {
                "name": "Task Tracker Web App",
                "description": "A CRUD app with login and storage.",
                "provesSkills": ["Backend Routing"],
            }
        ],
        "resources": [
            {
                "title": "HTTP and APIs for Beginners",
                "type": "interactive guide",
                "url": "https://example.com/http",
                "teachesSkills": ["HTTP/API Basics"],
            }
        ],
        "helpPersonas": [
            {"name": "Backend mentor", "canHelpWith": ["HTTP/API Basics", "Backend Routing"]}
        ],
        "nextBestSkill": "HTTP/API Basics",
        "helpPersona": "Backend mentor",
    }


class LLMValidationTests(unittest.TestCase):
    def test_graph_plan_from_payload_normalizes_json(self) -> None:
        graph_plan = graph_plan_from_payload(valid_payload(), fallback_target="Full-stack Developer")

        self.assertEqual(graph_plan.source, "llm")
        self.assertEqual(graph_plan.projects[0].id, "project:task-tracker-web-app")
        self.assertEqual(graph_plan.resources[0].url, "https://example.com/http")

    def test_validation_rejects_next_skill_outside_missing_skills(self) -> None:
        payload = valid_payload()
        payload["nextBestSkill"] = "React"

        with self.assertRaises(GraphPlanValidationError):
            graph_plan_from_payload(payload, fallback_target="Full-stack Developer")

    def test_openai_extraction_retries_invalid_json_once(self) -> None:
        config = LLMConfig(api_key="test-key", model="test-model")

        with patch(
            "careergraph.llm.call_openai_responses",
            side_effect=[
                {"output_text": "{not json"},
                {"output_text": json.dumps(valid_payload())},
            ],
        ) as call:
            graph_plan = build_graph_plan_with_openai(
                profile="I know HTML.",
                target_career="Full-stack Developer",
                config=config,
            )

        self.assertEqual(call.call_count, 2)
        self.assertEqual(graph_plan.next_best_skill, "HTTP/API Basics")

    def test_build_graph_plan_without_api_key_falls_back(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            graph_plan = build_graph_plan(
                profile="I know HTML.",
                target_career="Full-stack Developer",
                use_llm=True,
            )

        self.assertEqual(graph_plan.source, "fallback_demo:no_openai_key")


if __name__ == "__main__":
    unittest.main()
