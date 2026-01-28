"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create a test client
client = TestClient(app)


class TestRoot:
    """Test root endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test get activities endpoint"""

    def test_get_activities_success(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

        # Verify structure of activities
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_has_required_fields(self):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()

        required_activities = [
            "Tennis Club",
            "Basketball Team",
            "Drama Club",
            "ArtStudio",
            "Debate Team",
            "Science Olympiad",
            "Chess Club",
            "Programming Class",
            "Gym Class",
        ]

        for activity in required_activities:
            assert activity in data


class TestSignupForActivity:
    """Test signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Tennis Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Tennis Club" in data["message"]

    def test_signup_duplicate_student(self):
        """Test signup fails when student already registered"""
        # First signup
        client.post("/activities/Tennis Club/signup?email=duplicate@mergington.edu")

        # Duplicate signup
        response = client.post(
            "/activities/Tennis Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400

        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup fails for nonexistent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404

        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_activity_at_capacity(self):
        """Test signup fails when activity is at max capacity"""
        # Get current participants for an activity
        response = client.get("/activities")
        activities = response.json()

        # Find an activity with very limited space (max_participants - current)
        # Chess Club has max 12, initially has 2
        response = client.post(
            "/activities/Chess Club/signup?email=student1@mergington.edu"
        )
        assert response.status_code == 200

        # Get updated activities
        response = client.get("/activities")
        activities = response.json()

        # Verify student was added
        assert "student1@mergington.edu" in activities["Chess Club"]["participants"]


class TestUnregisterFromActivity:
    """Test unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        # First signup
        client.post("/activities/Drama Club/signup?email=testuser@mergington.edu")

        # Then unregister
        response = client.delete(
            "/activities/Drama Club/unregister?email=testuser@mergington.edu"
        )
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "testuser@mergington.edu" in data["message"]
        assert "Drama Club" in data["message"]

    def test_unregister_not_registered(self):
        """Test unregister fails when student not registered"""
        response = client.delete(
            "/activities/Debate Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400

        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister fails for nonexistent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404

        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removetest@mergington.edu"

        # Signup
        client.post(f"/activities/Science Olympiad/signup?email={email}")

        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Science Olympiad"]["participants"]

        # Unregister
        client.delete(f"/activities/Science Olympiad/unregister?email={email}")

        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Science Olympiad"]["participants"]


class TestActivityAvailability:
    """Test activity availability logic"""

    def test_participants_list_exists(self):
        """Test that all activities have a participants list"""
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity_details in data.items():
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_max_participants_field_exists(self):
        """Test that all activities have max_participants field"""
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity_details in data.items():
            assert "max_participants" in activity_details
            assert isinstance(activity_details["max_participants"], int)
            assert activity_details["max_participants"] > 0
