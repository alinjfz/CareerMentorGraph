"""Neo4j write boundary for CareerGraph."""

from __future__ import annotations

from typing import Any

from careergraph.config import Neo4jConfig, get_neo4j_config
from careergraph.schema import CareerGraphPlan, StoreResult, slugify, unique


CONSTRAINTS = [
    "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT career_goal_id IF NOT EXISTS FOR (n:CareerGoal) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (n:Skill) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (n:Project) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT resource_id IF NOT EXISTS FOR (n:Resource) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (n:Evidence) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT help_persona_id IF NOT EXISTS FOR (n:HelpPersona) REQUIRE n.id IS UNIQUE",
]

WRITE_PERSON_GOAL_CYPHER = """
MERGE (person:Person {id: $person.id})
SET person.name = $person.name

MERGE (goal:CareerGoal {id: $goal.id})
SET goal.name = $goal.name

MERGE (person)-[:TARGETS]->(goal)
"""

WRITE_SKILLS_CYPHER = """
UNWIND $skills AS skill
MERGE (s:Skill {id: skill.id})
SET s.name = skill.name,
    s.category = skill.category,
    s.difficulty = skill.difficulty
"""

WRITE_CAREER_REQUIRES_CYPHER = """
MATCH (goal:CareerGoal {id: $goalId})
UNWIND $career_requires AS requiredSkill
MATCH (s:Skill {id: requiredSkill.id})
MERGE (goal)-[:REQUIRES]->(s)
"""

WRITE_MISSING_SKILLS_CYPHER = """
MATCH (person:Person {id: $personId})
UNWIND $missing_skills AS missingSkill
MATCH (s:Skill {id: missingSkill.id})
MERGE (person)-[:MISSING]->(s)
"""

WRITE_EVIDENCE_CYPHER = """
MATCH (person:Person {id: $personId})
UNWIND $evidence AS evidence
MERGE (e:Evidence {id: evidence.id})
SET e.description = evidence.description
MERGE (person)-[:HAS_EVIDENCE]->(e)
"""

WRITE_EVIDENCE_PROVES_CYPHER = """
UNWIND $evidence AS evidence
MATCH (e:Evidence {id: evidence.id})
UNWIND evidence.proves AS provedSkill
MATCH (s:Skill {id: provedSkill.id})
MERGE (e)-[:PROVES]->(s)
"""

WRITE_PROJECTS_CYPHER = """
UNWIND $projects AS project
MERGE (p:Project {id: project.id})
SET p.name = project.name,
    p.description = project.description
"""

WRITE_PROJECT_PROVES_CYPHER = """
UNWIND $projects AS project
MATCH (p:Project {id: project.id})
UNWIND project.proves AS provedSkill
MATCH (s:Skill {id: provedSkill.id})
MERGE (p)-[:PROVES]->(s)
"""

WRITE_RESOURCES_CYPHER = """
UNWIND $resources AS resource
MERGE (r:Resource {id: resource.id})
SET r.title = resource.title,
    r.type = resource.type,
    r.url = resource.url
"""

WRITE_RESOURCE_TEACHES_CYPHER = """
UNWIND $resources AS resource
MATCH (r:Resource {id: resource.id})
UNWIND resource.teaches AS taughtSkill
MATCH (s:Skill {id: taughtSkill.id})
MERGE (r)-[:TEACHES]->(s)
"""

WRITE_HELP_PERSONAS_CYPHER = """
UNWIND $help_personas AS persona
MERGE (hp:HelpPersona {id: persona.id})
SET hp.name = persona.name
"""

WRITE_HELP_PERSONA_SKILLS_CYPHER = """
UNWIND $help_personas AS persona
MATCH (hp:HelpPersona {id: persona.id})
UNWIND persona.can_help_with AS skill
MATCH (s:Skill {id: skill.id})
MERGE (hp)-[:CAN_HELP_WITH]->(s)
"""

