import pytest


def create_task(client, headers, **payload):
    payload.setdefault("title", "Sample task")
    response = client.post("/tasks", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


# ---------- Autenticación ----------


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/tasks"),
        ("get", "/tasks"),
        ("get", "/tasks/1"),
        ("patch", "/tasks/1"),
        ("delete", "/tasks/1"),
    ],
)
def test_task_endpoints_require_authentication(client, method, path):
    response = client.request(method, path, json={"title": "x"})

    assert response.status_code == 401


# ---------- Crear ----------


def test_create_task_success(client, auth_headers):
    response = client.post(
        "/tasks",
        json={"title": "Estudiar FastAPI", "description": "Fase 3"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Estudiar FastAPI"
    assert body["description"] == "Fase 3"
    assert body["status"] == "pending"
    assert body["due_date"] is None
    assert "id" in body and "created_at" in body and "owner_id" in body


def test_create_task_with_status_and_due_date(client, auth_headers):
    task = create_task(
        client,
        auth_headers,
        status="in_progress",
        due_date="2026-12-01T12:00:00Z",
    )

    assert task["status"] == "in_progress"
    assert task["due_date"] is not None


@pytest.mark.parametrize(
    "payload",
    [
        {"title": ""},
        {"description": "no title"},
        {"title": "ok", "status": "hecho"},
        {"title": "x" * 201},
    ],
)
def test_create_task_invalid_payload_returns_422(client, auth_headers, payload):
    response = client.post("/tasks", json=payload, headers=auth_headers)

    assert response.status_code == 422


# ---------- Leer ----------


def test_get_task_success(client, auth_headers):
    task = create_task(client, auth_headers, title="Mine")

    response = client.get(f"/tasks/{task['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["title"] == "Mine"


def test_get_nonexistent_task_returns_404(client, auth_headers):
    response = client.get("/tasks/9999", headers=auth_headers)

    assert response.status_code == 404


# ---------- Listar, paginar, filtrar, ordenar ----------


def test_list_tasks_empty(client, auth_headers):
    response = client.get("/tasks", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_list_tasks_pagination_has_no_gaps_or_repeats(client, auth_headers):
    created_ids = [create_task(client, auth_headers, title=f"T{i}")["id"] for i in range(5)]

    seen_ids = []
    for offset in (0, 2, 4):
        response = client.get(f"/tasks?limit=2&offset={offset}", headers=auth_headers)
        body = response.json()
        assert body["total"] == 5
        assert body["limit"] == 2
        assert body["offset"] == offset
        seen_ids += [item["id"] for item in body["items"]]

    assert seen_ids == created_ids


def test_list_tasks_limit_above_maximum_returns_422(client, auth_headers):
    response = client.get("/tasks?limit=101", headers=auth_headers)

    assert response.status_code == 422


def test_list_tasks_negative_offset_returns_422(client, auth_headers):
    response = client.get("/tasks?offset=-1", headers=auth_headers)

    assert response.status_code == 422


def test_list_tasks_filter_by_status(client, auth_headers):
    create_task(client, auth_headers, title="a", status="pending")
    create_task(client, auth_headers, title="b", status="done")
    create_task(client, auth_headers, title="c", status="done")

    response = client.get("/tasks?status=done", headers=auth_headers)

    body = response.json()
    assert body["total"] == 2
    assert {item["title"] for item in body["items"]} == {"b", "c"}


def test_list_tasks_invalid_status_filter_returns_422(client, auth_headers):
    response = client.get("/tasks?status=hecho", headers=auth_headers)

    assert response.status_code == 422


def test_list_tasks_order_by_due_date_puts_tasks_without_date_last(client, auth_headers):
    create_task(client, auth_headers, title="no date")
    create_task(client, auth_headers, title="late", due_date="2026-12-20T12:00:00Z")
    create_task(client, auth_headers, title="early", due_date="2026-12-01T12:00:00Z")

    asc = client.get("/tasks?order_by=due_date&direction=asc", headers=auth_headers)
    desc = client.get("/tasks?order_by=due_date&direction=desc", headers=auth_headers)

    assert [t["title"] for t in asc.json()["items"]] == ["early", "late", "no date"]
    assert [t["title"] for t in desc.json()["items"]] == ["late", "early", "no date"]


# ---------- Actualizar ----------


def test_patch_updates_only_sent_fields(client, auth_headers):
    task = create_task(client, auth_headers, title="Original", description="keep me")

    response = client.patch(
        f"/tasks/{task['id']}", json={"status": "done"}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["title"] == "Original"
    assert body["description"] == "keep me"


def test_patch_can_clear_optional_fields_with_null(client, auth_headers):
    task = create_task(
        client,
        auth_headers,
        description="remove me",
        due_date="2026-12-01T12:00:00Z",
    )

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"description": None, "due_date": None},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["due_date"] is None


@pytest.mark.parametrize("payload", [{"title": None}, {"status": None}, {"title": ""}])
def test_patch_invalid_values_return_422(client, auth_headers, payload):
    task = create_task(client, auth_headers)

    response = client.patch(f"/tasks/{task['id']}", json=payload, headers=auth_headers)

    assert response.status_code == 422


def test_patch_nonexistent_task_returns_404(client, auth_headers):
    response = client.patch("/tasks/9999", json={"title": "x"}, headers=auth_headers)

    assert response.status_code == 404


# ---------- Borrar ----------


def test_delete_task_returns_204_and_removes_it(client, auth_headers):
    task = create_task(client, auth_headers)

    response = client.delete(f"/tasks/{task['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/tasks/{task['id']}", headers=auth_headers).status_code == 404


def test_delete_nonexistent_task_returns_404(client, auth_headers):
    response = client.delete("/tasks/9999", headers=auth_headers)

    assert response.status_code == 404


# ---------- Aislamiento entre usuarios ----------


def test_user_cannot_read_another_users_task(client, auth_headers, other_headers):
    task = create_task(client, auth_headers)

    response = client.get(f"/tasks/{task['id']}", headers=other_headers)

    assert response.status_code == 404


def test_user_cannot_update_another_users_task(client, auth_headers, other_headers):
    task = create_task(client, auth_headers, title="Original")

    response = client.patch(
        f"/tasks/{task['id']}", json={"title": "Hacked"}, headers=other_headers
    )

    assert response.status_code == 404
    unchanged = client.get(f"/tasks/{task['id']}", headers=auth_headers).json()
    assert unchanged["title"] == "Original"


def test_user_cannot_delete_another_users_task(client, auth_headers, other_headers):
    task = create_task(client, auth_headers)

    response = client.delete(f"/tasks/{task['id']}", headers=other_headers)

    assert response.status_code == 404
    assert client.get(f"/tasks/{task['id']}", headers=auth_headers).status_code == 200


def test_list_only_returns_own_tasks(client, auth_headers, other_headers):
    create_task(client, auth_headers, title="Alice 1")
    create_task(client, auth_headers, title="Alice 2")
    create_task(client, other_headers, title="Bob 1")

    alice = client.get("/tasks", headers=auth_headers).json()
    bob = client.get("/tasks", headers=other_headers).json()

    assert alice["total"] == 2
    assert {t["title"] for t in alice["items"]} == {"Alice 1", "Alice 2"}
    assert bob["total"] == 1
    assert bob["items"][0]["title"] == "Bob 1"