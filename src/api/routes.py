"""FastAPI route definitions."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models.user import User
from src.models.task import Task, TaskStatus
from src.services.user_service import UserService
from src.services.task_service import TaskService
from src.api.schemas import (
    UserCreate, UserUpdate, UserResponse,
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    user_to_response, task_to_response
)

router = APIRouter()


# ============== User Endpoints ==============

@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    service = UserService(db)

    # Check if user already exists
    if service.get_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    if service.get_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    db_user = service.create(user)
    return user_to_response(db_user)


@router.get("/users/", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all users with pagination."""
    service = UserService(db)
    users = service.get_all(skip=skip, limit=limit)
    return [user_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a user by ID."""
    service = UserService(db)
    user = service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user_to_response(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user."""
    service = UserService(db)
    user = service.update(user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user_to_response(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user."""
    service = UserService(db)
    if not service.delete(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# ============== Task Endpoints ==============

@router.post("/users/{user_id}/tasks/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(user_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task for a user."""
    user_service = UserService(db)
    if not user_service.get_by_id(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    task_service = TaskService(db)
    db_task = task_service.create(task, owner_id=user_id)
    return task_to_response(db_task)


@router.get("/users/{user_id}/tasks/", response_model=TaskListResponse)
def list_user_tasks(
    user_id: int,
    status_filter: Optional[TaskStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List tasks for a user with optional status filter."""
    user_service = UserService(db)
    if not user_service.get_by_id(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    task_service = TaskService(db)
    skip = (page - 1) * per_page
    tasks, total = task_service.get_by_owner(
        owner_id=user_id,
        status_filter=status_filter,
        skip=skip,
        limit=per_page
    )

    return TaskListResponse(
        tasks=[task_to_response(t) for t in tasks],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a task by ID."""
    task_service = TaskService(db)
    task = task_service.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task_to_response(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task."""
    task_service = TaskService(db)
    task = task_service.update(task_id, task_update)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task_to_response(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    task_service = TaskService(db)
    if not task_service.delete(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    """Mark a task as completed."""
    task_service = TaskService(db)
    task = task_service.mark_completed(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task_to_response(task)


# ============== Health Check ==============

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
