"""Domain models and seed data for Phase 13 Skill Ontology and Relationships."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class SkillRelationType(str, Enum):
    """Semantic relationship types between skills."""

    ALIAS = "ALIAS"                      # Exact equivalent (e.g. JS -> JavaScript)
    PARENT = "PARENT"                    # Generalization (e.g. JavaScript is parent of React)
    CHILD = "CHILD"                      # Specialization (e.g. FastAPI is child of Python)
    RELATED = "RELATED"                  # Complementary (e.g. Docker and Kubernetes)
    TRANSFERABLE = "TRANSFERABLE"        # Transferable capability (e.g. PostgreSQL -> MySQL, FastAPI -> REST APIs)


@dataclass
class SkillNode:
    """Canonical representation of a skill within the ontology graph."""

    canonical_name: str
    category: str
    aliases: Set[str] = field(default_factory=set)
    transferable_to: Dict[str, float] = field(default_factory=dict)  # target_skill -> transfer_weight (0.0 to 1.0)
    related_skills: Set[str] = field(default_factory=set)


# Curated, practical baseline ontology for modern software, cloud, and data engineering
CORE_ONTOLOGY_DATA: List[Dict] = [
    # Languages
    {
        "canonical_name": "Python",
        "category": "Programming Languages",
        "aliases": ["py", "python3", "python 3"],
        "transferable_to": {"FastAPI": 0.85, "Django": 0.85, "Flask": 0.85, "Backend Development": 0.80},
        "related": ["Django", "FastAPI", "Flask", "Pandas", "PyTorch"],
    },
    {
        "canonical_name": "JavaScript",
        "category": "Programming Languages",
        "aliases": ["js", "ecmascript", "es6", "es2020"],
        "transferable_to": {"TypeScript": 0.80, "Node.js": 0.85, "React": 0.80, "Frontend Development": 0.85},
        "related": ["TypeScript", "React", "Node.js", "Vue", "Angular"],
    },
    {
        "canonical_name": "TypeScript",
        "category": "Programming Languages",
        "aliases": ["ts"],
        "transferable_to": {"JavaScript": 0.95, "React": 0.85, "Node.js": 0.85},
        "related": ["JavaScript", "React", "Node.js", "Next.js"],
    },
    {
        "canonical_name": "SQL",
        "category": "Data & Databases",
        "aliases": ["ansi sql", "structured query language"],
        "transferable_to": {"PostgreSQL": 0.85, "MySQL": 0.85, "Database Design": 0.90},
        "related": ["PostgreSQL", "MySQL", "Database Design", "Redis"],
    },
    {
        "canonical_name": "Java",
        "category": "Programming Languages",
        "aliases": ["java 17", "java 21", "java 11", "jdk"],
        "transferable_to": {"Kotlin": 0.75, "Spring Boot": 0.85, "Backend Development": 0.80},
        "related": ["Spring Boot", "Kotlin", "Hibernate", "JVM"],
    },
    {
        "canonical_name": "Go",
        "category": "Programming Languages",
        "aliases": ["golang"],
        "transferable_to": {"Backend Development": 0.85, "Distributed Systems": 0.80},
        "related": ["Docker", "Kubernetes", "gRPC", "Microservices"],
    },
    {
        "canonical_name": "C++",
        "category": "Programming Languages",
        "aliases": ["cpp", "cplusplus"],
        "transferable_to": {"C": 0.90, "Systems Programming": 0.90},
        "related": ["C", "Rust", "Embedded Systems"],
    },
    {
        "canonical_name": "Rust",
        "category": "Programming Languages",
        "aliases": ["rust-lang"],
        "transferable_to": {"Systems Programming": 0.85, "C++": 0.70},
        "related": ["C++", "WebAssembly", "Concurrency"],
    },

    # Frameworks & Libraries
    {
        "canonical_name": "React",
        "category": "Frontend Frameworks",
        "aliases": ["reactjs", "react.js", "react-native"],
        "transferable_to": {"Next.js": 0.90, "Vue.js": 0.75, "Frontend Development": 0.95},
        "related": ["Next.js", "TypeScript", "JavaScript", "HTML", "CSS", "Redux"],
    },
    {
        "canonical_name": "FastAPI",
        "category": "Backend Frameworks",
        "aliases": ["fast-api", "fastapi framework"],
        "transferable_to": {"REST APIs": 0.95, "Flask": 0.85, "Python": 0.90},
        "related": ["Python", "Pydantic", "Uvicorn", "REST APIs", "AsyncIO"],
    },
    {
        "canonical_name": "Django",
        "category": "Backend Frameworks",
        "aliases": ["django-rest-framework", "drf"],
        "transferable_to": {"FastAPI": 0.80, "REST APIs": 0.90, "Python": 0.90},
        "related": ["Python", "PostgreSQL", "ORM", "REST APIs"],
    },
    {
        "canonical_name": "Node.js",
        "category": "Backend Runtimes",
        "aliases": ["nodejs", "node"],
        "transferable_to": {"Express.js": 0.90, "Backend Development": 0.85, "JavaScript": 0.90},
        "related": ["Express.js", "TypeScript", "JavaScript", "REST APIs"],
    },
    {
        "canonical_name": "Spring Boot",
        "category": "Backend Frameworks",
        "aliases": ["springboot", "spring-boot", "spring framework"],
        "transferable_to": {"Java": 0.90, "Microservices": 0.85, "REST APIs": 0.90},
        "related": ["Java", "Hibernate", "Microservices", "PostgreSQL"],
    },

    # Databases & Storage
    {
        "canonical_name": "PostgreSQL",
        "category": "Data & Databases",
        "aliases": ["postgres", "pgsql", "postgresql 16"],
        "transferable_to": {"SQL": 0.95, "MySQL": 0.85, "Relational Databases": 0.95},
        "related": ["SQL", "MySQL", "pgvector", "SQLAlchemy", "Database Design"],
    },
    {
        "canonical_name": "MySQL",
        "category": "Data & Databases",
        "aliases": ["my-sql"],
        "transferable_to": {"SQL": 0.95, "PostgreSQL": 0.85, "Relational Databases": 0.95},
        "related": ["SQL", "PostgreSQL", "Relational Databases"],
    },
    {
        "canonical_name": "MongoDB",
        "category": "Data & Databases",
        "aliases": ["mongo", "documentdb"],
        "transferable_to": {"NoSQL": 0.95, "Document Databases": 0.95},
        "related": ["NoSQL", "Mongoose", "Node.js"],
    },
    {
        "canonical_name": "Redis",
        "category": "Data & Databases",
        "aliases": ["redis-cache"],
        "transferable_to": {"Caching": 0.95, "In-Memory Databases": 0.95},
        "related": ["PostgreSQL", "Message Queues", "Caching"],
    },

    # Cloud & DevOps
    {
        "canonical_name": "Docker",
        "category": "DevOps & Cloud",
        "aliases": ["docker containers", "docker compose"],
        "transferable_to": {"Containerization": 0.95, "Kubernetes": 0.70},
        "related": ["Kubernetes", "Linux", "CI/CD"],
    },
    {
        "canonical_name": "Kubernetes",
        "category": "DevOps & Cloud",
        "aliases": ["k8s", "k8"],
        "transferable_to": {"Docker": 0.90, "Container Orchestration": 0.95, "Cloud Infrastructure": 0.85},
        "related": ["Docker", "Helm", "Cloud Infrastructure", "DevOps"],
    },
    {
        "canonical_name": "AWS",
        "category": "DevOps & Cloud",
        "aliases": ["amazon web services", "amazon aws"],
        "transferable_to": {"Cloud Computing": 0.95, "GCP": 0.75, "Azure": 0.75},
        "related": ["GCP", "Azure", "Terraform", "Docker"],
    },
    {
        "canonical_name": "GCP",
        "category": "DevOps & Cloud",
        "aliases": ["google cloud", "google cloud platform"],
        "transferable_to": {"Cloud Computing": 0.95, "AWS": 0.75, "Azure": 0.75},
        "related": ["AWS", "Kubernetes", "Cloud Computing"],
    },
    {
        "canonical_name": "Azure",
        "category": "DevOps & Cloud",
        "aliases": ["microsoft azure"],
        "transferable_to": {"Cloud Computing": 0.95, "AWS": 0.75, "GCP": 0.75},
        "related": ["AWS", "GCP", "Cloud Computing"],
    },
    {
        "canonical_name": "CI/CD",
        "category": "DevOps & Cloud",
        "aliases": ["continuous integration", "continuous deployment", "github actions", "gitlab ci"],
        "transferable_to": {"DevOps": 0.85, "Automation": 0.85},
        "related": ["Docker", "Git", "DevOps"],
    },

    # Concepts & Architecture
    {
        "canonical_name": "REST APIs",
        "category": "Architecture & Concepts",
        "aliases": ["restful apis", "rest api", "rest", "web api"],
        "transferable_to": {"API Design": 0.95, "FastAPI": 0.80, "Express.js": 0.80},
        "related": ["FastAPI", "HTTP", "GraphQL", "gRPC"],
    },
    {
        "canonical_name": "Microservices",
        "category": "Architecture & Concepts",
        "aliases": ["microservice architecture", "distributed services"],
        "transferable_to": {"Distributed Systems": 0.90, "System Design": 0.85},
        "related": ["Docker", "Kubernetes", "REST APIs", "gRPC"],
    },
]
