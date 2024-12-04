from fastapi.testclient import TestClient

from scripts.main import app
import pytest


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# sanity test
def test_get_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Ticket API is working :DDD"}


def test_get_user(client):
    create_response = client.post(
        "/user", json={"username": "Panchito", "password": "1234"}
    )

    user_id = create_response.json()["id"]
    get_response = client.get(f"/user/{user_id}")

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Panchito"
    # we are testing for correct retrieval after creation


def test_get_all_user(client):
    get_response = client.get("/user")
    for user in get_response.json():
        assert isinstance(user["id"], int)
        assert isinstance(user["name"], str)


def test_create_user(client):
    user_data = {"username": "Pepito", "password": "1234"}
    response = client.post("/user", json=user_data)
    assert response.status_code == 201
    assert response.json()["name"] == "Pepito"

    bad_user_data = {
        "username": "",
        "password": "1234",
    }
    # username cant be empty
    response = client.post("/user", json=bad_user_data)
    assert response.status_code == 400


def test_get_event(client):
    event_data = {
        "name": "TEST_GET_EVENT",
        "price": 100,
    }
    create_response = client.post("/event", json=event_data)
    event_id = int(create_response.json()["id"])  # created event id

    get_response = client.get(f"/event/{event_id}")

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "TEST_GET_EVENT"

    # event ids start from 1
    response = client.get(f"/event/{0}")
    assert response.status_code == 404


def test_get_all_events(client):
    response = client.get("/event")
    for event in response.json():
        assert isinstance(event["id"], int)
        assert isinstance(event["name"], str)
        assert isinstance(event["price"], float)


def test_create_event(client):
    event_data = {
        "name": "TEST_CREATE_EVENT",
        "price": 100,
    }
    create_response = client.post("/event", json=event_data)
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "TEST_CREATE_EVENT"

    bad_event_data = {
        "name": "",
        "price": 100,
    }
    # event name cant be empty
    create_response = client.post("/event", json=bad_event_data)
    assert create_response.status_code == 400


def test_delete_event(client):
    event_data = {
        "name": "TEST_DELETE_EVENT",
        "price": 100,
    }
    create_response = client.post("/event", json=event_data)
    event_id = create_response.json()["id"]

    delete_response = client.delete(f"/movie/{event_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["name"] == "TEST_DELETE_EVENT"

    # event ids start from 1
    delete_response = client.delete(f"/movie/{0}")
    assert delete_response.status_code == 404
