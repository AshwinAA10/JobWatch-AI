"""Repository for Company data access operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.company import CompanyCreate


class CompanyRepository:
    """Data access repository for Company entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, company_in: CompanyCreate) -> Company:
        """Create and persist a new Company."""
        company = Company(
            name=company_in.name,
            slug=company_in.slug,
            website_url=company_in.website_url,
            description=company_in.description,
            is_active=company_in.is_active,
        )
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def get_by_id(self, company_id: UUID) -> Optional[Company]:
        """Fetch a single company by its primary key ID."""
        return self.db.get(Company, company_id)

    def get_by_slug(self, slug: str) -> Optional[Company]:
        """Fetch a company by unique slug."""
        stmt = select(Company).where(Company.slug == slug)
        return self.db.scalars(stmt).first()

    def list_active(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """List active companies ordered by name."""
        stmt = (
            select(Company)
            .where(Company.is_active.is_(True))
            .order_by(Company.name)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """List all companies with pagination."""
        stmt = select(Company).order_by(Company.name).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
