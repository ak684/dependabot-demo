"""Unit tests for Pydantic schemas.

CRITICAL: These tests use Pydantic v1 features that WILL BREAK in v2:
- .dict() method -> becomes .model_dump()
- .parse_obj() method -> becomes .model_validate()
- from_orm() method -> becomes model_validate()
- @validator decorator -> becomes @field_validator
- class Config with orm_mode -> becomes model_config with from_attributes
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from src.api.schemas import (
    UserCreate, UserUpdate, UserInDB, UserResponse,
    TaskCreate, TaskUpdate, TaskInDB, TaskResponse,
    user_to_response, task_to_response
)
from src.models.task import TaskStatus


class TestUserSchemas:
    """Tests for user schemas."""

    def test_user_create_valid(self):
        """Test creating a valid user."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="password123"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"

    def test_user_create_password_validation(self):
        """Test password must contain a number."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="nodigitshere"
            )
        assert "Password must contain at least one number" in str(exc_info.value)

    def test_user_create_invalid_email(self):
        """Test invalid email format is rejected."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                username="testuser",
                password="password123"
            )

    def test_user_create_username_too_short(self):
        """Test username minimum length."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",  # Less than 3 chars
                password="password123"
            )

    def test_user_update_partial(self):
        """Test partial user update."""
        update = UserUpdate(full_name="New Name")

        # Using Pydantic v1's .dict() - WILL BREAK in v2
        update_dict = update.dict(exclude_unset=True)
        assert update_dict == {"full_name": "New Name"}

    def test_user_in_db_dict_conversion(self):
        """Test UserInDB can convert to dict.

        Uses .dict() which is v1 syntax - WILL BREAK in v2
        """
        user = UserInDB(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow()
        )

        # This uses v1's .dict() method - breaks in v2
        user_dict = user.dict()
        assert "id" in user_dict
        assert "email" in user_dict
        assert user_dict["is_active"] is True

    def test_user_in_db_dict_exclude(self):
        """Test dict() with exclude parameter.

        Uses .dict(exclude=...) which is v1 syntax
        """
        user = UserInDB(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow()
        )

        # v1 syntax for excluding fields
        user_dict = user.dict(exclude={"is_superuser"})
        assert "is_superuser" not in user_dict


class TestTaskSchemas:
    """Tests for task schemas."""

    def test_task_create_valid(self):
        """Test creating a valid task."""
        task = TaskCreate(
            title="Test Task",
            description="A test task",
            priority=3
        )
        assert task.title == "Test Task"
        assert task.priority == 3

    def test_task_create_priority_bounds(self):
        """Test task priority must be 1-5."""
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", priority=6)

        with pytest.raises(ValidationError):
            TaskCreate(title="Test", priority=0)

    def test_task_update_to_dict(self):
        """Test TaskUpdate converts to dict properly.

        Uses v1's .dict() method - WILL BREAK in v2
        """
        update = TaskUpdate(
            status=TaskStatus.IN_PROGRESS,
            priority=5
        )

        # v1 syntax
        update_dict = update.dict(exclude_unset=True)
        assert update_dict["status"] == TaskStatus.IN_PROGRESS
        assert update_dict["priority"] == 5

    def test_task_in_db_dict_conversion(self):
        """Test TaskInDB dict conversion.

        Uses .dict() which is v1 syntax - WILL BREAK in v2
        """
        task = TaskInDB(
            id=1,
            title="Test Task",
            description="Description",
            status=TaskStatus.PENDING,
            priority=2,
            owner_id=1,
            created_at=datetime.utcnow()
        )

        # v1 syntax - .dict() becomes .model_dump() in v2
        task_dict = task.dict()
        assert task_dict["id"] == 1
        assert task_dict["status"] == "pending"  # use_enum_values=True

    def test_task_in_db_json_conversion(self):
        """Test TaskInDB JSON conversion.

        Uses .json() which changes behavior in v2
        """
        task = TaskInDB(
            id=1,
            title="Test Task",
            status=TaskStatus.COMPLETED,
            priority=1,
            owner_id=1,
            created_at=datetime.utcnow()
        )

        # v1 syntax
        json_str = task.json()
        assert '"status":"completed"' in json_str or '"status": "completed"' in json_str


class TestSchemaHelpers:
    """Tests for schema helper functions."""

    def test_user_to_response_uses_dict(self):
        """Test user_to_response uses Pydantic v1 methods."""
        # Create a mock user-like object
        class MockUser:
            id = 1
            email = "test@example.com"
            username = "testuser"
            full_name = "Test User"
            is_active = True
            is_superuser = False
            created_at = datetime.utcnow()
            updated_at = None

        result = user_to_response(MockUser())
        assert isinstance(result, dict)
        assert result["email"] == "test@example.com"

    def test_task_to_response_uses_dict(self):
        """Test task_to_response uses Pydantic v1 methods."""
        class MockTask:
            id = 1
            title = "Test Task"
            description = "Test"
            status = TaskStatus.PENDING
            priority = 1
            owner_id = 1
            created_at = datetime.utcnow()
            updated_at = None
            due_date = None

        result = task_to_response(MockTask())
        assert isinstance(result, dict)
        assert result["title"] == "Test Task"


class TestConfigOrmMode:
    """Tests that specifically rely on orm_mode Config.

    These will fail in Pydantic v2 where orm_mode becomes from_attributes
    """

    def test_user_from_orm_creates_model(self):
        """Test UserInDB.from_orm() works.

        from_orm() is v1 syntax - becomes model_validate() in v2
        """
        class MockUser:
            id = 1
            email = "orm@test.com"
            username = "ormuser"
            full_name = "ORM User"
            is_active = True
            is_superuser = False
            created_at = datetime.utcnow()
            updated_at = None

        # v1 syntax - .from_orm() becomes .model_validate() in v2
        user = UserInDB.from_orm(MockUser())
        assert user.email == "orm@test.com"

    def test_task_from_orm_creates_model(self):
        """Test TaskInDB.from_orm() works."""
        class MockTask:
            id = 1
            title = "ORM Task"
            description = "From ORM"
            status = TaskStatus.IN_PROGRESS
            priority = 4
            owner_id = 1
            created_at = datetime.utcnow()
            updated_at = None
            due_date = None

        # v1 syntax
        task = TaskInDB.from_orm(MockTask())
        assert task.title == "ORM Task"
        assert task.status == TaskStatus.IN_PROGRESS


class TestParseObj:
    """Tests using parse_obj which changes in v2."""

    def test_user_parse_obj(self):
        """Test UserCreate.parse_obj().

        parse_obj() is v1 syntax - becomes model_validate() in v2
        """
        data = {
            "email": "parse@test.com",
            "username": "parseuser",
            "password": "password123"
        }

        # v1 syntax
        user = UserCreate.parse_obj(data)
        assert user.email == "parse@test.com"

    def test_task_parse_obj(self):
        """Test TaskCreate.parse_obj()."""
        data = {
            "title": "Parsed Task",
            "description": "Created via parse_obj",
            "priority": 2
        }

        # v1 syntax
        task = TaskCreate.parse_obj(data)
        assert task.title == "Parsed Task"
