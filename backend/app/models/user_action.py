"""
UserAction model - tracks user interactions with AI recommendations.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.design_step import DesignStep
    from app.models.ai_recommendation import AIRecommendation


class UserActionBase(SQLModel):
    """Base schema for UserAction with shared attributes."""
    step_id: int = Field(foreign_key="design_steps.id", index=True)
    recommendation_id: Optional[int] = Field(
        default=None, foreign_key="ai_recommendations.id", index=True
    )
    action_type: str = Field(max_length=50)  # e.g., "accept", "reject", "edit", "comment"
    edited_content: Optional[str] = Field(default=None, max_length=50000)
    comment: Optional[str] = Field(default=None, max_length=5000)


class UserAction(UserActionBase, table=True):
    """UserAction ORM model - stored in database."""
    __tablename__ = "user_actions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    design_step: Optional["DesignStep"] = Relationship(back_populates="user_actions")
    recommendation: Optional["AIRecommendation"] = Relationship(back_populates="user_actions")


class UserActionCreate(SQLModel):
    """Schema for creating a new user action."""
    step_id: int
    recommendation_id: Optional[int] = None
    action_type: str
    edited_content: Optional[str] = None
    comment: Optional[str] = None


class UserActionRead(UserActionBase):
    """Schema for reading a user action."""
    id: int
    created_at: datetime

