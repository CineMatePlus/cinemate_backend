Feature: User API Tests
  As a user
  I want to test User API endpoints
  So that I can ensure user operations work correctly

  Scenario: Check API health
    When I send a GET request to "/"
    Then the response status code should be 200
    And the API should be healthy
    
  Scenario: Register a new user
    When I send a POST request to "/api/v1/auth/register" with body
      """
      {
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "testpassword123",
        "gender": 0
      }
      """
    Then the response status code should be 201
    And the response should contain "access_token"

  Scenario: Login with registered user
    When I send a POST request to "/api/v1/auth/login" with body
      | username | password |
      | testuser@example.com | testpassword123 |
    Then the response status code should be 200
    And the response should contain "access_token"

  Scenario: Get current user profile with token
    Given I have a valid access token
    When I send a GET request to "/api/v1/auth/me" with headers
      | Authorization | 
      |Bearer {token} |
    Then the response status code should be 200
    And the response should contain "email"
    And the response should contain "name"

  Scenario: Rotate a refresh token and reject reuse
    Given I have a valid token pair
    When I rotate the refresh token
    Then the response status code should be 200
    And the response should contain "refresh_token"
    When I reuse the previous refresh token
    Then the response status code should be 401
