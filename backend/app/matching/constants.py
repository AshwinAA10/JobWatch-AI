"""Configuration constants, weights, and aliases for deterministic matching."""

from typing import Dict, Tuple

# Current matching scoring algorithm version
SCORING_VERSION: str = "v1"

# Dimension weights for score computation (sum must be 1.0)
DEFAULT_MATCH_WEIGHTS: Dict[str, float] = {
    "skills": 0.35,
    "experience": 0.20,
    "title": 0.15,
    "location": 0.10,
    "workplace": 0.10,
    "employment_type": 0.05,
    "salary": 0.03,
    "education": 0.02,
}

# Skill component weights (required vs preferred)
REQUIRED_SKILL_WEIGHT: float = 0.80
PREFERRED_SKILL_WEIGHT: float = 0.20

# Canonical skill aliases for deterministic normalization
SKILL_ALIASES: Dict[str, str] = {
    "reactjs": "react",
    "react.js": "react",
    "react native": "react-native",
    "nodejs": "node.js",
    "node": "node.js",
    "node js": "node.js",
    "typescript": "typescript",
    "ts": "typescript",
    "javascript": "javascript",
    "js": "javascript",
    "python3": "python",
    "py": "python",
    "golang": "go",
    "postgres": "postgresql",
    "psql": "postgresql",
    "k8s": "kubernetes",
    "docker": "docker",
    "aws": "amazon web services",
    "amazon web services": "amazon web services",
    "gcp": "google cloud platform",
    "azure": "azure",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "c#": "c#",
    "csharp": "c#",
    ".net": ".net",
    "dotnet": ".net",
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "graphql": "graphql",
    "rest": "rest",
    "rest api": "rest",
    "restful": "rest",
    "ci/cd": "cicd",
    "ci-cd": "cicd",
    "cicd": "cicd",
}

# Title aliases for deterministic normalization
TITLE_ALIASES: Dict[str, str] = {
    "engineer": "developer",
    "programmer": "developer",
    "coder": "developer",
    "sw": "software",
    "swe": "software developer",
    "sde": "software developer",
    "sr": "senior",
    "jr": "junior",
    "fullstack": "full stack",
    "frontend": "front end",
    "backend": "back end",
}

# Education levels mapped to numeric hierarchy for threshold comparison
EDUCATION_HIERARCHY: Dict[str, int] = {
    "high school": 1,
    "associate": 2,
    "bachelor": 3,
    "bachelors": 3,
    "bachelor's": 3,
    "bs": 3,
    "ba": 3,
    "btech": 3,
    "b.tech": 3,
    "be": 3,
    "b.e": 3,
    "b.sc": 3,
    "master": 4,
    "masters": 4,
    "master's": 4,
    "ms": 4,
    "msc": 4,
    "m.sc": 4,
    "mtech": 4,
    "m.tech": 4,
    "mba": 4,
    "doctorate": 5,
    "phd": 5,
    "ph.d": 5,
}

# Engineering interpretation bands (informational, not guarantees)
SCORE_BANDS: Dict[str, Tuple[float, float]] = {
    "STRONG_MATCH": (80.0, 100.0),
    "MODERATE_MATCH": (60.0, 79.99),
    "WEAK_MATCH": (40.0, 59.99),
    "POOR_MATCH": (0.0, 39.99),
}
