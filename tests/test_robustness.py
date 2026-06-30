import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    return TestClient(app)


@pytest.fixture()
def client_with_classifier(client, monkeypatch):
    monkeypatch.setattr(
        "app.classifier.classify_ticket",
        lambda title, description: {"category": "bug", "priority": "P2", "tags": []},
    )
    return client


def _create(client, title="Título válido", description="Descripción válida"):
    return client.post("/tickets", json={"title": title, "description": description})


# ── 1. Validación de título ────────────────────────────────────────────────────

def test_blank_title_rejected(client):
    assert _create(client, title="").status_code == 422


def test_whitespace_only_title_rejected(client):
    assert _create(client, title="   ").status_code == 422


def test_title_at_max_length_accepted(client_with_classifier):
    assert _create(client_with_classifier, title="A" * 200).status_code == 201


def test_title_over_max_length_rejected(client):
    assert _create(client, title="A" * 201).status_code == 422


# ── 2. Unicode y emojis ────────────────────────────────────────────────────────

def test_unicode_and_emojis_accepted(client_with_classifier):
    r = _create(client_with_classifier, title="Error 🚨 crítico", description="描述问题 العربية ñoño 🐛")
    assert r.status_code == 201
    data = r.json()
    assert "🚨" in data["title"]
    assert "描述问题" in data["description"]


# ── 3. HTML/XSS en descripción ────────────────────────────────────────────────

def test_html_in_description_stored_as_is(client_with_classifier):
    payload = "<script>alert('xss')</script>"
    r = _create(client_with_classifier, description=payload)
    assert r.status_code == 201
    # El contenido se almacena sin modificar; Jinja2 lo escapa al renderizar
    assert r.json()["description"] == payload


# ── 4. Inyección SQL ──────────────────────────────────────────────────────────

def test_sql_injection_in_description_is_safe(client_with_classifier):
    r = _create(client_with_classifier, description="'; DROP TABLE tickets; --")
    assert r.status_code == 201
    # La tabla sigue en pie
    assert client_with_classifier.get("/tickets").status_code == 200


# ── 5. LLM caído → fallback ───────────────────────────────────────────────────

def test_classifier_failure_falls_back_gracefully(client, monkeypatch):
    monkeypatch.setattr(
        "app.classifier.classify_ticket",
        lambda t, d: (_ for _ in ()).throw(RuntimeError("LLM unavailable")),
    )
    r = _create(client)
    assert r.status_code == 201
    data = r.json()
    assert data["category"] == "question"
    assert data["priority"] == "P3"
    assert data["tags"] == []


# ── 6. Tickets duplicados ─────────────────────────────────────────────────────

def test_duplicate_ticket_creates_two_entries(client_with_classifier):
    r1 = _create(client_with_classifier, title="Duplicado", description="misma desc")
    r2 = _create(client_with_classifier, title="Duplicado", description="misma desc")
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


# ── 7. IDs malformados ────────────────────────────────────────────────────────

def test_patch_negative_id_returns_404(client):
    r = client.patch("/tickets/-1", json={"status": "in_progress"})
    assert r.status_code == 404


def test_patch_nonexistent_id_returns_404(client):
    r = client.patch("/tickets/99999999999", json={"status": "in_progress"})
    assert r.status_code == 404


def test_patch_string_id_returns_422(client):
    r = client.patch("/tickets/abc", json={"status": "in_progress"})
    assert r.status_code == 422


# ── 8. PATCH con valores inválidos ────────────────────────────────────────────

def test_patch_invalid_status_rejected(client_with_classifier):
    ticket_id = _create(client_with_classifier).json()["id"]
    r = client_with_classifier.patch(f"/tickets/{ticket_id}", json={"status": "inventado"})
    assert r.status_code == 422


def test_patch_invalid_priority_rejected(client_with_classifier):
    ticket_id = _create(client_with_classifier).json()["id"]
    r = client_with_classifier.patch(f"/tickets/{ticket_id}", json={"priority": "P9"})
    assert r.status_code == 422


def test_patch_valid_status_accepted(client_with_classifier):
    ticket_id = _create(client_with_classifier).json()["id"]
    r = client_with_classifier.patch(f"/tickets/{ticket_id}", json={"status": "in_progress"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"


# ── 9. Concurrencia ───────────────────────────────────────────────────────────

def test_concurrent_posts_all_succeed(tmp_path, monkeypatch):
    import threading
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'concurrent.db'}")
    monkeypatch.setattr(
        "app.classifier.classify_ticket",
        lambda t, d: {"category": "bug", "priority": "P1", "tags": []},
    )
    client = TestClient(app)
    results = []

    def post(i):
        r = client.post("/tickets", json={"title": f"Ticket {i}", "description": f"desc {i}"})
        results.append(r.status_code)

    threads = [threading.Thread(target=post, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count(201) == 20