WRITE_PREREQUISITES_CYPHER = """
UNWIND $prerequisites AS edge
MATCH (source:Skill {id: edge.source.id})
OPTIONAL MATCH (targetSkill:Skill {id: edge.target.id})
OPTIONAL MATCH (targetGoal:CareerGoal {id: edge.target.id})
WITH source, edge, coalesce(targetSkill, targetGoal) AS target
WHERE target IS NOT NULL
MERGE (source)-[:PREREQUISITE_OF]->(target)
"""


def write_graph(
    graph_plan: CareerGraphPlan,
    enabled: bool = False,
    config: Neo4jConfig | None = None,
) -> StoreResult:
    payload = build_graph_payload(graph_plan)

    if not enabled:
        return StoreResult(
            ok=True,
            message=(
                f"dry run prepared {payload['node_count']} graph nodes and "
                f"{payload['relationship_count']} relationships; pass --write-neo4j to persist."
            ),
        )

    config = config or get_neo4j_config()
    if config is None:
        return StoreResult(
            ok=False,
            message="Neo4j write skipped: set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD.",
        )

    try:
        from neo4j import GraphDatabase
    except ImportError:
        return StoreResult(
            ok=False,
            message="Neo4j write skipped: install dependencies from requirements.txt.",
        )

    driver = GraphDatabase.driver(config.uri, auth=(config.username, config.password))
    try:
        with driver.session(database=config.database) as session:
            for statement in CONSTRAINTS:
                session.run(statement)
            session.execute_write(_write_graph_transaction, payload)
    finally:
        driver.close()

    return StoreResult(
        ok=True,
        message=(
            f"wrote {payload['node_count']} graph nodes and "
            f"{payload['relationship_count']} relationships to Neo4j."
        ),
    )


def _write_graph_transaction(tx: Any, payload: dict[str, Any]) -> None:
    tx.run(WRITE_PERSON_GOAL_CYPHER, person=payload["person"], goal=payload["goal"])
    tx.run(WRITE_SKILLS_CYPHER, skills=payload["skills"])
    tx.run(
        WRITE_CAREER_REQUIRES_CYPHER,
        goalId=payload["goal"]["id"],
        career_requires=payload["career_requires"],
    )
    tx.run(
        WRITE_MISSING_SKILLS_CYPHER,
        personId=payload["person"]["id"],
        missing_skills=payload["missing_skills"],
    )
    tx.run(WRITE_EVIDENCE_CYPHER, personId=payload["person"]["id"], evidence=payload["evidence"])
    tx.run(WRITE_EVIDENCE_PROVES_CYPHER, evidence=payload["evidence"])
    tx.run(WRITE_PROJECTS_CYPHER, projects=payload["projects"])
    tx.run(WRITE_PROJECT_PROVES_CYPHER, projects=payload["projects"])
    tx.run(WRITE_RESOURCES_CYPHER, resources=payload["resources"])
    tx.run(WRITE_RESOURCE_TEACHES_CYPHER, resources=payload["resources"])
    tx.run(WRITE_HELP_PERSONAS_CYPHER, help_personas=payload["help_personas"])
    tx.run(WRITE_HELP_PERSONA_SKILLS_CYPHER, help_personas=payload["help_personas"])
    tx.run(WRITE_PREREQUISITES_CYPHER, prerequisites=payload["prerequisites"])


