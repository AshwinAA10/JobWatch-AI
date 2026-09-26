from app.repositories.candidate_preferences import CandidatePreferencesRepository
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.candidate_skill import CandidateSkillRepository
from app.repositories.career_source import CareerSourceRepository
from app.repositories.company import CompanyRepository
from app.repositories.education import EducationRepository
from app.repositories.experience import ExperienceRepository
from app.repositories.job import JobRepository
from app.repositories.job_duplicate import JobDuplicateRepository
from app.repositories.monitoring_run import MonitoringRunRepository
from app.repositories.skill import SkillRepository
from app.repositories.user import UserRepository

__all__ = [
    "CompanyRepository",
    "CareerSourceRepository",
    "JobRepository",
    "JobDuplicateRepository",
    "MonitoringRunRepository",
    "UserRepository",
    "CandidateProfileRepository",
    "SkillRepository",
    "CandidateSkillRepository",
    "ExperienceRepository",
    "EducationRepository",
    "CandidatePreferencesRepository",
]
