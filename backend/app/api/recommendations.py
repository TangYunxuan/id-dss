"""
Recommendations API router - manage AI recommendations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import AIRecommendation, AIRecommendationCreate, AIRecommendationRead, DesignStep

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/", response_model=AIRecommendationRead, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    recommendation_data: AIRecommendationCreate,
    db: Session = Depends(get_session),
) -> AIRecommendation:
    """Create a new AI recommendation."""
    # Verify step exists
    step = db.get(DesignStep, recommendation_data.step_id)
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step with id {recommendation_data.step_id} not found",
        )
    
    db_recommendation = AIRecommendation.model_validate(recommendation_data)
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)
    return db_recommendation


@router.get("/", response_model=List[AIRecommendationRead])
def list_recommendations(
    step_id: int = None,
    phase: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session),
) -> List[AIRecommendation]:
    """List AI recommendations, optionally filtered by step or phase."""
    statement = select(AIRecommendation)
    if step_id is not None:
        statement = statement.where(AIRecommendation.step_id == step_id)
    if phase is not None:
        statement = statement.where(AIRecommendation.phase == phase)
    statement = statement.offset(skip).limit(limit)
    recommendations = db.exec(statement).all()
    return recommendations


@router.get("/{recommendation_id}", response_model=AIRecommendationRead)
def get_recommendation_by_id(
    recommendation_id: int,
    db: Session = Depends(get_session),
) -> AIRecommendation:
    """Get a specific AI recommendation by ID."""
    recommendation = db.get(AIRecommendation, recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with id {recommendation_id} not found",
        )
    return recommendation