def build_graph_payload(graph_plan: CareerGraphPlan) -> dict[str, Any]:
    skill_names = collect_skill_names(graph_plan)
    skills = [skill_payload(name) for name in skill_names]
    goal = {"id": career_id(graph_plan.target_career), "name": graph_plan.target_career}

    payload = {
        "person": {"id": "person:demo-learner", "name": graph_plan.person_name},
        "goal": goal,
        "skills": skills,
        "career_requires": [skill_ref(name) for name in graph_plan.career_requires],
        "missing_skills": [skill_ref(name) for name in graph_plan.missing_skills],
        "evidence": [
            {
                "id": evidence.id,
                "description": evidence.description,
                "proves": [skill_ref(name) for name in evidence.proves_skills],
            }
            for evidence in graph_plan.known_evidence
        ],
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "proves": [skill_ref(name) for name in project.proves_skills],
            }
            for project in graph_plan.projects
        ],
        "resources": [
            {
                "id": resource.id,
                "title": resource.title,
                "type": resource.type,
                "url": resource.url,
                "teaches": [skill_ref(name) for name in resource.teaches_skills],
            }
            for resource in graph_plan.resources
        ],
        "help_personas": [
            {
                "id": persona.id,
                "name": persona.name,
                "can_help_with": [skill_ref(name) for name in persona.can_help_with if name in skill_names],
            }
            for persona in graph_plan.help_personas
        ],
        "prerequisites": [
            {"source": skill_ref(source), "target": graph_target_ref(destination, graph_plan)}
            for source, destination in graph_plan.prerequisites
        ],
    }
    payload["node_count"] = (
        1
        + 1
        + len(payload["skills"])
        + len(payload["evidence"])
        + len(payload["projects"])
        + len(payload["resources"])
        + len(payload["help_personas"])
    )
    payload["relationship_count"] = estimate_relationship_count(payload)
    return payload


def collect_skill_names(graph_plan: CareerGraphPlan) -> list[str]:
    prerequisite_skill_names = [
        name
        for pair in graph_plan.prerequisites
        for name in pair
        if name != graph_plan.target_career
    ]
    return unique(
        [
            *graph_plan.career_requires,
            *graph_plan.missing_skills,
            *graph_plan.proven_skills,
            *prerequisite_skill_names,
            *[
                skill
                for project in graph_plan.projects
                for skill in project.proves_skills
            ],
            *[
                skill
                for resource in graph_plan.resources
                for skill in resource.teaches_skills
            ],
        ]
    )


def skill_payload(name: str) -> dict[str, Any]:
    return {
        "id": skill_id(name),
        "name": name,
        "category": infer_skill_category(name),
        "difficulty": infer_skill_difficulty(name),
    }


def skill_ref(name: str) -> dict[str, str]:
    return {"id": skill_id(name), "name": name}


def graph_target_ref(name: str, graph_plan: CareerGraphPlan) -> dict[str, str]:
    if name == graph_plan.target_career:
        return {"id": career_id(name), "name": name}
    return skill_ref(name)


def skill_id(name: str) -> str:
    return f"skill:{slugify(name)}"


def career_id(name: str) -> str:
    return f"career:{slugify(name)}"


def infer_skill_category(name: str) -> str:
    lowered = name.lower()
    if any(token in lowered for token in ["html", "css", "javascript", "react", "frontend"]):
        return "frontend"
    if any(token in lowered for token in ["api", "backend", "database", "auth"]):
        return "backend"
    if any(token in lowered for token in ["deploy", "cloud", "ci"]):
        return "delivery"
    return "general"


def infer_skill_difficulty(name: str) -> int:
    lowered = name.lower()
    if any(token in lowered for token in ["basic", "html", "css"]):
        return 1
    if any(token in lowered for token in ["auth", "database", "deployment"]):
        return 3
    return 2


def estimate_relationship_count(payload: dict[str, Any]) -> int:
    evidence_proves = sum(len(item["proves"]) for item in payload["evidence"])
    project_proves = sum(len(item["proves"]) for item in payload["projects"])
    resource_teaches = sum(len(item["teaches"]) for item in payload["resources"])
    persona_help = sum(len(item["can_help_with"]) for item in payload["help_personas"])
    return (
        1
        + len(payload["career_requires"])
        + len(payload["missing_skills"])
        + len(payload["evidence"])
        + evidence_proves
        + project_proves
        + resource_teaches
        + persona_help
        + len(payload["prerequisites"])
    )
