"""
Session model - represents a design session for a course.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.design_step import DesignStep


class SessionBase(SQLModel):
    """Base schema for Session with shared attributes."""
    course_title: str = Field(index=True, max_length=255)
    level: str = Field(max_length=100)  # e.g., "undergraduate", "graduate", "professional"
    modality: str = Field(max_length=100)  # e.g., "online", "in-person", "hybrid"
    constraints: Optional[str] = Field(default=None, max_length=2000)  # JSON or text
    learning_objectives: Optional[str] = Field(default=None, max_length=8000)


class Session(SessionBase, table=True):
    """Session ORM model - stored in database."""
    __tablename__ = "sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    design_steps: List["DesignStep"] = Relationship(back_populates="session")


class SessionCreate(SessionBase):
    """Schema for creating a new session."""
    pass


class SessionRead(SessionBase):
    """Schema for reading a session."""
    id: int
    created_at: datetime

