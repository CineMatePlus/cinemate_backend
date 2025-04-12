from behave import when, then
import requests
import time
import json

BASE_URL = "http://localhost:8000"


def wait_for_server():
    max_retries = 5
    retry_delay = 5

    for _ in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(retry_delay)
    return False


@when('I send a GET request to "/":')
def step_impl(context):
    if not wait_for_server():
        raise Exception("API sunucusu başlatılamadı")
    context.response = requests.get(f"{BASE_URL}/")


@when('I send a POST request to "/api/v1/auth/auth/register" with body')
def step_impl(context):
    if not wait_for_server():
        raise Exception("API sunucusu başlatılamadı")
    data = json.loads(context.text)
    context.response = requests.post(f"{BASE_URL}/api/v1/auth/auth/register", json=data)
    if context.response.status_code != 200:
        print(f"Register hatası: {context.response.text}")


@then("the response status code should be 200")
def step_impl(context):
    assert (
        context.response.status_code == 200
    ), f"Beklenen: 200, Alınan: {context.response.status_code}, Response: {context.response.text}"
