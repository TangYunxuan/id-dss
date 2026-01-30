"""
Sessions API router - manage design sessions.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import Session as SessionModel, SessionCreate, SessionRead
from pydantic import BaseModel

router = APIRouter(prefix="/sessions", tags=["sessions"])

class SessionUpdate(BaseModel):
    course_title: Optional[str] = None
    level: Optional[str] = None
    modality: Optional[str] = None
    constraints: Optional[str] = None
    learning_objectives: Optional[str] = None


@router.post("/", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_session),
) -> SessionModel:
    """Create a new design session."""
    db_session = SessionModel.model_validate(session_data)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/", response_model=List[SessionRead])
def list_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session),
) -> List[SessionModel]:
    """List all design sessions."""
    statement = select(SessionModel).offset(skip).limit(limit)
    sessions = db.exec(statement).all()
    return sessions


@router.get("/{session_id}", response_model=SessionRead)
def get_session_by_id(
    session_id: int,
    db: Session = Depends(get_session),
) -> SessionModel:
    """Get a specific design session by ID."""
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found",
        )
    return session


@router.patch("/{session_id}", response_model=SessionRead)
def update_session(
    session_id: int,
    patch: SessionUpdate,
    db: Session = Depends(get_session),
) -> SessionModel:
    """Update an existing session (partial update)."""
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found",
        )

    data = patch.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(session, k, v)

    db.add(session)
    db.commit()
    db.refresh(session)
    return session

