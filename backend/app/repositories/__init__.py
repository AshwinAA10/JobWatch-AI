from app.repositories.ai_explanation import AIExplanationRepository
from app.repositories.ai_job_extraction import AIJobExtractionRepository
from app.repositories.candidate_embedding import CandidateEmbeddingRepository
from app.repositories.candidate_preferences import CandidatePreferencesRepository
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.candidate_skill import CandidateSkillRepository
from app.repositories.career_source import CareerSourceRepository
from app.repositories.company import CompanyRepository
from app.repositories.education import EducationRepository
from app.repositories.experience import ExperienceRepository
from app.repositories.job import JobRepository
from app.repositories.job_duplicate import JobDuplicateRepository
from app.repositories.job_embedding import JobEmbeddingRepository
from app.repositories.job_match import JobMatchRepository
from app.repositories.job_requirements import JobRequirementsRepository
from app.repositories.monitoring_run import MonitoringRunRepository
from app.repositories.skill import SkillRepository
from app.repositories.user import UserRepository

from app.repositories.notification import NotificationRepository
from app.repositories.notification_delivery import NotificationDeliveryRepository
from app.repositories.notification_preference import NotificationPreferenceRepository

__all__ = [
    "CompanyRepository",
    "CareerSourceRepository",
    "JobRepository",
    "JobRequirementsRepository",
    "JobMatchRepository",
    "AIJobExtractionRepository",
    "JobEmbeddingRepository",
    "CandidateEmbeddingRepository",
    "AIExplanationRepository",
    "JobDuplicateRepository",
    "MonitoringRunRepository",
    "UserRepository",
    "CandidateProfileRepository",
    "SkillRepository",
    "CandidateSkillRepository",
    "ExperienceRepository",
    "EducationRepository",
    "CandidatePreferencesRepository",
    "NotificationPreferenceRepository",
    "NotificationRepository",
    "NotificationDeliveryRepository",
]
