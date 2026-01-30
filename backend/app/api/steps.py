"""
Steps API router - manage design steps within sessions.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import DesignStep, DesignStepCreate, DesignStepRead
from app.models import Session as SessionModel

router = APIRouter(prefix="/steps", tags=["steps"])


@router.post("/", response_model=DesignStepRead, status_code=status.HTTP_201_CREATED)
def create_step(
    step_data: DesignStepCreate,
    db: Session = Depends(get_session),
) -> DesignStep:
    """Create a new design step for a session."""
    # Verify session exists
    session = db.get(SessionModel, step_data.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {step_data.session_id} not found",
        )
    
    db_step = DesignStep.model_validate(step_data)
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


@router.get("/", response_model=List[DesignStepRead])
def list_steps(
    session_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session),
) -> List[DesignStep]:
    """List design steps, optionally filtered by session."""
    statement = select(DesignStep)
    if session_id is not None:
        statement = statement.where(DesignStep.session_id == session_id)
    statement = statement.offset(skip).limit(limit)
    steps = db.exec(statement).all()
    return steps


@router.get("/{step_id}", response_model=DesignStepRead)
def get_step_by_id(
    step_id: int,
    db: Session = Depends(get_session),
) -> DesignStep:
    """Get a specific design step by ID."""
    step = db.get(DesignStep, step_id)
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step with id {step_id} not found",
        )
    return step

