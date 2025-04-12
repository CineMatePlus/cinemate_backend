Feature: User API Tests
  As a user
  I want to test User API endpoints
  So that I can ensure user operations work correctly

  Scenario: Check API health
    When I send a GET request to "/":
    Then the response status code should be 200

  Scenario: Register a new user
    When I send a POST request to "/api/v1/auth/auth/register" with body
      """
      {
        "email": "strissssdasd@gmail.com",
        "name": "string",
        "password": "string"
      }
      """
    Then the response status code should be 200