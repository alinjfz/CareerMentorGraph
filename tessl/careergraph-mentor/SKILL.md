# careergraph-mentor

Use this skill when converting learner career context into a CareerGraph plan.

## Purpose

CareerGraph is a graph-first career mentor. The model should not give shallow
advice like "learn React" without evidence, prerequisites, and a concrete proof
path. It should produce graph-safe JSON that can be written into Neo4j.

## Extraction Rules

- Treat concrete work as stronger than self-reported familiarity.
- Evidence should be phrased as observable actions, such as "Built a static
  portfolio page" or "Shipped a Flask API".
- A skill is proven only when evidence or a project can reasonably demonstrate it.
- Missing skills should be relevant to the target career and not already proven.
- Prerequisites should form useful paths from current blockers to target skills
  or the final career goal.
- Projects should prove multiple missing skills when possible.
- Resources should teach the next missing skill or a direct prerequisite.
- Help personas should map to the learner's current blocker, not to the broad
  career goal.

## Required JSON Shape

Return JSON only:

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

## Recommendation Rules

- Pick `nextBestSkill` from `missingSkills`.
- Prefer prerequisite blockers over advanced framework skills.
- Prefer portfolio projects that prove the most missing skills.
- Justification must be expressible as graph relationships:
  - `Evidence -> PROVES -> Skill`
  - `Skill -> PREREQUISITE_OF -> Skill`
  - `Project -> PROVES -> Skill`
  - `Resource -> TEACHES -> Skill`
  - `HelpPersona -> CAN_HELP_WITH -> Skill`

## Failure Behavior

If the learner profile is sparse, make conservative assumptions and keep the
plan small. Do not fabricate specific credentials, employers, certificates, or
project history.
