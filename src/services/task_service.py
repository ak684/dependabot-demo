"""Task service for business logic."""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.task import Task, TaskStatus
from src.api.schemas import TaskCreate, TaskUpdate


class TaskService:
    """Service class for task operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_by_owner(
        self,
        owner_id: int,
        status_filter: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Task], int]:
        """Get tasks by owner with optional status filter."""
        query = self.db.query(Task).filter(Task.owner_id == owner_id)

        if status_filter:
            query = query.filter(Task.status == status_filter)

        total = query.count()
        tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()

        return tasks, total

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get all tasks with pagination."""
        return self.db.query(Task).offset(skip).limit(limit).all()

    def create(self, task_data: TaskCreate, owner_id: int) -> Task:
        """Create a new task."""
        # Using Pydantic v1's .dict() - WILL BREAK in v2
        task_dict = task_data.dict()

        db_task = Task(
            **task_dict,
            owner_id=owner_id,
            status=TaskStatus.PENDING
        )

        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def update(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """Update an existing task."""
        db_task = self.get_by_id(task_id)
        if not db_task:
            return None

        # Using Pydantic v1's .dict() - WILL BREAK in v2
        update_data = task_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_task, field, value)

        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def delete(self, task_id: int) -> bool:
        """Delete a task."""
        db_task = self.get_by_id(task_id)
        if not db_task:
            return False

        self.db.delete(db_task)
        self.db.commit()
        return True

    def mark_completed(self, task_id: int) -> Optional[Task]:
        """Mark a task as completed."""
        db_task = self.get_by_id(task_id)
        if not db_task:
            return None

        db_task.status = TaskStatus.COMPLETED
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def get_stats(self, owner_id: int) -> dict:
        """Get task statistics for a user."""
        query = self.db.query(
            Task.status,
            func.count(Task.id).label('count')
        ).filter(Task.owner_id == owner_id).group_by(Task.status)

        results = query.all()

        stats = {status.value: 0 for status in TaskStatus}
        for status, count in results:
            stats[status.value] = count

        return stats
