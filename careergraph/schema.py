"""Shared data structures for the CareerGraph MVP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Evidence:
    id: str
    description: str
    proves_skills: list[str]


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    description: str
    proves_skills: list[str]


@dataclass(frozen=True)
class Resource:
    id: str
    title: str
    type: str
    teaches_skills: list[str]
    url: str | None = None


@dataclass(frozen=True)
class HelpPersona:
    id: str
    name: str
    can_help_with: list[str]


@dataclass(frozen=True)
class CareerGraphPlan:
    person_name: str
    target_career: str
    known_evidence: list[Evidence]
    missing_skills: list[str]
    career_requires: list[str]
    prerequisites: list[tuple[str, str]]
    projects: list[Project]
    resources: list[Resource]
    help_personas: list[HelpPersona]
    next_best_skill: str
    help_persona: str
    source: str

    @property
    def proven_skills(self) -> list[str]:
        return unique(
            skill
            for evidence in self.known_evidence
            for skill in evidence.proves_skills
        )


@dataclass(frozen=True)
class StoreResult:
    ok: bool
    message: str


@dataclass(frozen=True)
class DemoQueryResults:
    proven_skills: list[str]
    shortest_path: list[str]
    best_project: Project
    best_resources: list[Resource]
    next_best_skill: str
    help_persona: str


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def slugify(value: str) -> str:
    normalized = value.lower().strip()
    chars: list[str] = []
    previous_dash = False

    for char in normalized:
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True

    return "".join(chars).strip("-") or "item"
