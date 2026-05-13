from __future__ import annotations

import unittest

from careergraph.fallback_demo import build_fallback_demo
from careergraph.queries import (
    BEST_PROJECT_QUERY,
    BEST_RESOURCE_QUERY,
    HELP_PERSONA_QUERY,
    SHORTEST_CAREER_PATH_QUERY,
    find_best_project,
    find_best_resources,
    find_shortest_path,
    select_help_persona,
)


class QueryTests(unittest.TestCase):
    def test_in_memory_queries_match_expected_answers(self) -> None:
        graph_plan = build_fallback_demo()

        self.assertEqual(
            find_shortest_path(
                [graph_plan.next_best_skill],
                graph_plan.target_career,
                graph_plan.prerequisites,
            ),
            ["HTTP/API Basics", "Backend Routing", "Databases", "Full-stack Developer"],
        )
        self.assertEqual(find_best_project(graph_plan).name, "Task Tracker Web App")
        self.assertEqual(find_best_resources(graph_plan)[0].title, "HTTP and APIs for Beginners")
        self.assertEqual(select_help_persona(graph_plan).name, "Backend mentor")

    def test_cypher_queries_include_sponsor_visible_questions(self) -> None:
        self.assertIn("PREREQUISITE_OF", SHORTEST_CAREER_PATH_QUERY)
        self.assertIn("PROVES", BEST_PROJECT_QUERY)
        self.assertIn("TEACHES", BEST_RESOURCE_QUERY)
        self.assertIn("CAN_HELP_WITH", HELP_PERSONA_QUERY)


if __name__ == "__main__":
    unittest.main()
