"""Validation and normalization for LLM-produced career graph JSON."""

from __future__ import annotations

from typing import Any

from careergraph.schema import (
    CareerGraphPlan,
    Evidence,
    HelpPersona,
    Project,
    Resource,
    slugify,
    unique,
)


class GraphPlanValidationError(ValueError):
    """Raised when LLM JSON cannot be turned into a safe graph plan."""


def graph_plan_from_payload(payload: dict[str, Any], fallback_target: str) -> CareerGraphPlan:
    required_keys = {
        "person",
        "knownEvidence",
        "missingSkills",
        "careerRequires",
        "prerequisites",
        "projects",
        "resources",
        "nextBestSkill",
        "helpPersona",
    }
    missing = sorted(required_keys.difference(payload))
    if missing:
        raise GraphPlanValidationError(f"Missing required keys: {', '.join(missing)}")

    person = require_object(payload["person"], "person")
    person_name = require_string(person.get("name"), "person.name") or "Demo Learner"
    target_career = (
        require_string(person.get("targetCareer"), "person.targetCareer")
        or fallback_target
    )

    known_evidence = [
        parse_evidence(item, index)
        for index, item in enumerate(require_list(payload["knownEvidence"], "knownEvidence"), start=1)
    ]
    missing_skills = normalize_names(require_list(payload["missingSkills"], "missingSkills"))
    career_requires = normalize_names(require_list(payload["careerRequires"], "careerRequires"))
    prerequisites = [
        parse_prerequisite(item, index)
        for index, item in enumerate(require_list(payload["prerequisites"], "prerequisites"), start=1)
    ]
    projects = [
        parse_project(item, index)
        for index, item in enumerate(require_list(payload["projects"], "projects"), start=1)
    ]
    resources = [
        parse_resource(item, index)
        for index, item in enumerate(require_list(payload["resources"], "resources"), start=1)
    ]
    help_personas = parse_help_personas(payload.get("helpPersonas"))
    next_best_skill = require_string(payload["nextBestSkill"], "nextBestSkill")
    help_persona = require_string(payload["helpPersona"], "helpPersona")

    if not missing_skills:
        raise GraphPlanValidationError("missingSkills must contain at least one skill")
    if not career_requires:
        raise GraphPlanValidationError("careerRequires must contain at least one skill")
    if not projects:
        raise GraphPlanValidationError("projects must contain at least one project")
    if not resources:
        raise GraphPlanValidationError("resources must contain at least one resource")
    if next_best_skill not in missing_skills:
        raise GraphPlanValidationError("nextBestSkill must be one of missingSkills")

    return CareerGraphPlan(
        person_name=person_name,
        target_career=target_career,
        known_evidence=known_evidence,
        missing_skills=missing_skills,
        career_requires=career_requires,
        prerequisites=prerequisites,
        projects=projects,
        resources=resources,
        help_personas=help_personas,
        next_best_skill=next_best_skill,
        help_persona=help_persona,
        source="llm",
    )


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GraphPlanValidationError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise GraphPlanValidationError(f"{field} must be a list")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise GraphPlanValidationError(f"{field} must be a string")
    stripped = value.strip()
    if not stripped:
        raise GraphPlanValidationError(f"{field} must not be empty")
    return stripped


def normalize_names(values: list[Any]) -> list[str]:
    return unique(require_string(value, "name") for value in values)


def parse_evidence(item: Any, index: int) -> Evidence:
    obj = require_object(item, f"knownEvidence[{index}]")
    description = require_string(obj.get("description"), f"knownEvidence[{index}].description")
    proves_skills = normalize_names(require_list(obj.get("provesSkills"), f"knownEvidence[{index}].provesSkills"))
    if not proves_skills:
        raise GraphPlanValidationError(f"knownEvidence[{index}].provesSkills must not be empty")
    return Evidence(
        id=f"evidence:{slugify(description)}",
        description=description,
        proves_skills=proves_skills,
    )


def parse_prerequisite(item: Any, index: int) -> tuple[str, str]:
    pair = require_list(item, f"prerequisites[{index}]")
    if len(pair) != 2:
        raise GraphPlanValidationError(f"prerequisites[{index}] must contain exactly two items")
    return (
        require_string(pair[0], f"prerequisites[{index}][0]"),
        require_string(pair[1], f"prerequisites[{index}][1]"),
    )


def parse_project(item: Any, index: int) -> Project:
    obj = require_object(item, f"projects[{index}]")
    name = require_string(obj.get("name"), f"projects[{index}].name")
    description = require_string(obj.get("description"), f"projects[{index}].description")
    proves_skills = normalize_names(require_list(obj.get("provesSkills"), f"projects[{index}].provesSkills"))
    if not proves_skills:
        raise GraphPlanValidationError(f"projects[{index}].provesSkills must not be empty")
    return Project(
        id=f"project:{slugify(name)}",
        name=name,
        description=description,
        proves_skills=proves_skills,
    )


def parse_resource(item: Any, index: int) -> Resource:
    obj = require_object(item, f"resources[{index}]")
    title = require_string(obj.get("title"), f"resources[{index}].title")
    resource_type = require_string(obj.get("type"), f"resources[{index}].type")
    teaches_skills = normalize_names(require_list(obj.get("teachesSkills"), f"resources[{index}].teachesSkills"))
    url = obj.get("url")
    if url is not None:
        url = require_string(url, f"resources[{index}].url")
    if not teaches_skills:
        raise GraphPlanValidationError(f"resources[{index}].teachesSkills must not be empty")
    return Resource(
        id=f"resource:{slugify(title)}",
        title=title,
        type=resource_type,
        teaches_skills=teaches_skills,
        url=url,
    )


def parse_help_personas(value: Any) -> list[HelpPersona]:
    if value is None:
        return default_help_personas()

    personas = []
    for index, item in enumerate(require_list(value, "helpPersonas"), start=1):
        obj = require_object(item, f"helpPersonas[{index}]")
        name = require_string(obj.get("name"), f"helpPersonas[{index}].name")
        can_help_with = normalize_names(require_list(obj.get("canHelpWith"), f"helpPersonas[{index}].canHelpWith"))
        personas.append(
            HelpPersona(
                id=f"persona:{slugify(name)}",
                name=name,
                can_help_with=can_help_with,
            )
        )

    return personas or default_help_personas()


def default_help_personas() -> list[HelpPersona]:
    return [
        HelpPersona(
            id="persona:senior-frontend-mentor",
            name="Senior frontend mentor",
            can_help_with=["HTML", "CSS", "JavaScript Basics", "React"],
        ),
        HelpPersona(
            id="persona:backend-mentor",
            name="Backend mentor",
            can_help_with=["HTTP/API Basics", "Backend Routing", "Databases", "Authentication", "Deployment"],
        ),
        HelpPersona(
            id="persona:career-coach",
            name="Career coach",
            can_help_with=["Portfolio Strategy", "Interview Preparation", "Career Planning"],
        ),
    ]
