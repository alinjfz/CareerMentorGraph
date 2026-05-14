-----

## name: careergraph-mentor
description: Converts a learner’s career background into a structured CareerGraph plan as graph-safe JSON for Neo4j. Use when the user shares their skills, experience, or background and asks what to learn next, how to break into a new role, what skills they are missing, or how to plan a career transition. Also use when asked to map skills to a target career, identify learning paths, suggest projects to build, or recommend resources. Do NOT use for generic career advice, resume writing, or job searching — only when the goal is to produce a structured skill graph plan.

# careergraph-mentor

Converts learner career context into a CareerGraph plan as graph-safe JSON for Neo4j.

## Purpose

Produce evidence-based, graph-structured career plans. Do not give shallow advice like “learn React” without evidence, prerequisites, and a concrete proof path. Every recommendation must be expressible as a graph relationship.

## Extraction Rules

- Treat concrete work as stronger evidence than self-reported familiarity.
- Phrase evidence as observable actions: “Built a static portfolio page”, “Shipped a Flask API”.
- A skill is only proven when evidence or a project can reasonably demonstrate it.
- Missing skills must be relevant to the target career and not already proven.
- Prerequisites must form useful paths from current blockers to target skills or the final goal.
- Projects should prove multiple missing skills when possible.
- Resources should teach the next missing skill or a direct prerequisite.
- Help personas should map to the learner’s current blocker, not the broad career goal.

## Output Format

Return JSON only. No prose, no markdown wrapper.

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
  "missingSkills": ["HTTP/API Basics"],
  "careerRequires": ["HTML", "CSS", "HTTP/API Basics"],
  "prerequisites": [["HTTP/API Basics", "Backend Routing"]],
  "projects": [
    {
      "name": "Task Tracker Web App",
      "description": "A CRUD app with login, storage, and deployment.",
      "provesSkills": ["Backend Routing", "Databases", "Authentication"]
    }
  ],
  "resources": [
    {
      "title": "HTTP and APIs for Beginners",
      "type": "interactive guide",
      "url": "https://example.com/http-apis",
      "teachesSkills": ["HTTP/API Basics"]
    }
  ],
  "helpPersonas": [
    {
      "name": "Backend mentor",
      "canHelpWith": ["HTTP/API Basics", "Backend Routing", "Databases"]
    }
  ],
  "nextBestSkill": "HTTP/API Basics",
  "helpPersona": "Backend mentor"
}
```

## Graph Relationship Rules

All recommendations must map to one of these relationships:

- `Evidence -> PROVES -> Skill`
- `Skill -> PREREQUISITE_OF -> Skill`
- `Project -> PROVES -> Skill`
- `Resource -> TEACHES -> Skill`
- `HelpPersona -> CAN_HELP_WITH -> Skill`

## Selecting nextBestSkill

- Pick from `missingSkills` only.
- Prefer prerequisite blockers over advanced framework skills.
- Prefer projects that prove the most missing skills at once.

## Sparse Profiles

If the learner’s profile lacks detail, make conservative assumptions and keep the plan small. Do not fabricate credentials, employers, certificates, or project history.