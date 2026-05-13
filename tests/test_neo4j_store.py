from __future__ import annotations

import unittest

from careergraph.fallback_demo import build_fallback_demo
from careergraph.neo4j_store import CONSTRAINTS, build_graph_payload, skill_id, write_graph


class Neo4jStoreTests(unittest.TestCase):
    def test_payload_contains_graph_nodes_and_relationships(self) -> None:
        graph_plan = build_fallback_demo()
        payload = build_graph_payload(graph_plan)

        skill_ids = {skill["id"] for skill in payload["skills"]}
        self.assertIn(skill_id("HTTP/API Basics"), skill_ids)
        self.assertEqual(payload["person"]["id"], "person:demo-learner")
        self.assertGreaterEqual(payload["node_count"], 20)
        self.assertGreater(payload["relationship_count"], payload["node_count"])

    def test_prerequisite_to_career_goal_uses_career_id(self) -> None:
        graph_plan = build_fallback_demo()
        payload = build_graph_payload(graph_plan)

        goal_edges = [
            edge
            for edge in payload["prerequisites"]
            if edge["target"]["name"] == "Full-stack Developer"
        ]

        self.assertTrue(goal_edges)
        self.assertTrue(goal_edges[0]["target"]["id"].startswith("career:"))

    def test_write_graph_dry_run_does_not_require_neo4j(self) -> None:
        result = write_graph(build_fallback_demo(), enabled=False)

        self.assertTrue(result.ok)
        self.assertIn("dry run prepared", result.message)

    def test_constraints_cover_core_labels(self) -> None:
        joined = "\n".join(CONSTRAINTS)

        self.assertIn("Person", joined)
        self.assertIn("CareerGoal", joined)
        self.assertIn("HelpPersona", joined)


if __name__ == "__main__":
    unittest.main()
