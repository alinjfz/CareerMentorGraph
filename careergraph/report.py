"""HTML report generation for the CareerGraph MVP."""

from __future__ import annotations

from html import escape
from pathlib import Path

from careergraph.schema import CareerGraphPlan, DemoQueryResults

OUT_DIR = Path("out")


def write_html_report(
    graph_plan: CareerGraphPlan,
    results: DemoQueryResults,
    output_path: Path | None = None,
) -> Path:
    report_path = output_path or OUT_DIR / "career_map.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_html_report(graph_plan, results), encoding="utf-8")
    return report_path


def render_html_report(graph_plan: CareerGraphPlan, results: DemoQueryResults) -> str:
    evidence_items = "\n".join(
        f"<li><strong>{escape(evidence.description)}</strong><span>{escape(', '.join(evidence.proves_skills))}</span></li>"
        for evidence in graph_plan.known_evidence
    )
    missing_items = "\n".join(f"<li>{escape(skill)}</li>" for skill in graph_plan.missing_skills)
    resource_items = "\n".join(render_resource_item(resource) for resource in results.best_resources)
    proven_items = "\n".join(f"<li>{escape(skill)}</li>" for skill in results.proven_skills)

    path = " -> ".join(results.shortest_path)
    best_project_skills = ", ".join(results.best_project.proves_skills)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CareerGraph Map</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18202a;
      --muted: #607083;
      --line: #d8e0ea;
      --paper: #f6f8fb;
      --panel: #ffffff;
      --accent: #0f766e;
      --accent-soft: #d9f2ee;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}

    main {{
      width: min(1040px, calc(100% - 32px));
      margin: 0 auto;
      padding: 40px 0;
    }}

    header {{
      margin-bottom: 28px;
    }}

    h1, h2, p {{
      margin: 0;
    }}

    h1 {{
      font-size: 40px;
      line-height: 1.05;
      letter-spacing: 0;
    }}

    h2 {{
      font-size: 18px;
      margin-bottom: 14px;
    }}

    .subhead {{
      color: var(--muted);
      font-size: 17px;
      margin-top: 10px;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}

    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
    }}

    .wide {{
      grid-column: 1 / -1;
    }}

    ul {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 10px;
    }}

    li {{
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }}

    li:first-child {{
      border-top: 0;
      padding-top: 0;
    }}

    li span {{
      display: block;
      color: var(--muted);
      margin-top: 2px;
    }}

    .path {{
      background: var(--accent-soft);
      border: 1px solid #9fd8d0;
      border-radius: 8px;
      color: #104f49;
      font-weight: 700;
      padding: 14px;
      overflow-wrap: anywhere;
    }}

    .metric {{
      color: var(--accent);
      font-size: 28px;
      font-weight: 800;
      line-height: 1.15;
    }}

    .muted {{
      color: var(--muted);
      margin-top: 8px;
    }}

    @media (max-width: 760px) {{
      main {{
        width: min(100% - 24px, 1040px);
        padding: 28px 0;
      }}

      h1 {{
        font-size: 32px;
      }}

      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{escape(graph_plan.person_name)}'s CareerGraph</h1>
      <p class="subhead">Target career: {escape(graph_plan.target_career)}</p>
    </header>

    <section class="grid">
      <article class="card">
        <h2>Next Best Skill</h2>
        <p class="metric">{escape(results.next_best_skill)}</p>
        <p class="muted">Source: {escape(graph_plan.source)}</p>
      </article>

      <article class="card">
        <h2>Mentor Persona</h2>
        <p class="metric">{escape(results.help_persona)}</p>
        <p class="muted">Best fit for the current blocker skill.</p>
      </article>

      <article class="card wide">
        <h2>Shortest Career Path</h2>
        <p class="path">{escape(path)}</p>
        <p class="muted">Graph path: selected prerequisite chain from blocker skill to target career.</p>
      </article>

      <article class="card">
        <h2>Known Evidence</h2>
        <ul>{evidence_items}</ul>
      </article>

      <article class="card">
        <h2>Proven Skills</h2>
        <ul>{proven_items}</ul>
      </article>

      <article class="card">
        <h2>Missing Skills</h2>
        <ul>{missing_items}</ul>
      </article>

      <article class="card">
        <h2>Best Portfolio Project</h2>
        <p class="metric">{escape(results.best_project.name)}</p>
        <p class="muted">{escape(results.best_project.description)}</p>
        <p class="muted">Proves: {escape(best_project_skills)}</p>
      </article>

      <article class="card wide">
        <h2>Suggested Resources</h2>
        <ul>{resource_items}</ul>
      </article>
    </section>
  </main>
</body>
</html>
"""


def render_resource_item(resource) -> str:
    url = f"<span>{escape(resource.url)}</span>" if resource.url else ""
    return (
        f"<li><strong>{escape(resource.title)}</strong>"
        f"<span>{escape(resource.type)} - teaches {escape(', '.join(resource.teaches_skills))}</span>"
        f"{url}</li>"
    )
