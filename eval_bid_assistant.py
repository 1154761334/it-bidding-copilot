"""
Baseline evaluator for the IT bidding assistant.

It exercises the real FastAPI /bid contract and generated artifacts. It does
not call or mock an LLM.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from src.main import app  # noqa: E402


def check(name: str, ok: bool, details: str = "") -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "details": details}


def main() -> int:
    client = TestClient(app)
    checks: list[dict[str, Any]] = []

    health = client.get("/health")
    health_json = health.json() if health.status_code == 200 else {}
    checks.append(check("health endpoint", health.status_code == 200, str(health.status_code)))
    checks.append(check("evidence store nonempty", health_json.get("evidence_count", 0) > 0, str(health_json.get("evidence_count"))))

    projects = client.get("/projects")
    checks.append(check("projects endpoint", projects.status_code == 200, str(projects.status_code)))

    evidence = client.get("/evidence/search", params={"query": "ISO9001 营业执照 授权书", "top_k": 8})
    evidence_json = evidence.json() if evidence.status_code == 200 else {}
    evidence_results = evidence_json.get("results", [])
    checks.append(check("evidence search returns results", bool(evidence_results), str(evidence_json.get("count"))))
    checks.append(check("evidence_id present", bool(evidence_results and evidence_results[0].get("evidence_id", "").startswith("EVID-"))))

    demo = client.post("/demo/real-case")
    demo_json = demo.json() if demo.status_code == 200 else {}
    checks.append(check("real demo completes", demo.status_code == 200 and demo_json.get("status") == "completed", str(demo.status_code)))
    project_id = demo_json.get("project_id", "")

    detail = client.get(f"/projects/{project_id}") if project_id else None
    detail_json = detail.json() if detail is not None and detail.status_code == 200 else {}
    checks.append(check("project detail available", bool(detail_json.get("id"))))

    artifacts = set(demo_json.get("artifacts", []))
    required_artifacts = {"plan.md", "response_matrix.md", "draft.md", "review.md", "evidence_trace.json"}
    for artifact in sorted(required_artifacts):
        checks.append(check(f"artifact {artifact}", artifact in artifacts))

    artifact_text: dict[str, str] = {}
    for artifact in sorted(required_artifacts):
        if not project_id:
            artifact_text[artifact] = ""
            continue
        response = client.get(f"/projects/{project_id}/artifacts/{artifact}")
        artifact_text[artifact] = response.text if response.status_code == 200 else ""

    trace: list[dict[str, Any]] = []
    try:
        trace = json.loads(artifact_text["evidence_trace.json"])
    except Exception:
        trace = []
    checks.append(check("evidence trace nonempty", bool(trace), str(len(trace))))

    matrix = artifact_text["response_matrix.md"]
    draft = artifact_text["draft.md"]
    review = artifact_text["review.md"]
    checks.append(check("matrix covers hard clauses", "| hard_clause |" in matrix))
    checks.append(check("matrix covers scoring items", "| scoring_item |" in matrix))
    checks.append(check("draft has realistic structure", all(token in draft for token in ["商务响应", "技术方案", "售后服务方案"])))
    checks.append(check("draft avoids page placeholders", "第 **X** 页" not in draft and "第X页" not in draft))
    checks.append(check("review flags coverage or findings", "评分覆盖" in review and "硬性条款覆盖" in review))

    passed = sum(1 for item in checks if item["ok"])
    total = len(checks)
    score = round(passed / total * 100, 1) if total else 0
    result = {
        "score": score,
        "checks_passed": passed,
        "checks_total": total,
        "project_id": project_id,
        "failed": [item for item in checks if not item["ok"]],
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if score >= 85 else 1


if __name__ == "__main__":
    raise SystemExit(main())
