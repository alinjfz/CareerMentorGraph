"""Deterministic Full-stack Developer demo graph."""

from __future__ import annotations

from careergraph.schema import CareerGraphPlan, Evidence, HelpPersona, Project, Resource

DEMO_PROFILE = (
    "I study computer science. I know Python basics, HTML, CSS, and a little JavaScript. "
    "I have built small scripts and a static portfolio page. I want to become a full-stack "
    "developer. I have not used databases, authentication, APIs, or deployment much."
)

DEMO_TARGET = "Full-stack Developer"


def build_fallback_demo(profile: str = DEMO_PROFILE, target_career: str = DEMO_TARGET) -> CareerGraphPlan:
    target = target_career.strip() or DEMO_TARGET

    return CareerGraphPlan(
        person_name="Demo Learner",
        target_career=target,
        known_evidence=[
            Evidence(
                id="evidence:small-scripts",
                description="Built small scripts",
                proves_skills=["Python Basics"],
            ),
            Evidence(
                id="evidence:static-portfolio",
                description="Built a static portfolio page",
                proves_skills=["HTML", "CSS"],
            ),
            Evidence(
                id="evidence:small-frontend-work",
                description="Built small frontend work with a little JavaScript",
                proves_skills=["JavaScript Basics"],
            ),
        ],
        missing_skills=[
            "HTTP/API Basics",
            "Backend Routing",
            "Databases",
            "Authentication",
            "Deployment",
        ],
        career_requires=[
            "HTML",
            "CSS",
            "JavaScript Basics",
            "HTTP/API Basics",
            "Backend Routing",
            "Databases",
            "Authentication",
            "Deployment",
        ],
        prerequisites=[
            ("HTTP/API Basics", "Backend Routing"),
            ("Backend Routing", "Databases"),
            ("Backend Routing", "Authentication"),
            ("Databases", target),
            ("Deployment", target),
        ],
        projects=[
            Project(
                id="project:task-tracker-web-app",
                name="Task Tracker Web App",
                description=(
                    "A CRUD app with login, task creation, database storage, and deployment."
                ),
                proves_skills=[
                    "Backend Routing",
                    "Databases",
                    "Authentication",
                    "Deployment",
                ],
            ),
            Project(
                id="project:api-backed-portfolio",
                name="API-backed Portfolio",
                description=(
                    "A portfolio that loads project data from a backend API and stores edits "
                    "in a database."
                ),
                proves_skills=["HTTP/API Basics", "Backend Routing", "Databases"],
            ),
        ],
        resources=[
            Resource(
                id="resource:http-api-basics",
                title="HTTP and APIs for Beginners",
                type="interactive guide",
                teaches_skills=["HTTP/API Basics"],
            ),
            Resource(
                id="resource:flask-crud-app",
                title="Build a Flask CRUD App",
                type="project tutorial",
                teaches_skills=["Backend Routing", "Databases"],
            ),
            Resource(
                id="resource:deploy-web-app",
                title="Deploy a Web App End to End",
                type="deployment walkthrough",
                teaches_skills=["Deployment"],
            ),
        ],
        help_personas=[
            HelpPersona(
                id="persona:senior-frontend-mentor",
                name="Senior frontend mentor",
                can_help_with=["HTML", "CSS", "JavaScript Basics"],
            ),
            HelpPersona(
                id="persona:backend-mentor",
                name="Backend mentor",
                can_help_with=[
                    "HTTP/API Basics",
                    "Backend Routing",
                    "Databases",
                    "Authentication",
                    "Deployment",
                ],
            ),
            HelpPersona(
                id="persona:career-coach",
                name="Career coach",
                can_help_with=["Portfolio Strategy", "Interview Preparation"],
            ),
        ],
        next_best_skill="HTTP/API Basics",
        help_persona="Backend mentor",
        source="fallback_demo",
    )
