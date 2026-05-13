# CareerGraph MentorGraph Plan

## Summary
Build **CareerGraph**, a persistent AI-powered career knowledge base.

A user tells the system about their studies, skills, projects, interests, and target career. The LLM converts that into structured graph data. Neo4j stores the career knowledge base and answers graph-native questions like:

- What skills do I already have evidence for?
- What skills am I missing for my target career?
- Which prerequisite skill blocks the most progress?
- Which project would prove the most missing skills?
- Which resource should I use next?
- What is my shortest path from current evidence to target role?

The demo career will be **Full-stack Developer**, but the product supports any career goal by letting the LLM generate/extend the graph.

## Sponsor Justification
**Neo4j**
Neo4j is the core product, not just storage. It stores a persistent knowledge graph of skills, projects, resources, evidence, and career goals. It powers path queries, prerequisite reasoning, and project/resource recommendations.

**Tessl**
Create a custom `careergraph-mentor` skill. This teaches the AI how to:
- extract career evidence from messy user text,
- generate graph-safe career schemas,
- recommend paths using graph relationships,
- avoid shallow “learn React” advice,
- always justify recommendations with graph paths.

**Codex**
Codex builds the CLI, Cypher, graph schema, Tessl skill, and HTML report.

**Hubble**
Use a simple help persona layer:
- “Ask a senior frontend mentor”
- “Ask a backend mentor”
- “Ask a career coach”
This keeps Hubble conceptually present without real API work.

**Kimchi**
Optional story:
- “Kimchi could run long-context CV/course/resource ingestion cheaply.”
Do not depend on it for the MVP.

## Simplified Product
The MVP has one main command:

```bash
python3 careergraph.py demo
```

It does:

1. Ask the user for one career profile paragraph.
2. Ask their target career.
3. LLM extracts:
   - current skills,
   - evidence,
   - existing projects,
   - target role,
   - missing skills,
   - suggested projects,
   - suggested resources.
4. LLM creates or extends a graph plan.
5. App writes graph data into Neo4j.
6. Neo4j runs one or two headline queries.
7. App generates `out/career_map.html`.

## Demo Input
Use this on stage:

```text
I study computer science. I know Python basics, HTML, CSS, and a little JavaScript.
I have built small scripts and a static portfolio page. I want to become a full-stack developer.
I have not used databases, authentication, APIs, or deployment much.
```

Target career:

```text
Full-stack Developer
```

Expected result:

```text
Known evidence:
- Python Basics from small scripts
- HTML/CSS from static portfolio
- JavaScript Basics from small frontend work

Missing skills:
- HTTP/API Basics
- Backend Routing
- Databases
- Authentication
- Deployment

Next best skill:
HTTP/API Basics

Best portfolio project:
Task Tracker Web App

Why:
HTTP/API Basics -> Backend Routing -> Databases -> Full-stack Developer
The Task Tracker project proves backend routing, CRUD, database use, and deployment.
```

## Graph Schema
Nodes:

```cypher
(:Person {id, name})
(:CareerGoal {id, name})
(:Skill {id, name, category, difficulty})
(:Project {id, name, description})
(:Resource {id, title, type, url})
(:Evidence {id, description})
(:HelpPersona {id, name})
```

Relationships:

```cypher
(:Person)-[:TARGETS]->(:CareerGoal)
(:CareerGoal)-[:REQUIRES]->(:Skill)
(:Skill)-[:PREREQUISITE_OF]->(:Skill)
(:Person)-[:HAS_EVIDENCE]->(:Evidence)
(:Evidence)-[:PROVES]->(:Skill)
(:Person)-[:MISSING]->(:Skill)
(:Project)-[:PROVES]->(:Skill)
(:Resource)-[:TEACHES]->(:Skill)
(:HelpPersona)-[:CAN_HELP_WITH]->(:Skill)
```

This is the key reason Neo4j is justified: a single skill can be required by multiple careers, taught by multiple resources, proven by multiple projects, and blocked by multiple prerequisites.

## Headline Neo4j Queries
Use these as the sponsor-visible demo.

### 1. Shortest Career Path
Find how the learner gets from a missing blocker to the target career:

```cypher
MATCH (p:Person {id: $personId})-[:TARGETS]->(goal:CareerGoal)
MATCH (p)-[:MISSING]->(missing:Skill)
MATCH path = (missing)-[:PREREQUISITE_OF*0..5]->(required:Skill)<-[:REQUIRES]-(goal)
RETURN path
ORDER BY length(path)
LIMIT 1;
```

### 2. Best Project To Prove Missing Skills
Find the project that covers the most missing skills:

```cypher
MATCH (p:Person {id: $personId})-[:MISSING]->(s:Skill)
MATCH (project:Project)-[:PROVES]->(s)
RETURN project.name AS project,
       collect(s.name) AS provesMissingSkills,
       count(s) AS coverage
ORDER BY coverage DESC
LIMIT 1;
```

### 3. Best Resource To Unlock The Next Skill
Find a resource for the selected next skill:

