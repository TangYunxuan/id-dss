"""
LLM API router - endpoints for AI-powered instructional design features.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import Session as SessionModel, DesignStep, DesignStepCreate, AIRecommendation
from app.services.llm import (
    generate_objective_analysis,
    generate_activity_suggestions,
    generate_assessment_recommendations,
)
from app.config import settings
import json

router = APIRouter(prefix="/llm", tags=["llm"])


# ============================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================

class ObjectiveAnalysisRequest(BaseModel):
    session_id: int
    objectives: str


class ActivitySuggestionRequest(BaseModel):
    session_id: int
    objectives: str


class AssessmentRecommendationRequest(BaseModel):
    session_id: int
    objectives: str
    activities: str


class LLMResponse(BaseModel):
    success: bool
    step_id: int
    recommendation_id: int
    data: dict


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/analyze-objectives", response_model=LLMResponse)
async def analyze_objectives(
    request: ObjectiveAnalysisRequest,
    db: Session = Depends(get_session),
) -> LLMResponse:
    """
    Analyze learning objectives using AI.
    Creates a DesignStep and AIRecommendation record.
    """
    # Verify session exists
    session = db.get(SessionModel, request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {request.session_id} not found",
        )
    
    # Check if API key is configured
    if settings.LLM_PROVIDER.value == "openai" and not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY in .env file.",
        )
    if settings.LLM_PROVIDER.value == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env file.",
        )
    if settings.LLM_PROVIDER.value == "gemini" and not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key not configured. Set GEMINI_API_KEY in .env file.",
        )
    
    try:
        # Call LLM
        result = await generate_objective_analysis(
            course_title=session.course_title,
            level=session.level,
            modality=session.modality,
            objectives=request.objectives,
            constraints=session.constraints,
        )
        
        # Create design step
        step = DesignStep(
            session_id=request.session_id,
            phase="objective-analysis",
            user_input=request.objectives,
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        
        # Create AI recommendation
        recommendation = AIRecommendation(
            step_id=step.id,
            phase="objective-analysis",
            raw_response=json.dumps(result),
        )
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        
        return LLMResponse(
            success=True,
            step_id=step.id,
            recommendation_id=recommendation.id,
            data=result,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM request failed: {str(e)}",
        )


@router.post("/suggest-activities", response_model=LLMResponse)
async def suggest_activities(
    request: ActivitySuggestionRequest,
    db: Session = Depends(get_session),
) -> LLMResponse:
    """
    Generate activity suggestions using AI.
    Creates a DesignStep and AIRecommendation record.
    """
    # Verify session exists
    session = db.get(SessionModel, request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {request.session_id} not found",
        )
    
    # Check if API key is configured
    if settings.LLM_PROVIDER.value == "openai" and not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY in .env file.",
        )
    if settings.LLM_PROVIDER.value == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env file.",
        )
    if settings.LLM_PROVIDER.value == "gemini" and not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key not configured. Set GEMINI_API_KEY in .env file.",
        )
    
    try:
        # Call LLM
        result = await generate_activity_suggestions(
            course_title=session.course_title,
            level=session.level,
            modality=session.modality,
            objectives=request.objectives,
            constraints=session.constraints,
        )
        
        # Create design step
        step = DesignStep(
            session_id=request.session_id,
            phase="activity-suggestion",
            user_input=request.objectives,
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        
        # Create AI recommendation
        recommendation = AIRecommendation(
            step_id=step.id,
            phase="activity-suggestion",
            raw_response=json.dumps(result),
        )
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        
        return LLMResponse(
            success=True,
            step_id=step.id,
            recommendation_id=recommendation.id,
            data=result,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM request failed: {str(e)}",
        )


@router.post("/recommend-assessments", response_model=LLMResponse)
async def recommend_assessments(
    request: AssessmentRecommendationRequest,
    db: Session = Depends(get_session),
) -> LLMResponse:
    """
    Generate assessment recommendations using AI.
    Creates a DesignStep and AIRecommendation record.
    """
    # Verify session exists
    session = db.get(SessionModel, request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {request.session_id} not found",
        )
    
    # Check if API key is configured
    if settings.LLM_PROVIDER.value == "openai" and not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY in .env file.",
        )
    if settings.LLM_PROVIDER.value == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env file.",
        )
    if settings.LLM_PROVIDER.value == "gemini" and not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key not configured. Set GEMINI_API_KEY in .env file.",
        )
    
    try:
        # Call LLM
        result = await generate_assessment_recommendations(
            course_title=session.course_title,
            level=session.level,
            modality=session.modality,
            objectives=request.objectives,
            activities=request.activities,
            constraints=session.constraints,
        )
        
        # Create design step
        step = DesignStep(
            session_id=request.session_id,
            phase="assessment-recommendation",
            user_input=f"Objectives:\n{request.objectives}\n\nActivities:\n{request.activities}",
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        
        # Create AI recommendation
        recommendation = AIRecommendation(
            step_id=step.id,
            phase="assessment-recommendation",
            raw_response=json.dumps(result),
        )
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        
        return LLMResponse(
            success=True,
            step_id=step.id,
            recommendation_id=recommendation.id,
            data=result,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM request failed: {str(e)}",
        )


@router.get("/status")
async def llm_status():
    """Check LLM configuration status."""
    provider = settings.LLM_PROVIDER.value
    
    if provider == "openai":
        configured = bool(settings.OPENAI_API_KEY)
        model = settings.OPENAI_MODEL
    elif provider == "anthropic":
        configured = bool(settings.ANTHROPIC_API_KEY)
        model = settings.ANTHROPIC_MODEL
    elif provider == "gemini":
        configured = bool(settings.GEMINI_API_KEY)
        model = settings.GEMINI_MODEL
    else:
        configured = False
        model = "unknown"
    
    return {
        "provider": provider,
        "model": model,
        "configured": configured,
        "message": "Ready" if configured else (
            "Set GEMINI_API_KEY in .env file" if provider == "gemini" else f"Set {provider.upper()}_API_KEY in .env file"
        ),
    }


@router.get("/gemini/models")
async def gemini_models():
    """
    List Gemini models available for the configured API key.
    Helpful when a model name is not found / not supported.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key not configured. Set GEMINI_API_KEY in your environment variables.",
        )

    try:
        import google.generativeai as genai
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"google-generativeai import failed: {str(e)}",
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)
    out = []
    for m in list(genai.list_models()):
        name = getattr(m, "name", "") or ""
        if name.startswith("models/"):
            name = name.split("/", 1)[1]
        out.append(
            {
                "name": name,
                "display_name": getattr(m, "display_name", None),
                "supported_generation_methods": getattr(m, "supported_generation_methods", None),
            }
        )

    return {
        "configured_model": settings.GEMINI_MODEL,
        "models": out,
        "generate_content_models": [x for x in out if x.get("supported_generation_methods") and "generateContent" in x["supported_generation_methods"]],
    }


