import json
import os

import requests
from behave import given, then, when

API_ORIGIN = f"http://127.0.0.1:{os.getenv('TEST_API_PORT', '8011')}"
BASE_URL = f"{API_ORIGIN}/api/v1"


# Check API health
@when('I send a GET request to "/"')
def step_impl(context):
    context.response = requests.get(f"{API_ORIGIN}/")


# Register a new user
@when('I send a POST request to "/api/v1/auth/register" with body')
def step_impl(context):
    data = json.loads(context.text)
    context.response = requests.post(f"{BASE_URL}/auth/register", json=data)


# Login with registered user
@when('I send a POST request to "/api/v1/auth/login" with body')
def step_impl(context):
    row = context.table[0]
    body = {
        "email": row.get("username"),
        "password": row.get("password"),
    }
    context.response = requests.post(f"{BASE_URL}/auth/login", json=body)
    # Token'ı sakla
    if context.response.status_code == 200:
        context.access_token = context.response.json()["access_token"]


# Get user profile with token
@given("I have a valid access token")
def step_impl(context):
    # Önce kayıt ol
    register_data = {
        "email": "testuser1@example.com",
        "name": "Test User",
        "password": "testpassword123",
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    assert response.status_code == 201

    # Sonra giriş yap
    body = {
        "email": "testuser1@example.com",
        "password": "testpassword123",
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=body)
    assert response.status_code == 200
    context.access_token = response.json()["access_token"]


@when('I send a GET request to "/api/v1/auth/me" with headers')
def step_impl(context):
    row = context.table[0]
    headers = {"Authorization": f"Bearer {context.access_token}"}
    context.response = requests.get(f"{BASE_URL}/auth/me", headers=headers)


@then("the response status code should be 200")
def step_impl(context):
    assert context.response.status_code == 200


@then("the API should be healthy")
def step_impl(context):
    assert context.response.status_code == 200
    assert "message" in context.response.json()
    assert context.response.json()["message"] == "Cinemate API'ye hoş geldiniz!"


@then('the response should contain "{text}"')
def step_impl(context, text):
    assert text in context.response.text


@given("I have a valid token pair")
def step_impl(context):
    register_data = {
        "email": "rotation@example.com",
        "name": "Rotation Test",
        "password": "testpassword123",
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    assert response.status_code == 201
    context.refresh_token = response.json()["refresh_token"]


@when("I rotate the refresh token")
def step_impl(context):
    context.previous_refresh_token = context.refresh_token
    context.response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": context.refresh_token},
    )
    if context.response.status_code == 200:
        context.refresh_token = context.response.json()["refresh_token"]


@when("I reuse the previous refresh token")
def step_impl(context):
    context.response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": context.previous_refresh_token},
    )


@then("the response status code should be 201")
def step_impl(context):
    assert context.response.status_code == 201


@then("the response status code should be 401")
def step_impl(context):
    assert context.response.status_code == 401
