from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


SAMPLE_FILE = Path(__file__).resolve().parents[2] / "sample-data" / "sales_orders.csv"


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_demo_login_and_current_user() -> None:
    client = TestClient(app)

    headers = login(client, "demo@example.com", "demo123456")
    me_response = client.get("/api/auth/me", headers=headers)

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "demo@example.com"


def test_task_creation_requires_login() -> None:
    client = TestClient(app)

    with SAMPLE_FILE.open("rb") as file:
        response = client.post(
            "/api/tasks",
            data={"objective": "分析销售数据并生成经营报告。"},
            files={"file": ("sales_orders.csv", file, "text/csv")},
        )

    assert response.status_code == 401


def test_user_can_only_read_own_tasks() -> None:
    client = TestClient(app)
    demo_headers = login(client, "demo@example.com", "demo123456")

    register_response = client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "other123456"},
    )
    assert register_response.status_code in {200, 409}
    other_headers = login(client, "other@example.com", "other123456")

    with SAMPLE_FILE.open("rb") as file:
        create_response = client.post(
            "/api/tasks",
            data={"objective": "分析销售数据并生成经营报告。"},
            files={"file": ("sales_orders.csv", file, "text/csv")},
            headers=demo_headers,
        )

    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    own_response = client.get(f"/api/tasks/{task_id}", headers=demo_headers)
    other_response = client.get(f"/api/tasks/{task_id}", headers=other_headers)

    assert own_response.status_code == 200
    assert other_response.status_code == 404
