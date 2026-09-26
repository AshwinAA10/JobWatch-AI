"""Repository for User data access operations."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Data access repository for User entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        email: str,
        password_hash: str,
        is_active: bool = True,
        is_verified: bool = False,
    ) -> User:
        """Create and persist a new User."""
        user = User(
            email=email.strip().lower(),
            password_hash=password_hash,
            is_active=is_active,
            is_verified=is_verified,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Fetch a user by UUID primary key."""
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a user by normalized unique email."""
        stmt = select(User).where(User.email == email.strip().lower())
        return self.db.scalars(stmt).first()

    def update_last_login(self, user: User) -> User:
        """Update the last_login_at timestamp for a user."""
        user.last_login_at = datetime.now(timezone.utc)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        """Commit updates to a user entity."""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
