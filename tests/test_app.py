"""
Tests for the Mergington High School Activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as _activities

ORIGINAL_ACTIVITIES = copy.deepcopy(_activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore in-memory activities to their original state before each test."""
    _activities.clear()
    _activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict(self, client):
        data = client.get("/activities").json()
        assert isinstance(data, dict)

    def test_contains_expected_activities(self, client):
        data = client.get("/activities").json()
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_has_required_fields(self, client):
        data = client.get("/activities").json()
        chess = data["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        data = client.get("/activities").json()
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]

    def test_duplicate_signup_returns_400(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 400

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Unknown Activity/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_signup_full_activity_returns_400(self, client):
        activity = _activities["Chess Club"]
        activity["participants"] = [
            f"student{i}@mergington.edu"
            for i in range(activity["max_participants"])
        ]
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "overflow@mergington.edu"},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"},
        )
        data = client.get("/activities").json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]

    def test_unregister_not_enrolled_returns_400(self, client):
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "nothere@mergington.edu"},
        )
        assert response.status_code == 400

    def test_unregister_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Unknown Activity/unregister",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 404
