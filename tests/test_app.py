from app import create_app


def test_health():
    client = create_app("testing").test_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["errors"] == []
