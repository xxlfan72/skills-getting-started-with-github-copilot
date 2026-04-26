import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: No setup needed
        Act: GET /activities
        Assert: Response includes all activities and participant lists
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_includes_participant_lists(self, client, reset_activities):
        """
        Arrange: No setup needed
        Act: GET /activities
        Assert: Each activity has a participants list
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """
        Arrange: Valid activity name and email
        Act: POST to signup endpoint
        Assert: Student added to participants, 200 response
        """
        # Arrange
        activity_name = "Basketball Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]

    def test_signup_activity_not_found(self, client, reset_activities):
        """
        Arrange: Non-existent activity name
        Act: POST to signup endpoint with invalid activity
        Assert: 404 Not Found response
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_signup(self, client, reset_activities):
        """
        Arrange: Student already signed up for Chess Club
        Act: Attempt to sign up same student again
        Assert: 400 Bad Request with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in participants
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_activity_full(self, client, reset_activities):
        """
        Arrange: Fill up an activity to max capacity
        Act: Try to signup beyond capacity
        Assert: 400 Bad Request - Activity is full
        """
        # Arrange
        activity_name = "Tennis Team"  # max_participants: 10
        
        # Fill it up with dummy emails
        for i in range(10):
            email = f"student{i}@mergington.edu"
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Act - Try to add one more beyond capacity
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overflow@mergington.edu"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()

    def test_signup_missing_email_parameter(self, client, reset_activities):
        """
        Arrange: Valid activity but missing email parameter
        Act: POST without email query parameter
        Assert: 422 Unprocessable Entity (FastAPI validation error)
        """
        # Arrange
        activity_name = "Basketball Club"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup")
        
        # Assert
        assert response.status_code == 422  # FastAPI validation error

    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """
        Arrange: Multiple different students
        Act: Sign up multiple students for the same activity
        Assert: All successfully added
        """
        # Arrange
        activity_name = "Art Club"
        emails = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]
        
        # Act
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert - verify all students are in the activity
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        for email in emails:
            assert email in participants


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """
        Arrange: Student signed up for Chess Club
        Act: DELETE to unregister endpoint
        Assert: Student removed from participants, 200 response
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify student is registered
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client, reset_activities):
        """
        Arrange: Non-existent activity name
        Act: DELETE from nonexistent activity
        Assert: 404 Not Found response
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_student_not_signed_up(self, client, reset_activities):
        """
        Arrange: Student not registered for Chess Club
        Act: Attempt to unregister someone who isn't signed up
        Assert: 400 Bad Request with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notsignup@mergington.edu"
        
        # Verify student is not in participants
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_missing_email_parameter(self, client, reset_activities):
        """
        Arrange: Valid activity but missing email parameter
        Act: DELETE without email query parameter
        Assert: 422 Unprocessable Entity (FastAPI validation error)
        """
        # Arrange
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister")
        
        # Assert
        assert response.status_code == 422  # FastAPI validation error

    def test_signup_then_unregister_frees_up_spot(self, client, reset_activities):
        """
        Arrange: Fill an activity to capacity, then unregister someone
        Act: Sign up one more person after unregister
        Assert: The new signup succeeds (spot was freed)
        """
        # Arrange
        activity_name = "Tennis Team"  # max_participants: 10
        
        # Fill it up
        for i in range(10):
            email = f"student{i}@mergington.edu"
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Remove one student
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": "student0@mergington.edu"}
        )
        
        # Act - Try to add a new student to the freed spot
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Assert - should succeed
        assert response.status_code == 200
