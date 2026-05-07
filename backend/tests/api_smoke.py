"""
Smoke test for the /bid FastAPI contract.

Run from backend:
    venv/bin/python tests/api_smoke.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200, health.text
    assert health.json()["evidence_count"] > 0

    projects = client.get("/projects")
    assert projects.status_code == 200, projects.text
    assert "projects" in projects.json()

    evidence = client.get("/evidence/search", params={"query": "ISO9001 营业执照 授权书", "top_k": 5})
    assert evidence.status_code == 200, evidence.text
    payload = evidence.json()
    assert payload["count"] > 0
    assert payload["results"][0]["evidence_id"].startswith("EVID-")

    demo = client.post("/demo/real-case")
    assert demo.status_code == 200, demo.text
    demo_payload = demo.json()
    assert demo_payload["status"] == "completed"
    project_id = demo_payload["project_id"]
    for name in {"plan.md", "response_matrix.md", "draft.md", "review.md", "evidence_trace.json"}:
        assert name in demo_payload["artifacts"], demo_payload["artifacts"]
        artifact = client.get(f"/projects/{project_id}/artifacts/{name}")
        assert artifact.status_code == 200, artifact.text
        assert artifact.text.strip()

    print("API_SMOKE PASS")


if __name__ == "__main__":
    main()
