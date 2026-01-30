"""
AIRecommendation model - stores AI-generated recommendations for design steps.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.design_step import DesignStep
    from app.models.user_action import UserAction


class AIRecommendationBase(SQLModel):
    """Base schema for AIRecommendation with shared attributes."""
    step_id: int = Field(foreign_key="design_steps.id", index=True)
    phase: str = Field(max_length=100)  # Phase this recommendation belongs to
    raw_response: str = Field(max_length=50000)  # JSON or text from LLM


class AIRecommendation(AIRecommendationBase, table=True):
    """AIRecommendation ORM model - stored in database."""
    __tablename__ = "ai_recommendations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    design_step: Optional["DesignStep"] = Relationship(back_populates="recommendations")
    user_actions: List["UserAction"] = Relationship(back_populates="recommendation")


class AIRecommendationCreate(SQLModel):
    """Schema for creating a new AI recommendation."""
    step_id: int
    phase: str
    raw_response: str


class AIRecommendationRead(AIRecommendationBase):
    """Schema for reading an AI recommendation."""
    id: int
    created_at: datetime

