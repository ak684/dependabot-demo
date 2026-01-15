"""Pydantic schemas for API request/response validation.

IMPORTANT: This file uses Pydantic v1 syntax intentionally.
When Dependabot upgrades to Pydantic v2, the following will break:
- `class Config:` -> should be `model_config = ConfigDict(...)`
- `.dict()` method -> should be `.model_dump()`
- `.parse_obj()` -> should be `.model_validate()`
- `@validator` -> should be `@field_validator`
- `orm_mode` -> should be `from_attributes`
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator, Field

from src.models.task import TaskStatus


# ============== User Schemas ==============

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8)

    # Pydantic v1 validator syntax - WILL BREAK in v2
    @validator('password')
    def password_strength(cls, v):
        """Validate password has at least one number."""
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """User schema as stored in database."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Pydantic v1 Config class - WILL BREAK in v2
    class Config:
        orm_mode = True  # This becomes `from_attributes = True` in v2


class UserResponse(UserInDB):
    """User response schema (excludes sensitive data)."""
    pass


# ============== Task Schemas ==============

class TaskBase(BaseModel):
    """Base task schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[datetime] = None


class TaskInDB(TaskBase):
    """Task schema as stored in database."""
    id: int
    status: TaskStatus
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Pydantic v1 Config class - WILL BREAK in v2
    class Config:
        orm_mode = True
        use_enum_values = True  # This also changes in v2


class TaskResponse(TaskInDB):
    """Task response schema."""
    pass


class TaskListResponse(BaseModel):
    """Response schema for list of tasks."""
    tasks: List[TaskResponse]
    total: int
    page: int
    per_page: int


# ============== Auth Schemas ==============

class Token(BaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    scopes: List[str] = []


# ============== Utility Functions ==============

def user_to_response(user_obj) -> dict:
    """Convert SQLAlchemy User to response dict.

    Uses Pydantic v1's .dict() method - WILL BREAK in v2
    Should be .model_dump() in v2
    """
    user_schema = UserInDB.from_orm(user_obj)  # v1 syntax
    return user_schema.dict(exclude_unset=True)  # v1 syntax - breaks in v2


def task_to_response(task_obj) -> dict:
    """Convert SQLAlchemy Task to response dict.

    Uses Pydantic v1's .dict() method - WILL BREAK in v2
    """
    task_schema = TaskInDB.from_orm(task_obj)  # v1 syntax
    return task_schema.dict()  # v1 syntax - breaks in v2
