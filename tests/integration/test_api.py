"""Integration tests for the API endpoints."""
import pytest
from fastapi import status


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"


class TestUserEndpoints:
    """Tests for user API endpoints."""

    def test_create_user(self, client, sample_user_data):
        """Test creating a new user."""
        response = client.post("/api/v1/users/", json=sample_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned

    def test_create_user_duplicate_email(self, client, sample_user_data):
        """Test creating user with duplicate email fails."""
        client.post("/api/v1/users/", json=sample_user_data)
        response = client.post("/api/v1/users/", json=sample_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_get_user(self, client, sample_user_data):
        """Test getting a user by ID."""
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == user_id

    def test_get_user_not_found(self, client):
        """Test getting non-existent user returns 404."""
        response = client.get("/api/v1/users/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_users(self, client, sample_user_data):
        """Test listing all users."""
        client.post("/api/v1/users/", json=sample_user_data)
        response = client.get("/api/v1/users/")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_update_user(self, client, sample_user_data):
        """Test updating a user."""
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        update_data = {"full_name": "Updated Name"}
        response = client.patch(f"/api/v1/users/{user_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["full_name"] == "Updated Name"

    def test_delete_user(self, client, sample_user_data):
        """Test deleting a user."""
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify user is deleted
        get_response = client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestTaskEndpoints:
    """Tests for task API endpoints."""

    @pytest.fixture
    def created_user(self, client, sample_user_data):
        """Create a user and return their ID."""
        response = client.post("/api/v1/users/", json=sample_user_data)
        return response.json()["id"]

    def test_create_task(self, client, created_user, sample_task_data):
        """Test creating a new task."""
        response = client.post(
            f"/api/v1/users/{created_user}/tasks/",
            json=sample_task_data
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == sample_task_data["title"]
        assert data["status"] == "pending"
        assert data["owner_id"] == created_user

    def test_create_task_for_nonexistent_user(self, client, sample_task_data):
        """Test creating task for non-existent user fails."""
        response = client.post("/api/v1/users/99999/tasks/", json=sample_task_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_task(self, client, created_user, sample_task_data):
        """Test getting a task by ID."""
        create_response = client.post(
            f"/api/v1/users/{created_user}/tasks/",
            json=sample_task_data
        )
        task_id = create_response.json()["id"]

        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == task_id

    def test_list_user_tasks(self, client, created_user, sample_task_data):
        """Test listing tasks for a user."""
        client.post(f"/api/v1/users/{created_user}/tasks/", json=sample_task_data)

        response = client.get(f"/api/v1/users/{created_user}/tasks/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert len(data["tasks"]) >= 1

    def test_update_task(self, client, created_user, sample_task_data):
        """Test updating a task."""
        create_response = client.post(
            f"/api/v1/users/{created_user}/tasks/",
            json=sample_task_data
        )
        task_id = create_response.json()["id"]

        update_data = {"title": "Updated Title", "priority": 5}
        response = client.patch(f"/api/v1/tasks/{task_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Updated Title"
        assert response.json()["priority"] == 5

    def test_complete_task(self, client, created_user, sample_task_data):
        """Test marking a task as completed."""
        create_response = client.post(
            f"/api/v1/users/{created_user}/tasks/",
            json=sample_task_data
        )
        task_id = create_response.json()["id"]

        response = client.post(f"/api/v1/tasks/{task_id}/complete")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "completed"

    def test_delete_task(self, client, created_user, sample_task_data):
        """Test deleting a task."""
        create_response = client.post(
            f"/api/v1/users/{created_user}/tasks/",
            json=sample_task_data
        )
        task_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_tasks_by_status(self, client, created_user, sample_task_data):
        """Test filtering tasks by status."""
        # Create and complete a task
        create_response = client.post(
            f"/api/v1/users/{created_user}/tasks/",
            json=sample_task_data
        )
        task_id = create_response.json()["id"]
        client.post(f"/api/v1/tasks/{task_id}/complete")

        # Create another pending task
        client.post(f"/api/v1/users/{created_user}/tasks/", json=sample_task_data)

        # Filter by completed
        response = client.get(
            f"/api/v1/users/{created_user}/tasks/",
            params={"status_filter": "completed"}
        )
        assert response.status_code == status.HTTP_200_OK
        tasks = response.json()["tasks"]
        assert all(t["status"] == "completed" for t in tasks)
