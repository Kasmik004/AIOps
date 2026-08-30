import httpx
from fastapi.testclient import TestClient

from app.main import app


def test_webhook_returns_200_when_telegram_reply_fails(monkeypatch):
    async def fake_post(*args, **kwargs):
        raise httpx.ConnectError("All connection attempts failed")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    client = TestClient(app)
    payload = {
        "update_id": 480565045,
        "message": {
            "message_id": 44,
            "from": {
                "id": 5362494329,
                "is_bot": False,
                "first_name": "Kasmik",
                "last_name": "Regmi",
                "username": "kasmik004",
                "language_code": "en",
            },
            "chat": {"id": 5362494329, "type": "private"},
            "date": 1788020777,
            "text": "Hi",
        },
    }

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
