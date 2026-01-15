"""Unit tests for service layer.

These tests exercise the Pydantic .dict() method used in services,
which will break when upgrading from Pydantic v1 to v2.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.user import User
from src.models.task import Task, TaskStatus
from src.services.user_service import UserService
from src.services.task_service import TaskService
from src.api.schemas import UserCreate, UserUpdate, TaskCreate, TaskUpdate


# In-memory database for unit tests
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestUserService:
    """Tests for UserService."""

    def test_create_user(self, db):
        """Test creating a user via service."""
        service = UserService(db)
        user_data = UserCreate(
            email="service@test.com",
            username="serviceuser",
            password="password123"
        )

        user = service.create(user_data)
        assert user.id is not None
        assert user.email == "service@test.com"
        assert user.hashed_password != "password123"  # Should be hashed

    def test_get_user_by_id(self, db):
        """Test getting user by ID."""
        service = UserService(db)
        user_data = UserCreate(
            email="get@test.com",
            username="getuser",
            password="password123"
        )
        created = service.create(user_data)

        found = service.get_by_id(created.id)
        assert found is not None
        assert found.email == "get@test.com"

    def test_get_user_by_email(self, db):
        """Test getting user by email."""
        service = UserService(db)
        user_data = UserCreate(
            email="email@test.com",
            username="emailuser",
            password="password123"
        )
        service.create(user_data)

        found = service.get_by_email("email@test.com")
        assert found is not None
        assert found.username == "emailuser"

    def test_update_user_uses_dict(self, db):
        """Test updating user uses Pydantic .dict().

        The service calls user_data.dict(exclude_unset=True)
        which is v1 syntax and will break in v2.
        """
        service = UserService(db)
        user_data = UserCreate(
            email="update@test.com",
            username="updateuser",
            password="password123"
        )
        created = service.create(user_data)

        update_data = UserUpdate(full_name="Updated Full Name")
        updated = service.update(created.id, update_data)

        assert updated is not None
        assert updated.full_name == "Updated Full Name"
        assert updated.email == "update@test.com"  # Unchanged

    def test_authenticate_user(self, db):
        """Test user authentication."""
        service = UserService(db)
        user_data = UserCreate(
            email="auth@test.com",
            username="authuser",
            password="password123"
        )
        service.create(user_data)

        # Valid authentication
        user = service.authenticate("authuser", "password123")
        assert user is not None
        assert user.email == "auth@test.com"

        # Invalid password
        user = service.authenticate("authuser", "wrongpassword")
        assert user is None

    def test_delete_user(self, db):
        """Test deleting a user."""
        service = UserService(db)
        user_data = UserCreate(
            email="delete@test.com",
            username="deleteuser",
            password="password123"
        )
        created = service.create(user_data)

        result = service.delete(created.id)
        assert result is True

        found = service.get_by_id(created.id)
        assert found is None


class TestTaskService:
    """Tests for TaskService."""

    @pytest.fixture
    def user(self, db):
        """Create a user for task tests."""
        service = UserService(db)
        user_data = UserCreate(
            email="taskowner@test.com",
            username="taskowner",
            password="password123"
        )
        return service.create(user_data)

    def test_create_task_uses_dict(self, db, user):
        """Test creating task uses Pydantic .dict().

        The service calls task_data.dict() which is v1 syntax.
        """
        service = TaskService(db)
        task_data = TaskCreate(
            title="Test Task",
            description="A test task",
            priority=3
        )

        task = service.create(task_data, owner_id=user.id)
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING

    def test_update_task_uses_dict(self, db, user):
        """Test updating task uses Pydantic .dict().

        The service calls task_data.dict(exclude_unset=True)
        which will break in Pydantic v2.
        """
        service = TaskService(db)
        task_data = TaskCreate(title="Original Title", priority=1)
        created = service.create(task_data, owner_id=user.id)

        update_data = TaskUpdate(title="Updated Title", priority=5)
        updated = service.update(created.id, update_data)

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.priority == 5

    def test_get_tasks_by_owner(self, db, user):
        """Test getting tasks by owner."""
        service = TaskService(db)

        # Create multiple tasks
        for i in range(5):
            task_data = TaskCreate(title=f"Task {i}", priority=i % 5 + 1)
            service.create(task_data, owner_id=user.id)

        tasks, total = service.get_by_owner(owner_id=user.id)
        assert total == 5
        assert len(tasks) == 5

    def test_get_tasks_with_status_filter(self, db, user):
        """Test filtering tasks by status."""
        service = TaskService(db)

        # Create tasks with different statuses
        task1 = service.create(TaskCreate(title="Task 1"), owner_id=user.id)
        task2 = service.create(TaskCreate(title="Task 2"), owner_id=user.id)
        service.mark_completed(task1.id)

        # Filter by pending
        tasks, total = service.get_by_owner(
            owner_id=user.id,
            status_filter=TaskStatus.PENDING
        )
        assert total == 1
        assert tasks[0].title == "Task 2"

    def test_mark_completed(self, db, user):
        """Test marking task as completed."""
        service = TaskService(db)
        task_data = TaskCreate(title="Complete Me", priority=1)
        created = service.create(task_data, owner_id=user.id)

        completed = service.mark_completed(created.id)
        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED

    def test_get_stats(self, db, user):
        """Test getting task statistics."""
        service = TaskService(db)

        # Create tasks with different statuses
        task1 = service.create(TaskCreate(title="Task 1"), owner_id=user.id)
        task2 = service.create(TaskCreate(title="Task 2"), owner_id=user.id)
        task3 = service.create(TaskCreate(title="Task 3"), owner_id=user.id)
        service.mark_completed(task1.id)
        service.mark_completed(task2.id)

        stats = service.get_stats(user.id)
        assert stats["completed"] == 2
        assert stats["pending"] == 1
