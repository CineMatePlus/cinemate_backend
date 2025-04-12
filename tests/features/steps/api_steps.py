from behave import given, when, then
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Check API health
@when('I send a GET request to "/"')
def step_impl(context):
    context.response = requests.get("http://localhost:8000/")

# Register a new user
@when('I send a POST request to "/api/v1/auth/auth/register" with body')
def step_impl(context):
    data = json.loads(context.text)
    context.response = requests.post(f"{BASE_URL}/auth/auth/register", json=data)

# Login with registered user
@when('I send a POST request to "/api/v1/auth/auth/login" with form data')
def step_impl(context):
    row = context.table[0]
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    form_data = {
        "username": row.get("username"),
        "password": row.get("password"),
        "grant_type": "password",
        "scope": "",
        "client_id": "in minim",
        "client_secret": "sunt eli"
    }
    context.response = requests.post(
        f"{BASE_URL}/auth/auth/login",
        headers=headers,
        data=form_data
    )
    # Token'ı sakla
    if context.response.status_code == 200:
        context.access_token = context.response.json()["access_token"]

# Get user profile with token
@given('I have a valid access token')
def step_impl(context):
    # Önce kayıt ol
    register_data = {
        "email": "testuser1@example.com",
        "name": "Test User",
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/auth/auth/register", json=register_data)
    assert response.status_code == 200
    
    # Sonra giriş yap
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    form_data = {
        "username": "testuser1@example.com",
        "password": "testpassword123",
        "grant_type": "password",
        "scope": "",
        "client_id": "in minim",
        "client_secret": "sunt eli"
    }
    response = requests.post(
        f"{BASE_URL}/auth/auth/login",
        headers=headers,
        data=form_data
    )
    assert response.status_code == 200
    context.access_token = response.json()["access_token"]

@when('I send a GET request to "/api/v1/auth/auth/me" with headers')
def step_impl(context):
    row = context.table[0]
    headers = {
        'Authorization': f'Bearer {context.access_token}'
    }
    context.response = requests.get(f"{BASE_URL}/auth/auth/me", headers=headers)

@then('the response status code should be 200')
def step_impl(context):
    assert context.response.status_code == 200

@then('the API should be healthy')
def step_impl(context):
    assert context.response.status_code == 200
    assert "message" in context.response.json()
    assert context.response.json()["message"] == "Cinemate API'ye hoş geldiniz!"

@then('the response should contain "{text}"')
def step_impl(context, text):
    assert text in context.response.text
