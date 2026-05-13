from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from careergraph.fallback_demo import build_fallback_demo
from careergraph.queries import build_demo_results
from careergraph.report import render_html_report


class DemoFlowTests(unittest.TestCase):
    def test_fallback_demo_matches_stage_story(self) -> None:
        graph_plan = build_fallback_demo()
        results = build_demo_results(graph_plan)

        self.assertEqual(results.next_best_skill, "HTTP/API Basics")
        self.assertEqual(results.best_project.name, "Task Tracker Web App")
        self.assertEqual(
            results.shortest_path,
            ["HTTP/API Basics", "Backend Routing", "Databases", "Full-stack Developer"],
        )
        self.assertEqual(results.help_persona, "Backend mentor")

    def test_report_contains_core_recommendations(self) -> None:
        graph_plan = build_fallback_demo()
        results = build_demo_results(graph_plan)

        html = render_html_report(graph_plan, results)

        self.assertIn("HTTP/API Basics", html)
        self.assertIn("Task Tracker Web App", html)
        self.assertIn("Backend mentor", html)

    def test_cli_demo_fast_generates_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "career_map.html"
            completed = subprocess.run(
                [
                    sys.executable,
                    "careergraph.py",
                    "demo",
                    "--demo-fast",
                    "--output",
                    str(output),
                ],
                cwd=Path(__file__).resolve().parents[1],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Next best skill: HTTP/API Basics", completed.stdout)
            self.assertTrue(output.exists())
            self.assertIn("Full-stack Developer", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
