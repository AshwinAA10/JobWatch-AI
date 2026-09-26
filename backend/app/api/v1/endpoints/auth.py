"""Authentication and user session endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth import AuthService
from app.services.exceptions import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Creates a new candidate user account with an Argon2id hashed password.",
)
def register(
    register_in: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    auth_service = AuthService(db)
    try:
        user = auth_service.register(register_in)
        return UserResponse.model_validate(user)
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate User and Obtain JWT Token",
    description="Verifies user credentials and returns a short-lived signed JWT bearer token.",
)
def login(
    login_in: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate and issue JWT access token."""
    auth_service = AuthService(db)
    try:
        user = auth_service.authenticate(login_in.email, login_in.password)
        return auth_service.create_token_response(user)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current Authenticated User",
    description="Returns public identity details for the currently authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve identity of currently logged-in user."""
    return UserResponse.model_validate(current_user)
