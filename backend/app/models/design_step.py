"""
DesignStep model - represents a step in the instructional design process.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.ai_recommendation import AIRecommendation
    from app.models.user_action import UserAction


class DesignStepBase(SQLModel):
    """Base schema for DesignStep with shared attributes."""
    session_id: int = Field(foreign_key="sessions.id", index=True)
    phase: str = Field(max_length=100)  # e.g., "analysis", "design", "development"
    user_input: Optional[str] = Field(default=None, max_length=10000)


class DesignStep(DesignStepBase, table=True):
    """DesignStep ORM model - stored in database."""
    __tablename__ = "design_steps"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    session: Optional["Session"] = Relationship(back_populates="design_steps")
    recommendations: List["AIRecommendation"] = Relationship(back_populates="design_step")
    user_actions: List["UserAction"] = Relationship(back_populates="design_step")


class DesignStepCreate(SQLModel):
    """Schema for creating a new design step."""
    session_id: int
    phase: str
    user_input: Optional[str] = None


class DesignStepRead(DesignStepBase):
    """Schema for reading a design step."""
    id: int
    created_at: datetime

