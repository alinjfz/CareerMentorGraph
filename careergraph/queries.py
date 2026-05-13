"""CareerGraph query helpers.

The in-memory helpers keep the demo reliable without Neo4j. The Cypher strings
mirror the same questions for the persisted graph.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from careergraph.config import Neo4jConfig
from careergraph.neo4j_store import skill_id
from careergraph.schema import CareerGraphPlan, DemoQueryResults, HelpPersona, Project, Resource


SHORTEST_CAREER_PATH_QUERY = """
MATCH (p:Person {id: $personId})-[:TARGETS]->(goal:CareerGoal)
MATCH (p)-[:MISSING]->(missing:Skill)
MATCH path = (missing)-[:PREREQUISITE_OF*0..5]->(goal)
RETURN [node IN nodes(path) | node.name] AS path
ORDER BY length(path)
LIMIT 1
"""

BEST_PROJECT_QUERY = """
MATCH (p:Person {id: $personId})-[:MISSING]->(s:Skill)
MATCH (project:Project)-[:PROVES]->(s)
RETURN project.name AS project,
       project.description AS description,
       collect(s.name) AS provesMissingSkills,
       count(s) AS coverage
ORDER BY coverage DESC, project.name ASC
LIMIT 1
"""

BEST_RESOURCE_QUERY = """
MATCH (p:Person {id: $personId})-[:MISSING]->(s:Skill)<-[:TEACHES]-(r:Resource)
RETURN s.name AS skill,
       r.title AS resource,
       r.type AS type,
       r.url AS url
ORDER BY s.difficulty ASC, r.title ASC
LIMIT 3
"""

HELP_PERSONA_QUERY = """
MATCH (skill:Skill {id: $skillId})<-[:CAN_HELP_WITH]-(persona:HelpPersona)
RETURN persona.name AS persona
ORDER BY persona.name ASC
LIMIT 1
"""


def build_demo_results(graph_plan: CareerGraphPlan) -> DemoQueryResults:
    return DemoQueryResults(
        proven_skills=graph_plan.proven_skills,
        shortest_path=find_shortest_path(
            starts=[graph_plan.next_best_skill],
            target=graph_plan.target_career,
            edges=graph_plan.prerequisites,
        ),
        best_project=find_best_project(graph_plan),
        best_resources=find_best_resources(graph_plan),
        next_best_skill=graph_plan.next_best_skill,
        help_persona=select_help_persona(graph_plan).name,
    )


def build_neo4j_results(
    graph_plan: CareerGraphPlan,
    config: Neo4jConfig,
    person_id: str = "person:demo-learner",
) -> DemoQueryResults:
    try:
        from neo4j import GraphDatabase
    except ImportError:
        return build_demo_results(graph_plan)

    driver = GraphDatabase.driver(config.uri, auth=(config.username, config.password))
    try:
        with driver.session(database=config.database) as session:
            path_record = session.run(SHORTEST_CAREER_PATH_QUERY, personId=person_id).single()
            project_record = session.run(BEST_PROJECT_QUERY, personId=person_id).single()
            resource_records = list(session.run(BEST_RESOURCE_QUERY, personId=person_id))
            persona_record = session.run(
                HELP_PERSONA_QUERY,
                skillId=skill_id(graph_plan.next_best_skill),
            ).single()
    finally:
        driver.close()

    fallback = build_demo_results(graph_plan)
    return DemoQueryResults(
        proven_skills=graph_plan.proven_skills,
        shortest_path=path_record["path"] if path_record else fallback.shortest_path,
        best_project=project_from_record(project_record, fallback.best_project),
        best_resources=resources_from_records(resource_records, fallback.best_resources),
        next_best_skill=graph_plan.next_best_skill,
        help_persona=persona_record["persona"] if persona_record else fallback.help_persona,
    )


def find_shortest_path(
    starts: list[str],
    target: str,
    edges: list[tuple[str, str]],
) -> list[str]:
    adjacency: dict[str, list[str]] = {}
    for source, destination in edges:
        adjacency.setdefault(source, []).append(destination)

    queue: deque[list[str]] = deque([[start] for start in starts])
    visited: set[str] = set()

    while queue:
        path = queue.popleft()
        current = path[-1]

        if current == target:
            return path

        if current in visited:
            continue

        visited.add(current)

        for next_node in adjacency.get(current, []):
            queue.append([*path, next_node])

    return [starts[0], target] if starts else [target]


def find_best_project(graph_plan: CareerGraphPlan) -> Project:
    missing = set(graph_plan.missing_skills)

    return max(
        graph_plan.projects,
        key=lambda project: (len(missing.intersection(project.proves_skills)), project.name),
    )


def find_best_resources(graph_plan: CareerGraphPlan) -> list[Resource]:
    missing = set(graph_plan.missing_skills)
    next_skill = graph_plan.next_best_skill

    matching = [
        resource
        for resource in graph_plan.resources
        if next_skill in resource.teaches_skills
        or missing.intersection(resource.teaches_skills)
    ]

    return matching[:3]


def select_help_persona(graph_plan: CareerGraphPlan) -> HelpPersona:
    for persona in graph_plan.help_personas:
        if graph_plan.next_best_skill in persona.can_help_with:
            return persona

    for persona in graph_plan.help_personas:
        if persona.name == graph_plan.help_persona:
            return persona

    return graph_plan.help_personas[0]


def project_from_record(record: Any, fallback: Project) -> Project:
    if not record:
        return fallback
    return Project(
        id=fallback.id,
        name=record["project"],
        description=record["description"],
        proves_skills=list(record["provesMissingSkills"]),
    )


def resources_from_records(records: list[Any], fallback: list[Resource]) -> list[Resource]:
    if not records:
        return fallback
    return [
        Resource(
            id=f"resource:{index}",
            title=record["resource"],
            type=record["type"],
            url=record["url"],
            teaches_skills=[record["skill"]],
        )
        for index, record in enumerate(records, start=1)
    ]
