"""Notification management and candidate alert endpoints."""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.notifications.exceptions import SSRFSecurityError
from app.notifications.service import NotificationService
from app.notifications.worker import NotificationDeliveryWorker
from app.repositories.notification import NotificationRepository
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
)
from app.services.profile import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Get Candidate Notification Preferences",
    description="Fetches alerting channels, match score thresholds, and frequency settings for the authenticated candidate.",
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferenceResponse:
    """Retrieve notification preferences for the logged-in candidate."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    notification_service = NotificationService(db)
    prefs = notification_service.get_preferences(profile.id)
    return NotificationPreferenceResponse.model_validate(prefs)


@router.put(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Update Candidate Notification Preferences",
    description="Configures notification delivery channels (email, webhook), threshold score, and frequency.",
)
def update_preferences(
    prefs_in: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferenceResponse:
    """Update notification preferences for the logged-in candidate."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    notification_service = NotificationService(db)
    try:
        updated = notification_service.update_preferences(profile.id, prefs_in)
        return NotificationPreferenceResponse.model_validate(updated)
    except SSRFSecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook URL: {str(exc)}",
        )
    except Exception as exc:
        logger.exception("notification.preferences.update_failed profile_id=%s", profile.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List Candidate Notifications",
    description="Returns a paginated list of notification events for the authenticated candidate.",
)
def list_notifications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (PENDING, SENT, FAILED)"),
    event_type: Optional[str] = Query(None, description="Filter by event type (NEW_MATCH, HIGH_QUALITY_MATCH)"),
    unread_only: bool = Query(False, description="Filter unread notifications only"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    """List notifications with pagination and filtering for authenticated user."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    repo = NotificationRepository(db)
    items, total, unread_count = repo.list_for_profile(
        profile_id=profile.id,
        status=status_filter,
        event_type=event_type,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
        unread_count=unread_count,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Get Notification Detail",
    description="Retrieves a specific notification record and delivery audit attempts.",
)
def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """Retrieve a single notification record with authorization isolation."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    repo = NotificationRepository(db)
    notification = repo.get_by_id(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    # Candidate isolation check
    if notification.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this notification",
        )

    return NotificationResponse.model_validate(notification)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark Notification as Read",
    description="Marks a single notification as read for the authenticated candidate.",
)
def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """Mark a notification as read."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    repo = NotificationRepository(db)
    notification = repo.get_by_id(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if notification.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this notification",
        )

    updated = repo.mark_as_read(notification_id)
    return NotificationResponse.model_validate(updated)


@router.post(
    "/read-all",
    summary="Mark All Notifications as Read",
    description="Marks all unread notifications as read for the authenticated candidate.",
)
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Mark all unread notifications as read for the current candidate."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    repo = NotificationRepository(db)
    count = repo.mark_all_as_read(profile.id)
    return {"marked_read": count}


@router.post(
    "/deliveries/process",
    summary="Process Pending Notification Deliveries",
    description="Scans and executes pending or retryable channel deliveries.",
)
def process_deliveries(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Trigger background delivery processing for pending/retryable alerts."""
    worker = NotificationDeliveryWorker(db)
    processed = worker.process_pending_deliveries(limit=limit)
    return {"status": "ok", "delivered_count": processed}
