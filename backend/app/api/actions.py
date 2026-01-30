"""
Actions API router - track user interactions with recommendations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import UserAction, UserActionCreate, UserActionRead
from app.models import DesignStep, AIRecommendation

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/", response_model=UserActionRead, status_code=status.HTTP_201_CREATED)
def create_action(
    action_data: UserActionCreate,
    db: Session = Depends(get_session),
) -> UserAction:
    """Create a new user action on a design step or recommendation."""
    # Verify step exists
    step = db.get(DesignStep, action_data.step_id)
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step with id {action_data.step_id} not found",
        )
    
    # Verify recommendation exists if provided
    if action_data.recommendation_id is not None:
        recommendation = db.get(AIRecommendation, action_data.recommendation_id)
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation with id {action_data.recommendation_id} not found",
            )
    
    db_action = UserAction.model_validate(action_data)
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action


@router.get("/", response_model=List[UserActionRead])
def list_actions(
    step_id: int = None,
    recommendation_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session),
) -> List[UserAction]:
    """List user actions, optionally filtered by step or recommendation."""
    statement = select(UserAction)
    if step_id is not None:
        statement = statement.where(UserAction.step_id == step_id)
    if recommendation_id is not None:
        statement = statement.where(UserAction.recommendation_id == recommendation_id)
    statement = statement.offset(skip).limit(limit)
    actions = db.exec(statement).all()
    return actions


@router.get("/{action_id}", response_model=UserActionRead)
def get_action_by_id(
    action_id: int,
    db: Session = Depends(get_session),
) -> UserAction:
    """Get a specific user action by ID."""
    action = db.get(UserAction, action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action with id {action_id} not found",
        )
    return action