```cypher
MATCH (p:Person {id: $personId})-[:MISSING]->(s:Skill)<-[:TEACHES]-(r:Resource)
RETURN s.name AS skill,
       r.title AS resource,
       r.type AS type
ORDER BY s.difficulty ASC
LIMIT 3;
```

## LLM Responsibilities
Keep the LLM powerful but bounded.

The LLM should produce JSON only:

```json
{
  "person": {
    "name": "Demo Learner",
    "targetCareer": "Full-stack Developer"
  },
  "knownEvidence": [
    {
      "description": "Built a static portfolio page",
      "provesSkills": ["HTML", "CSS"]
    }
  ],
  "missingSkills": [
    "HTTP/API Basics",
    "Backend Routing",
    "Databases",
    "Authentication",
    "Deployment"
  ],
  "careerRequires": [
    "HTML",
    "CSS",
    "JavaScript",
    "HTTP/API Basics",
    "Backend Routing",
    "Databases",
    "Authentication",
    "Deployment"
  ],
  "prerequisites": [
    ["HTTP/API Basics", "Backend Routing"],
    ["Backend Routing", "Databases"],
    ["Backend Routing", "Authentication"],
    ["Databases", "Full-stack Developer"],
    ["Deployment", "Full-stack Developer"]
  ],
  "projects": [
    {
      "name": "Task Tracker Web App",
      "description": "A CRUD app with login, task creation, database storage, and deployment.",
      "provesSkills": ["Backend Routing", "Databases", "Authentication", "Deployment"]
    }
  ],
  "resources": [
    {
      "title": "Build a Flask CRUD App",
      "type": "project tutorial",
      "teachesSkills": ["Backend Routing", "Databases"]
    }
  ],
  "nextBestSkill": "HTTP/API Basics",
  "helpPersona": "Backend mentor"
}
```

If the LLM fails JSON validation:
- retry once with a stricter prompt,
- then fall back to a built-in Full-stack Developer demo graph.

## Tessl Skill
Create:

```text
skills/careergraph-mentor/SKILL.md
```

Content:

```markdown
---
name: careergraph-mentor
description: Use when turning a learner's background into a persistent career knowledge graph with skills, projects, resources, evidence, and career paths.
---

# CareerGraph Mentor Rules

## Intake
- Extract skills only when there is evidence.
- Separate claimed interest from demonstrated evidence.
- Identify missing skills relative to the target career.
- Prefer practical portfolio projects over generic advice.

## Graph Modeling
- Model careers, skills, projects, resources, evidence, help personas, and people as nodes.
- Use relationships for REQUIRES, PREREQUISITE_OF, PROVES, TEACHES, TARGETS, and MISSING.
- Recommendations must be justified by graph paths.

## Recommendations
- Always return:
  1. known evidence,
  2. missing skills,
  3. next best skill,
  4. best portfolio project,
  5. best resource,
  6. shortest path to career goal,
  7. help persona.

## Tone
- Say "next best skill" instead of harsh weakness language.
- Make the learner feel capable.
- Keep advice specific enough to act on today.
```

## Static HTML Report
Generate:

```text
out/career_map.html
```

It should show:

- Target career
- Known evidence
- Missing skills
- Next best skill
- Best project
- Best resource
- Help persona
- Career path

Visual design:

- green = skills already proven
- orange = missing skills
- blue = next best skill
- purple = target career
- gray = resources/projects
- show path as a horizontal chain

Example visual path:

```text
HTTP/API Basics -> Backend Routing -> Databases -> Full-stack Developer
```

No full web app. No login. No dashboard.

## Build Order
1. Create Python CLI.
2. Add OpenAI-compatible LLM call.
3. Add JSON validation and fallback graph.
4. Add Neo4j connection.
5. Write graph import logic.
6. Add headline Cypher queries.
7. Generate CLI diagnosis.
8. Generate HTML report.
9. Add Tessl skill.
10. Add README with demo commands.

## Acceptance Tests
Manual tests:

- Running `python3 careergraph.py demo` produces a complete diagnosis.
- Neo4j contains Person, CareerGoal, Skill, Project, Resource, Evidence, and HelpPersona nodes.
- The best project query returns a project that covers at least two missing skills.
- The shortest path query returns a real path from a missing skill to the career goal.
- HTML report opens locally and clearly shows:
  - known evidence,
  - missing skills,
  - next best skill,
  - best project,
  - shortest career path.
- If LLM/API fails, fallback Full-stack Developer graph still demos successfully.
use the kimchi as optional api.


## What We Cut
- No quiz.
- No multi-turn tutor conversation.
- No real Hubble API.
- No real Kimchi dependency.
- No full web app.
- No authentication.
- No complex scoring.
- No scraping.
- No huge career ontology.

## Final Pitch
> CareerGraph turns your messy study history into a persistent career knowledge graph. Neo4j maps how your evidence, missing skills, projects, resources, and target career connect. Tessl turns the workflow into a reusable AI skill. The result is not generic career advice: it is a graph-backed plan for the next skill, project, and resource that move you toward your goal.
