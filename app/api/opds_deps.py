import logging
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
from app.services.settings_service import SettingsService

security = HTTPBasic()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]


def get_current_user_opds(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
        db: SessionDep
) -> User:
    """
    Validates Basic Auth credentials for OPDS clients.
    Also checks if OPDS is globally enabled.
    """
    # 1. Check Global Setting
    settings_service = SettingsService(db)
    if not settings_service.get("server.opds_enabled"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPDS Support is disabled on this server."
        )

    # 2. Check User
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user:
        # OPDS clients need standard 401 to prompt for password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    # 3. Verify Password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user


# Dependency Alias
OPDSUser = Annotated[User, Depends(get_current_user_opds)]