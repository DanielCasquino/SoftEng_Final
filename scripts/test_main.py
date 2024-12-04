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
    assert response.json() == {"message": "Working"}


def test_get_user(client):
    create_response = client.post(
        "/user", json={"username": "Panchito", "password": "1234"}
    )

    user_id = create_response.json()["id"]
    get_response = client.get(f"/user/{user_id}")

    assert get_response.status_code == 200
    assert get_response.json()["username"] == "Panchito"
    # we are testing for correct retrieval after creation


def test_get_all_user(client):
    get_response = client.get("/user")
    for user in get_response.json():
        assert isinstance(user["id"], int)
        assert isinstance(user["username"], str)


def test_create_user(client):
    user_data = {"username": "Pepito", "password": "1234"}
    response = client.post("/user", json=user_data)
    assert response.status_code == 201
    assert response.json()["username"] == "Pepito"

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


def test_buy_ticket(client):
    user_data = {"username": "Pepito", "password": "1234"}
    user_response = client.post("/user", json=user_data)
    user_id = user_response.json()["id"]

    event_data = {
        "name": "TEST_BUY_TICKET",
        "price": 100,
    }
    event_response = client.post("/event", json=event_data)
    event_id = event_response.json()["id"]

    ticket_buy_response = client.post(f"/ticket/buy/{user_id}/{event_id}")
    assert ticket_buy_response.status_code == 201
    assert ticket_buy_response.json()["user_id"] == user_id
    assert ticket_buy_response.json()["event_id"] == event_id

    ticket_buy_response = client.post(f"/ticket/buy/{0}/{0}")
    assert ticket_buy_response.status_code == 404


def test_reserve_ticket(client):
    user_data = {"username": "Pepito", "password": "1234"}
    user_response = client.post("/user", json=user_data)
    user_id = user_response.json()["id"]

    event_data = {
        "name": "TEST_RESERVE_TICKET",
        "price": 100,
    }
    event_response = client.post("/event", json=event_data)
    event_id = event_response.json()["id"]

    ticket_reserve_response = client.post(f"/ticket/reserve/{user_id}/{event_id}")
    assert ticket_reserve_response.status_code == 201

    ticket_reserve_response = client.post(f"/ticket/reserve/{0}/{0}")
    assert ticket_reserve_response.status_code == 404


def test_pay_ticket(client):
    user_data = {"username": "Pepito", "password": "1234"}
    user_response = client.post("/user", json=user_data)
    user_id = user_response.json()["id"]

    event_data = {
        "name": "TEST_TICKET_PAY",
        "price": 100,
    }
    event_response = client.post("/event", json=event_data)
    event_id = event_response.json()["id"]

    ticket_reserve_response = client.post(f"/ticket/reserve/{user_id}/{event_id}")
    ticket_id = ticket_reserve_response.json()["id"]

    ticket_pay_response = client.patch(f"/ticket/pay/{ticket_id}")
    assert ticket_pay_response.status_code == 200

    ticket_pay_response = client.patch(f"/ticket/pay/{0}")
    assert ticket_pay_response.status_code == 404

    ticket_pay_response = client.patch(f"/ticket/pay/{ticket_id}")
    assert ticket_pay_response.status_code == 400  # cause already paid


def test_cancel_ticket(client):
    user_data = {"username": "Pepito", "password": "1234"}
    user_response = client.post("/user", json=user_data)
    user_id = user_response.json()["id"]

    event_data = {
        "name": "TEST_TICKET_CANCEL",
        "price": 100,
    }
    event_response = client.post("/event", json=event_data)
    event_id = event_response.json()["id"]

    test_ticket_cancel_response = client.post(f"/ticket/reserve/{user_id}/{event_id}")
    ticket_id = test_ticket_cancel_response.json()["id"]

    ticket_cancel_response = client.patch(f"/ticket/cancel/{ticket_id}")
    assert ticket_cancel_response.status_code == 200


def test_use_ticket(client):
    user_data = {"username": "Pepito", "password": "1234"}
    user_response = client.post("/user", json=user_data)
    user_id = user_response.json()["id"]

    event_data = {
        "name": "TEST_TICKET_USE",
        "price": 100,
    }
    event_response = client.post("/event", json=event_data)
    event_id = event_response.json()["id"]

    test_ticket_use_response = client.post(f"/ticket/buy/{user_id}/{event_id}")
    ticket_id = test_ticket_use_response.json()["id"]

    ticket_use_response = client.patch(f"/ticket/use/{ticket_id}")
    assert ticket_use_response.status_code == 200

    ticket_use_response = client.patch(f"/ticket/use/{ticket_id}")
    assert ticket_use_response.status_code == 400  # cause already used
