"""Repository for CareerSource data access operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.career_source import CareerSource
from app.schemas.career_source import CareerSourceCreate


class CareerSourceRepository:
    """Data access repository for CareerSource entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, source_in: CareerSourceCreate) -> CareerSource:
        """Create and persist a new CareerSource."""
        source = CareerSource(
            company_id=source_in.company_id,
            name=source_in.name,
            source_type=source_in.source_type,
            base_url=source_in.base_url,
            is_active=source_in.is_active,
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def get_by_id(self, source_id: UUID) -> Optional[CareerSource]:
        """Fetch a single CareerSource by ID."""
        return self.db.get(CareerSource, source_id)

    def list_by_company(
        self,
        company_id: UUID,
        is_active: Optional[bool] = None,
    ) -> List[CareerSource]:
        """List career sources associated with a company."""
        stmt = select(CareerSource).where(CareerSource.company_id == company_id)
        if is_active is not None:
            stmt = stmt.where(CareerSource.is_active.is_(is_active))
        stmt = stmt.order_by(CareerSource.name)
        return list(self.db.scalars(stmt).all())
