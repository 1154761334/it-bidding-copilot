"""
Baseline evaluator for the IT bidding assistant.

It exercises the real FastAPI /bid contract and generated artifacts. It does
not call or mock an LLM.
"""
from __future__ import annotations

import json
import re
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


EVID_RE = re.compile(r"EVID-\d+")


def split_md_row(line: str) -> list[str]:
    """Split a Markdown table row on unescaped pipes."""
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    cells.append("".join(current).strip())
    return cells


def table_rows(markdown: str, expected_columns: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in markdown.splitlines():
        if not line.startswith("| ") or line.startswith("|---") or line.startswith("| ID") or line.startswith("| 序号") or line.startswith("| 证据ID"):
            continue
        cells = split_md_row(line)
        if len(cells) == expected_columns:
            rows.append(cells)
    return rows


def malformed_table_rows(markdown: str, expected_columns: int | set[int]) -> list[str]:
    allowed = {expected_columns} if isinstance(expected_columns, int) else expected_columns
    bad: list[str] = []
    for line in markdown.splitlines():
        if not line.startswith("| ") or line.startswith("|---"):
            continue
        if len(split_md_row(line)) not in allowed:
            bad.append(line)
    return bad


def read_repo_text(path: str) -> str:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


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
    matrix_rows = table_rows(matrix, 6)
    hard_rows = [row for row in matrix_rows if row[1] == "hard_clause"]
    tech_rows = [row for row in matrix_rows if row[1] == "technical_requirement"]
    scoring_rows = [row for row in matrix_rows if row[1] == "scoring_item"]
    checks.append(check("matrix table is well formed", not malformed_table_rows(matrix, 6), str(malformed_table_rows(matrix, 6)[:1])))
    checks.append(check("draft tables are well formed", not malformed_table_rows(draft, {4, 5, 6}), str(malformed_table_rows(draft, {4, 5, 6})[:1])))
    checks.append(check("matrix covers hard clauses", len(hard_rows) >= 5, str(len(hard_rows))))
    checks.append(check("matrix covers technical requirements", len(tech_rows) >= 8, str(len(tech_rows))))
    checks.append(check("matrix covers scoring items", len(scoring_rows) >= 5, str(len(scoring_rows))))
    checks.append(check("matrix has no missing evidence", "missing_evidence" not in matrix))

    trace_ids = {item.get("evidence_id") for item in trace}
    matrix_ids = set(EVID_RE.findall(matrix))
    draft_ids = set(EVID_RE.findall(draft))
    checks.append(check("matrix evidence ids fully traced", matrix_ids <= trace_ids, str(sorted(matrix_ids - trace_ids)[:5])))
    checks.append(check("draft evidence ids fully traced", draft_ids <= trace_ids, str(sorted(draft_ids - trace_ids)[:5])))
    checks.append(
        check(
            "trace records include source metadata",
            all(item.get("source_doc") and item.get("heading_path") for item in trace),
            str([item for item in trace if not item.get("source_doc") or not item.get("heading_path")][:1]),
        )
    )
    checks.append(check("trace records include asset paths", all("asset_paths" in item for item in trace)))

    checks.append(check("draft has realistic structure", all(token in draft for token in ["商务响应", "技术方案", "售后服务方案"])))
    checks.append(check("draft expands technical implementation", all(token in draft for token in ["#### T1", "响应口径", "实现要点", "证据定位", "不写无证据的扩展能力"])))
    checks.append(check("draft maps technical notes to clause types", all(token in draft for token in ["一云多芯兼容性", "纠删码保护机制", "服务目录编排"])))
    checks.append(check("draft has evidence index", "## 六、证据索引" in draft and "| 证据ID | 标题 | 来源文件 | 来源位置 | 页码/资产提示 | 装订状态 |" in draft))
    checks.append(check("draft evidence index tracks attachment readiness", all(token in draft for token in ["页码/资产提示", "装订状态", "需回填页码"])))
    checks.append(check("draft avoids page placeholders", "第 **X** 页" not in draft and "第X页" not in draft))
    checks.append(check("draft avoids unsupported provided claims", "待补充对应证明材料，正式稿不得写成已提供" not in draft))
    checks.append(check("review flags coverage", "评分覆盖" in review and "硬性条款覆盖" in review))
    checks.append(check("review flags missing form risks", "签章与主体信息" in review and "材料索引" in review))
    checks.append(check("review has attachment readiness", all(token in review for token in ["## 附件就绪度", "投标人侧证据", "装订状态"])))
    checks.append(
        check(
            "review has actionable risk buckets",
            all(token in review for token in ["## 风险分桶", "废标风险", "商务条款风险", "评分点风险", "签章与材料风险"]),
        )
    )

    frontend_route = read_repo_text("frontend/src/business/client/BusinessDesktopRoutes.tsx")
    frontend_store = read_repo_text("frontend/src/store/bidding/index.ts")
    frontend_workbench = read_repo_text("frontend/src/features/Bidding/BiddingWorkbench.tsx")
    frontend_draft_tab = read_repo_text("frontend/src/features/Bidding/BiddingDraftTab.tsx")
    frontend_review_tab = read_repo_text("frontend/src/features/Bidding/BiddingReviewTab.tsx")
    checks.append(check("frontend /bid route wired", "path: 'bid'" in frontend_route and "BiddingWorkbench" in frontend_route))
    checks.append(
        check(
            "frontend demo opens generated artifacts",
            all(
                token in frontend_store
                for token in [
                    "selectProject(result.project_id)",
                    "fetchArtifactContent(result.project_id",
                    "pickDefaultArtifact(get().artifacts, 'draft.md')",
                ]
            )
            and "setActiveTab('draft')" in frontend_workbench,
        )
    )
    checks.append(
        check(
            "frontend draft tab shows selected artifact metadata",
            all(token in frontend_draft_tab for token in ["currentArtifactName", "formatBytes", "evidenceCount"]),
        )
    )
    checks.append(
        check(
            "frontend renders markdown artifact tables",
            all(token in frontend_draft_tab for token in ["ArtifactPreview", "MarkdownTable", "splitMarkdownRow"]),
        )
    )
    checks.append(
        check(
            "frontend loads artifact evidence trace",
            all(token in frontend_store for token in ["currentEvidenceTrace", "parseEvidenceTrace", "getArtifact(projectId, 'evidence_trace.json')"]),
        )
    )
    checks.append(
        check(
            "frontend evidence ids open trace details",
            all(token in frontend_draft_tab for token in ["EvidenceTracePanel", "groupEvidenceTrace", "onSelectEvidence", "Page / Asset hint"]),
        )
    )
    checks.append(check("frontend evidence panel shows asset paths", all(token in frontend_draft_tab for token in ["asset_paths", "Asset paths"])))
    checks.append(check("frontend review tab shows risk buckets", all(token in frontend_review_tab for token in ["risk_buckets", "Risk Buckets", "bucket.status"])))

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
