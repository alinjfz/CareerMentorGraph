"""HTML report generation for the CareerGraph MVP."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from careergraph.schema import CareerGraphPlan, DemoQueryResults
from careergraph.schema import slugify

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
    graph_json = render_graph_json(graph_plan, results)
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
      --graph-bg: #101418;
      --graph-line: rgba(166, 190, 214, 0.26);
      --graph-text: #eff6ff;
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

    .graph-card {{
      background: var(--graph-bg);
      border-color: #242d36;
      color: var(--graph-text);
      padding: 0;
      overflow: hidden;
    }}

    .graph-head {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 20px;
      border-bottom: 1px solid #242d36;
      align-items: start;
    }}

    .graph-head p {{
      color: #aab8c8;
      margin-top: 4px;
    }}

    .graph-legend {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
      min-width: 220px;
    }}

    .legend-item {{
      align-items: center;
      color: #cbd6e2;
      display: inline-flex;
      font-size: 12px;
      gap: 6px;
      white-space: nowrap;
    }}

    .legend-dot {{
      border-radius: 999px;
      display: inline-block;
      height: 9px;
      width: 9px;
    }}

    .graph-wrap {{
      height: min(620px, 72vh);
      min-height: 430px;
      position: relative;
    }}

    #career-graph {{
      display: block;
      height: 100%;
      width: 100%;
    }}

    .graph-tooltip {{
      background: rgba(18, 24, 31, 0.94);
      border: 1px solid #324052;
      border-radius: 8px;
      color: #f8fbff;
      font-size: 13px;
      left: 16px;
      max-width: 280px;
      opacity: 0;
      padding: 10px 12px;
      pointer-events: none;
      position: absolute;
      top: 16px;
      transform: translateY(4px);
      transition: opacity 120ms ease, transform 120ms ease;
    }}

    .graph-tooltip strong {{
      display: block;
      margin-bottom: 2px;
    }}

    .graph-tooltip.visible {{
      opacity: 1;
      transform: translateY(0);
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

      .graph-head {{
        display: block;
      }}

      .graph-legend {{
        justify-content: flex-start;
        margin-top: 14px;
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
      <article class="card wide graph-card">
        <div class="graph-head">
          <div>
            <h2>Career Knowledge Graph</h2>
            <p>Evidence, skills, resources, projects, and mentor help connected as a career map.</p>
          </div>
          <div class="graph-legend" aria-label="Graph legend">
            <span class="legend-item"><span class="legend-dot" style="background:#f7c948"></span>Person</span>
            <span class="legend-item"><span class="legend-dot" style="background:#60a5fa"></span>Skill</span>
            <span class="legend-item"><span class="legend-dot" style="background:#34d399"></span>Project</span>
            <span class="legend-item"><span class="legend-dot" style="background:#f472b6"></span>Resource</span>
            <span class="legend-item"><span class="legend-dot" style="background:#a78bfa"></span>Goal</span>
          </div>
        </div>
        <div class="graph-wrap">
          <canvas id="career-graph" aria-label="CareerGraph visual map"></canvas>
          <div id="graph-tooltip" class="graph-tooltip"></div>
        </div>
      </article>

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
  <script id="career-graph-data" type="application/json">{graph_json}</script>
  <script>
{GRAPH_SCRIPT}
  </script>
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


def render_graph_json(graph_plan: CareerGraphPlan, results: DemoQueryResults) -> str:
    data = build_graph_data(graph_plan, results)
    return json.dumps(data).replace("<", "\\u003c")


def build_graph_data(graph_plan: CareerGraphPlan, results: DemoQueryResults) -> dict:
    nodes: dict[str, dict] = {}
    links: list[dict] = []

    def add_node(node_id: str, label: str, group: str, detail: str = "") -> None:
        nodes.setdefault(
            node_id,
            {
                "id": node_id,
                "label": label,
                "group": group,
                "detail": detail,
            },
        )

    def add_link(source: str, target: str, label: str) -> None:
        links.append({"source": source, "target": target, "label": label})

    person_id = "person:demo-learner"
    goal_id = f"career:{slugify(graph_plan.target_career)}"
    add_node(person_id, graph_plan.person_name, "person", "Learner profile")
    add_node(goal_id, graph_plan.target_career, "goal", "Target career")
    add_link(person_id, goal_id, "targets")

    skill_names = []
    for name in [
        *graph_plan.career_requires,
        *graph_plan.missing_skills,
        *results.proven_skills,
        *[skill for project in graph_plan.projects for skill in project.proves_skills],
        *[skill for resource in graph_plan.resources for skill in resource.teaches_skills],
    ]:
        if name not in skill_names:
            skill_names.append(name)

    for skill in skill_names:
        skill_node = f"skill:{slugify(skill)}"
        status = []
        if skill in results.proven_skills:
            status.append("proven")
        if skill in graph_plan.missing_skills:
            status.append("missing")
        add_node(skill_node, skill, "skill", ", ".join(status) or "career skill")
        if skill in graph_plan.career_requires:
            add_link(goal_id, skill_node, "requires")
        if skill in graph_plan.missing_skills:
            add_link(person_id, skill_node, "missing")

    for source, target in graph_plan.prerequisites:
        source_id = f"skill:{slugify(source)}"
        target_id = goal_id if target == graph_plan.target_career else f"skill:{slugify(target)}"
        add_node(source_id, source, "skill", "prerequisite")
        if target_id not in nodes:
            add_node(target_id, target, "skill", "unlocked skill")
        add_link(source_id, target_id, "prerequisite")

    for evidence in graph_plan.known_evidence:
        add_node(evidence.id, evidence.description, "evidence", "Known evidence")
        add_link(person_id, evidence.id, "has evidence")
        for skill in evidence.proves_skills:
            add_link(evidence.id, f"skill:{slugify(skill)}", "proves")

    for project in graph_plan.projects:
        group = "project"
        detail = project.description
        add_node(project.id, project.name, group, detail)
        for skill in project.proves_skills:
            add_link(project.id, f"skill:{slugify(skill)}", "proves")

    for resource in graph_plan.resources:
        add_node(resource.id, resource.title, "resource", resource.type)
        for skill in resource.teaches_skills:
            add_link(resource.id, f"skill:{slugify(skill)}", "teaches")

    for persona in graph_plan.help_personas:
        add_node(persona.id, persona.name, "persona", "Help persona")
        for skill in persona.can_help_with:
            skill_id = f"skill:{slugify(skill)}"
            if skill_id in nodes:
                add_link(persona.id, skill_id, "can help")

    return {"nodes": list(nodes.values()), "links": links}


GRAPH_SCRIPT = """
(() => {
  const canvas = document.getElementById("career-graph");
  const tooltip = document.getElementById("graph-tooltip");
  const raw = document.getElementById("career-graph-data").textContent;
  const graph = JSON.parse(raw);
  const ctx = canvas.getContext("2d");
  const colors = {
    person: "#f7c948",
    goal: "#a78bfa",
    skill: "#60a5fa",
    evidence: "#fb7185",
    project: "#34d399",
    resource: "#f472b6",
    persona: "#f59e0b"
  };
  const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));
  let width = 0;
  let height = 0;
  let hovered = null;
  let dragging = null;

  function resize() {
    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    canvas.width = Math.max(1, Math.floor(width * ratio));
    canvas.height = Math.max(1, Math.floor(height * ratio));
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    seedNodes();
  }

  function seedNodes() {
    const radius = Math.min(width, height) * 0.34;
    graph.nodes.forEach((node, index) => {
      if (typeof node.x === "number") {
        return;
      }
      const angle = (index / Math.max(1, graph.nodes.length)) * Math.PI * 2;
      node.x = width / 2 + Math.cos(angle) * radius;
      node.y = height / 2 + Math.sin(angle) * radius;
      node.vx = 0;
      node.vy = 0;
    });
  }

  function tick() {
    const centerForce = 0.004;
    const linkDistance = 126;
    const linkForce = 0.018;
    const charge = 2600;

    graph.nodes.forEach((node) => {
      node.vx += (width / 2 - node.x) * centerForce;
      node.vy += (height / 2 - node.y) * centerForce;
    });

    for (let i = 0; i < graph.nodes.length; i += 1) {
      for (let j = i + 1; j < graph.nodes.length; j += 1) {
        const a = graph.nodes[i];
        const b = graph.nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const distanceSquared = Math.max(dx * dx + dy * dy, 80);
        const force = charge / distanceSquared;
        const distance = Math.sqrt(distanceSquared);
        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;
        a.vx -= fx;
        a.vy -= fy;
        b.vx += fx;
        b.vy += fy;
      }
    }

    graph.links.forEach((link) => {
      const source = nodeById.get(link.source);
      const target = nodeById.get(link.target);
      if (!source || !target) {
        return;
      }
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
      const force = (distance - linkDistance) * linkForce;
      const fx = (dx / distance) * force;
      const fy = (dy / distance) * force;
      source.vx += fx;
      source.vy += fy;
      target.vx -= fx;
      target.vy -= fy;
    });

    graph.nodes.forEach((node) => {
      if (node === dragging) {
        node.vx = 0;
        node.vy = 0;
        return;
      }
      node.vx *= 0.72;
      node.vy *= 0.72;
      node.x = Math.max(24, Math.min(width - 24, node.x + node.vx));
      node.y = Math.max(24, Math.min(height - 24, node.y + node.vy));
    });
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    const gradient = ctx.createRadialGradient(width * 0.5, height * 0.5, 20, width * 0.5, height * 0.5, Math.max(width, height) * 0.7);
    gradient.addColorStop(0, "#17202a");
    gradient.addColorStop(1, "#0d1116");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    graph.links.forEach((link) => {
      const source = nodeById.get(link.source);
      const target = nodeById.get(link.target);
      if (!source || !target) {
        return;
      }
      const active = hovered && (hovered.id === source.id || hovered.id === target.id);
      ctx.strokeStyle = active ? "rgba(229, 240, 255, 0.72)" : "rgba(166, 190, 214, 0.24)";
      ctx.lineWidth = active ? 1.8 : 1;
      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.stroke();
    });

    graph.nodes.forEach((node) => {
      const active = node === hovered;
      const radius = nodeRadius(node);
      ctx.shadowColor = colors[node.group] || "#93c5fd";
      ctx.shadowBlur = active ? 24 : 10;
      ctx.fillStyle = colors[node.group] || "#93c5fd";
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.strokeStyle = active ? "#ffffff" : "rgba(255, 255, 255, 0.68)";
      ctx.lineWidth = active ? 2.4 : 1.2;
      ctx.stroke();

      if (active || node.group === "person" || node.group === "goal" || node.group === "project") {
        drawLabel(node, radius);
      }
    });
  }

  function drawLabel(node, radius) {
    ctx.font = node.group === "goal" ? "700 13px system-ui" : "600 12px system-ui";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const label = trimLabel(node.label, node === hovered ? 34 : 22);
    const textWidth = ctx.measureText(label).width;
    const x = Math.max(textWidth / 2 + 8, Math.min(width - textWidth / 2 - 8, node.x));
    const y = Math.min(height - 24, node.y + radius + 8);
    ctx.fillStyle = "rgba(9, 13, 18, 0.76)";
    roundRect(x - textWidth / 2 - 7, y - 3, textWidth + 14, 22, 6);
    ctx.fill();
    ctx.fillStyle = "#eef6ff";
    ctx.fillText(label, x, y);
  }

  function nodeRadius(node) {
    if (node.group === "person") return 10;
    if (node.group === "goal") return 11;
    if (node.group === "project") return 8;
    if (node.group === "resource") return 7;
    return 6;
  }

  function trimLabel(label, max) {
    return label.length > max ? `${label.slice(0, max - 1)}...` : label;
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function nearestNode(event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    let nearest = null;
    let nearestDistance = Infinity;
    graph.nodes.forEach((node) => {
      const dx = node.x - x;
      const dy = node.y - y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      if (distance < nearestDistance && distance < nodeRadius(node) + 12) {
        nearest = node;
        nearestDistance = distance;
      }
    });
    return { node: nearest, x, y };
  }

  function updateHover(event) {
    const hit = nearestNode(event);
    hovered = hit.node;
    canvas.style.cursor = hovered ? "grab" : "default";
    if (hovered) {
      tooltip.innerHTML = `<strong>${escapeHtml(hovered.label)}</strong><span>${escapeHtml(hovered.detail || hovered.group)}</span>`;
      tooltip.style.left = `${Math.min(width - 300, hit.x + 16)}px`;
      tooltip.style.top = `${Math.max(12, hit.y - 10)}px`;
      tooltip.classList.add("visible");
    } else {
      tooltip.classList.remove("visible");
    }
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[char]));
  }

  canvas.addEventListener("mousemove", (event) => {
    if (dragging) {
      const rect = canvas.getBoundingClientRect();
      dragging.x = event.clientX - rect.left;
      dragging.y = event.clientY - rect.top;
      return;
    }
    updateHover(event);
  });

  canvas.addEventListener("mouseleave", () => {
    hovered = null;
    dragging = null;
    tooltip.classList.remove("visible");
  });

  canvas.addEventListener("mousedown", (event) => {
    const hit = nearestNode(event);
    dragging = hit.node;
    if (dragging) {
      canvas.style.cursor = "grabbing";
    }
  });

  window.addEventListener("mouseup", () => {
    dragging = null;
    canvas.style.cursor = hovered ? "grab" : "default";
  });

  function animate() {
    tick();
    draw();
    requestAnimationFrame(animate);
  }

  window.addEventListener("resize", resize);
  resize();
  animate();
})();
"""
