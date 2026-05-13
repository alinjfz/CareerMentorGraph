#!/usr/bin/env python3
"""CareerGraph CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from careergraph.config import get_neo4j_config, load_dotenv
from careergraph.fallback_demo import DEMO_PROFILE, DEMO_TARGET
from careergraph.llm import build_graph_plan
from careergraph.neo4j_store import write_graph
from careergraph.queries import build_demo_results, build_neo4j_results
from careergraph.report import write_html_report


def prompt_with_default(label: str, default: str) -> str:
    value = input(f"{label}\n> ").strip()
    return value or default


def run_demo(args: argparse.Namespace) -> int:
    load_dotenv()

    print("CareerGraph demo")
    print("----------------")

    if args.demo_fast:
        profile = args.profile or DEMO_PROFILE
        target = args.target or DEMO_TARGET
    else:
        print("Paste a career profile paragraph. Press Enter on an empty prompt to use the built-in demo.")
        profile = args.profile or prompt_with_default("Career profile", DEMO_PROFILE)
        target = args.target or prompt_with_default("Target career", DEMO_TARGET)

    print("\nExtracting learner profile...")
    graph_plan = build_graph_plan(
        profile=profile,
        target_career=target,
        use_llm=args.use_llm,
        model=args.model,
    )

    print("Writing graph data..." if args.write_neo4j else "Preparing graph data...")
    store_result = write_graph(graph_plan, enabled=args.write_neo4j)

    print("Running career queries...")
    neo4j_config = get_neo4j_config() if args.query_neo4j else None
    if args.query_neo4j and neo4j_config is not None:
        query_results = build_neo4j_results(graph_plan, neo4j_config)
    else:
        query_results = build_demo_results(graph_plan)

    print("Generating HTML career map...")
    report_path = write_html_report(graph_plan, query_results, output_path=args.output)

    print("\nKnown evidence:")
    for evidence in graph_plan.known_evidence:
        skills = ", ".join(evidence.proves_skills)
        print(f"- {evidence.description} -> {skills}")

    print("\nMissing skills:")
    for skill in graph_plan.missing_skills:
        print(f"- {skill}")

    print(f"\nNext best skill: {query_results.next_best_skill}")
    print(f"Best portfolio project: {query_results.best_project.name}")
    print(f"Why: {' -> '.join(query_results.shortest_path)}")
    print(f"Mentor persona: {query_results.help_persona}")
    print(f"\nGraph storage: {store_result.message}")
    print(f"Report generated: {report_path}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="careergraph",
        description="Build a persistent AI-powered career knowledge graph.",
    )
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="Run the CareerGraph MVP demo.")
    demo_parser.add_argument("--profile", help="Career profile paragraph. Skips the prompt.")
    demo_parser.add_argument("--target", help="Target career. Skips the prompt.")
    demo_parser.add_argument("--demo-fast", action="store_true", help="Run with built-in demo inputs.")
    demo_parser.add_argument("--use-llm", action="store_true", help="Use OpenAI extraction when OPENAI_API_KEY is set.")
    demo_parser.add_argument("--model", help="OpenAI model for --use-llm.")
    demo_parser.add_argument("--write-neo4j", action="store_true", help="Persist graph data to Neo4j.")
    demo_parser.add_argument("--query-neo4j", action="store_true", help="Run headline queries against Neo4j.")
    demo_parser.add_argument(
        "--output",
        type=Path,
        default=Path("out/career_map.html"),
        help="HTML report path.",
    )
    demo_parser.set_defaults(func=run_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 2

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
