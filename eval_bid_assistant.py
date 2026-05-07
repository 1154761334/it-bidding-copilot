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
    readiness_summary = detail_json.get("readiness_summary") or {}
    checks.append(
        check(
            "project exposes readiness summary",
            all(
                key in readiness_summary
                for key in [
                    "attachment_ready",
                    "attachment_needs_page_hint",
                    "scoring_ready",
                    "scoring_needs_bidder_evidence",
                ]
            ),
            str(readiness_summary),
        )
    )
    review_payload = detail_json.get("review") or {}
    action_checklist = review_payload.get("action_checklist") or []
    checks.append(
        check(
            "project exposes action checklist",
            bool(action_checklist)
            and all(
                key in action_checklist[0]
                for key in ["priority", "area", "action", "owner", "references", "evidence_ids", "row_ids", "artifact_refs"]
            ),
            str(action_checklist[:1]),
        )
    )
    checks.append(
        check(
            "project action checklist has evidence links",
            any(item.get("evidence_ids") for item in action_checklist)
            and any(item.get("row_ids") for item in action_checklist),
            str(action_checklist),
        )
    )
    artifact_required_areas = {"主体信息", "商务复核", "商务证据回填", "合同义务签核", "附件定位", "评分定位"}
    checks.append(
        check(
            "project action checklist maps artifact refs",
            bool(action_checklist)
            and all(
                item.get("artifact_refs") and any(".md" in ref or ".json" in ref for ref in item.get("artifact_refs", []))
                for item in action_checklist
                if item.get("area") in artifact_required_areas
            ),
            str(action_checklist),
        )
    )
    material_groups = review_payload.get("material_groups") or []
    checks.append(
        check(
            "project exposes material groups",
            {item.get("label") for item in material_groups}
            >= {"资格证明材料", "商务报价材料", "技术评分附件"},
            str(material_groups),
        )
    )
    commercial_readiness = review_payload.get("commercial_evidence_readiness") or {}
    checks.append(
        check(
            "project exposes commercial evidence readiness",
            all(
                key in commercial_readiness
                for key in [
                    "ready",
                    "total",
                    "needs_page_hint",
                    "tender_only",
                    "rows",
                    "not_ready_rows",
                ]
            )
            and commercial_readiness.get("total", 0) >= 5,
            str(commercial_readiness),
        )
    )
    checks.append(
        check(
            "project flags commercial bidder evidence gaps",
            any(row.get("status") == "needs_page_hint" and row.get("bidder_evidence_ids") for row in commercial_readiness.get("rows", [])),
            str(commercial_readiness.get("rows", [])[:2]),
        )
    )
    contract_readiness = review_payload.get("contract_obligation_readiness") or {}
    checks.append(
        check(
            "project exposes contract obligation readiness",
            all(
                key in contract_readiness
                for key in [
                    "ready",
                    "total",
                    "needs_page_hint",
                    "tender_only",
                    "rows",
                    "not_ready_rows",
                ]
            )
            and contract_readiness.get("total", 0) >= 5,
            str(contract_readiness),
        )
    )
    checks.append(
        check(
            "project flags contract obligation bidder evidence gaps",
            any(row.get("status") != "ready" and row.get("row_id", "").startswith("C") for row in contract_readiness.get("rows", [])),
            str(contract_readiness.get("rows", [])[:2]),
        )
    )
    checks.append(
        check(
            "project exposes draft contract appendix section",
            any(item.get("name") == "合同履约响应附录" for item in detail_json.get("draft_sections", []))
            and (detail_json.get("execution") or {}).get("draft_sections", 0) >= 6,
            str(detail_json.get("draft_sections", [])),
        )
    )
    checks.append(check("project exposes handoff artifact", review_payload.get("handoff_artifact") == "handoff.md", str(review_payload.get("handoff_artifact"))))

    artifacts = set(demo_json.get("artifacts", []))
    required_artifacts = {"plan.md", "response_matrix.md", "draft.md", "review.md", "handoff.md", "evidence_trace.json"}
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
    handoff = artifact_text["handoff.md"]
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
    review_ids = set(EVID_RE.findall(review))
    handoff_ids = set(EVID_RE.findall(handoff))
    checks.append(check("matrix evidence ids fully traced", matrix_ids <= trace_ids, str(sorted(matrix_ids - trace_ids)[:5])))
    checks.append(check("draft evidence ids fully traced", draft_ids <= trace_ids, str(sorted(draft_ids - trace_ids)[:5])))
    checks.append(check("review evidence ids fully traced", review_ids <= trace_ids, str(sorted(review_ids - trace_ids)[:5])))
    checks.append(check("handoff evidence ids fully traced", handoff_ids <= trace_ids, str(sorted(handoff_ids - trace_ids)[:5])))
    checks.append(
        check(
            "trace records include source metadata",
            all(item.get("source_doc") and item.get("heading_path") for item in trace),
            str([item for item in trace if not item.get("source_doc") or not item.get("heading_path")][:1]),
        )
    )
    checks.append(check("trace records include asset paths", all("asset_paths" in item for item in trace)))
    checks.append(
        check(
            "trace records include material groups",
            all(item.get("material_group_key") and item.get("material_group") for item in trace),
            str([item for item in trace if not item.get("material_group_key") or not item.get("material_group")][:1]),
        )
    )

    checks.append(check("draft has realistic structure", all(token in draft for token in ["商务响应", "技术方案", "售后服务方案"])))
    checks.append(
        check(
            "draft has commercial quotation response",
            all(
                token in draft
                for token in [
                    "## 二、报价及合同商务响应",
                    "| 商务事项 | 响应口径 | 证据定位 | 签核要求 |",
                    "投标报价",
                    "付款",
                    "履约保证金",
                    "增值税专用发票",
                ]
            ),
        )
    )
    checks.append(check("draft expands technical implementation", all(token in draft for token in ["#### T1", "响应口径", "实现要点", "证据定位", "不写无证据的扩展能力"])))
    checks.append(check("draft maps technical notes to clause types", all(token in draft for token in ["一云多芯兼容性", "纠删码保护机制", "服务目录编排"])))
    checks.append(check("draft has scoring response checklist", all(token in draft for token in ["| 评分项 | 响应要点 | 证据定位 | 就绪状态 | 人工复核 |", "证书有效期", "合同金额", "团队人员证书"])))
    checks.append(
        check(
            "draft has contract obligation appendix",
            all(
                token in draft
                for token in [
                    "## 八、合同履约响应附录",
                    "| 合同义务 | 受控响应口径 | 证据定位 | 签核缺口 |",
                    "C1 服务期及现场服务",
                    "C4 违约责任及解除合同",
                    "仅招标依据",
                    "未签核的期限、金额、违约金或分包条件不得擅自扩写",
                ]
            ),
        )
    )
    checks.append(check("draft has evidence index", "## 七、证据索引" in draft and "| 证据ID | 标题 | 来源文件 | 来源位置 | 页码/资产提示 | 装订状态 |" in draft))
    checks.append(check("draft has material package view", all(token in draft for token in ["### 7.1 材料包视图", "资格证明材料", "商务报价材料", "技术评分附件"])))
    checks.append(
        check(
            "draft material package includes contract execution evidence",
            all(
                token in draft
                for token in [
                    "| 合同履约材料 | 项目经理/法务 | C1, C2, C3, C4, C5, C6 |",
                    "Review 阶段追加",
                    "仅招标依据：C4",
                    "EVID-131",
                    "EVID-137",
                ]
            ),
        )
    )
    checks.append(
        check(
            "draft evidence details include contract obligation records",
            all(
                token in draft
                for token in [
                    "| EVID-131 | 9.3.4.1售后服务承诺",
                    "| EVID-137 | 9.3.4.6.1售后服务响应方式",
                    "| EVID-199 | 十、违约责任",
                    "| EVID-200 | 十二、违约解除合同",
                ]
            ),
        )
    )
    checks.append(check("draft evidence index tracks attachment readiness", all(token in draft for token in ["页码/资产提示", "装订状态", "需回填页码"])))
    checks.append(check("draft avoids page placeholders", "第 **X** 页" not in draft and "第X页" not in draft))
    checks.append(check("draft avoids unsupported provided claims", "待补充对应证明材料，正式稿不得写成已提供" not in draft))
    checks.append(check("plan has material package assignments", all(token in artifact_text["plan.md"] for token in ["## 材料包分工", "资格证明材料", "商务报价材料", "技术评分附件"])))
    checks.append(check("matrix has material grouping", all(token in matrix for token in ["## 材料用途分组", "资格证明材料", "商务报价材料", "技术评分附件"])))
    checks.append(check("review flags coverage", "评分覆盖" in review and "硬性条款覆盖" in review))
    checks.append(check("review flags missing form risks", "签章与主体信息" in review and "材料索引" in review))
    checks.append(check("review has attachment readiness", all(token in review for token in ["## 附件就绪度", "投标人侧证据", "装订状态"])))
    checks.append(check("review has scoring readiness", all(token in review for token in ["## 评分就绪度", "评分项就绪", "需补投标人材料"])))
    checks.append(check("review has commercial evidence readiness", all(token in review for token in ["## 商务证据签核", "投标人侧商务证据", "仅招标依据", "需回填页码/附件编号"])))
    checks.append(check("review has contract obligation readiness", all(token in review for token in ["## 合同履约义务复核", "服务期", "验收", "违约责任", "转让分包"])))
    checks.append(
        check(
            "review has action checklist",
            all(token in review for token in ["## 操作清单", "责任人", "商务证据回填", "合同义务签核", "附件定位", "评分定位"]),
        )
    )
    checks.append(
        check(
            "review has action evidence index",
            all(token in review for token in ["## 操作证据定位", "关联行", "证据ID", "Artifact"]),
        )
    )
    checks.append(
        check(
            "review action index maps artifact refs",
            all(
                token in review
                for token in [
                    "draft.md#二、报价及合同商务响应",
                    "review.md#合同履约义务复核",
                    "review.md#附件就绪度",
                    "response_matrix.md",
                ]
            ),
        )
    )
    checks.append(check("review has material group review", all(token in review for token in ["## 材料包复核", "资格证明材料", "商务报价材料", "技术评分附件"])))
    checks.append(
        check(
            "review has actionable risk buckets",
            all(token in review for token in ["## 风险分桶", "废标风险", "商务条款风险", "评分点风险", "签章与材料风险"]),
        )
    )
    checks.append(
        check(
            "handoff summarizes trial readiness",
            all(
                token in handoff
                for token in [
                    "# 项目交接摘要",
                    "## 试用就绪快照",
                    "## 剩余人工动作",
                    "## 材料包交接",
                    "## Artifact Map",
                ]
            ),
        )
    )
    checks.append(
        check(
            "handoff lists evidence gaps",
            all(token in handoff for token in ["## 证据缺口", "EVID-74", "S3", "需回填页码"]),
        )
    )
    checks.append(check("handoff lists commercial evidence gaps", all(token in handoff for token in ["商务证据签核", "H1", "EVID-42", "投标人侧"])))
    checks.append(check("handoff lists contract obligation gaps", all(token in handoff for token in ["合同履约义务", "C1", "服务期", "投标人侧"])))
    checks.append(check("handoff states evidence boundary", "未列入证据链的内容不得在正式稿中写成已提供" in handoff))

    frontend_route = read_repo_text("frontend/src/business/client/BusinessDesktopRoutes.tsx")
    frontend_store = read_repo_text("frontend/src/store/bidding/index.ts")
    frontend_workbench = read_repo_text("frontend/src/features/Bidding/BiddingWorkbench.tsx")
    frontend_draft_tab = read_repo_text("frontend/src/features/Bidding/BiddingDraftTab.tsx")
    frontend_draft_tab_test = read_repo_text("frontend/src/features/Bidding/BiddingDraftTab.test.tsx")
    frontend_bid_route_smoke = read_repo_text("frontend/scripts/bidding/smokeBidRoute.mts")
    frontend_bid_route_storage_capture = read_repo_text("frontend/scripts/bidding/captureBidRouteStorageState.mts")
    frontend_bid_route_runbook = read_repo_text("frontend/scripts/bidding/README.md")
    frontend_bid_route_secret_check = read_repo_text("frontend/scripts/bidding/checkBidRouteSmokeSecrets.mts")
    frontend_bid_route_secret_test = read_repo_text("frontend/scripts/bidding/testBidRouteSmokeSecrets.mts")
    frontend_bid_route_acceptance_runner = read_repo_text("frontend/scripts/bidding/runBidSmokeAcceptance.mts")
    frontend_bid_route_acceptance_runner_test = read_repo_text("frontend/scripts/bidding/testBidSmokeAcceptanceRunner.mts")
    frontend_bid_route_command_matrix_test = read_repo_text("frontend/scripts/bidding/testBidSmokeCommandMatrix.mts")
    frontend_bid_route_production_docs_test = read_repo_text("frontend/scripts/bidding/testBidRouteProductionDocs.mts")
    frontend_bid_route_production_docs_drift_test = read_repo_text("frontend/scripts/bidding/testBidRouteProductionDocsDrift.mts")
    frontend_bid_route_production_docs_failure_test = read_repo_text("frontend/scripts/bidding/testBidRouteProductionDocsFailure.mts")
    frontend_gitignore = read_repo_text("frontend/.gitignore")
    frontend_package_json = read_repo_text("frontend/package.json")
    frontend_evidence_tab = read_repo_text("frontend/src/features/Bidding/BiddingEvidenceTab.tsx")
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
            "frontend review opens handoff artifact",
            all(
                token in frontend_store
                for token in [
                    "'handoff.md'",
                    "pickDefaultArtifact(get().artifacts, 'handoff.md')",
                    "fetchArtifactContent(projectId, artifactName)",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend project list shows readiness summary",
            all(
                token in frontend_workbench
                for token in [
                    "readiness_summary",
                    "Project Readiness",
                    "attachment_needs_page_hint",
                    "scoring_needs_bidder_evidence",
                ]
            ),
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
    checks.append(
        check(
            "frontend artifact trace filters material groups",
            all(
                token in frontend_draft_tab
                for token in [
                    "materialGroups",
                    "Material Group Filter",
                    "selectedMaterialGroupKey",
                    "filterEvidenceTrace",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend draft tab shows artifact material package jumps",
            all(
                token in frontend_draft_tab
                for token in [
                    "ArtifactMaterialPackageSummary",
                    "Artifact Material Packages",
                    "buildArtifactMaterialPackages",
                    "handleSelectMaterialPackage",
                    "CONTRACT_EXECUTION_GROUP_KEY",
                    "Open trace",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend draft material package jump has render smoke test",
            all(
                token in frontend_draft_tab_test
                for token in [
                    "BiddingDraftTab",
                    "Artifact Material Packages",
                    "合同履约材料",
                    "fireEvent.click",
                    "Selected Evidence",
                    "EVID-131",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend /bid route has real artifact smoke",
            all(
                token in frontend_bid_route_smoke
                for token in [
                    "chromium",
                    "NEXT_PUBLIC_BIDDING_API_BASE_URL",
                    "/bid",
                    "Demo Real Case",
                    "Artifact Material Packages",
                    "合同履约材料",
                    "Selected Evidence",
                    "requestfailed",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend /bid route smoke supports auth bootstrap diagnostic",
            all(
                token in frontend_bid_route_smoke
                for token in [
                    "BID_ROUTE_STORAGE_STATE",
                    "BID_ROUTE_ALLOW_AUTH_REQUIRED",
                    "BID_ROUTE_AUTH_REQUIRED",
                    "required_env_names",
                    "storageState",
                    "/signin",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend bid route storage state capture is standardized",
            all(
                token in frontend_bid_route_storage_capture
                for token in [
                    "BID_ROUTE_STORAGE_STATE",
                    "BID_ROUTE_STORAGE_STATE_READY",
                    "BID_ROUTE_LOGIN_REQUIRED",
                    "SAFE_BOOTSTRAP_ENV_NAMES",
                    ".auth/bid-route-storage-state.json",
                    "storageState",
                ]
            )
            and ".auth/" in frontend_gitignore
            and "capture:bid-storage-state" in frontend_package_json,
        )
    )
    checks.append(
        check(
            "frontend bid route production smoke scripts are standardized",
            all(
                token in frontend_package_json
                for token in [
                    "capture:bid-storage-state:prod",
                    "smoke:bid-route",
                    "smoke:bid-route:prod",
                    "BID_FRONTEND_BASE_URL=http://127.0.0.1:3210",
                    "BID_ROUTE_PATH=/spa/desktop/bid",
                ]
            )
            and "BID_ROUTE_STORAGE_STATE" in frontend_bid_route_smoke
            and "BID_ROUTE_AUTH_REQUIRED" in frontend_bid_route_smoke,
        )
    )
    checks.append(
        check(
            "frontend bid route production smoke runbook is non-secret",
            all(
                token in frontend_bid_route_runbook
                for token in [
                    "smoke:bid-route:prod",
                    "capture:bid-storage-state:prod",
                    "BID_ROUTE_STORAGE_STATE",
                    ".auth/bid-route-storage-state.json",
                    "BID_ROUTE_LOGIN_REQUIRED",
                    "environment variable names only",
                    "do not write secret values",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend bid route smoke secret guard is executable",
            all(
                token in frontend_bid_route_secret_check
                for token in [
                    "TARGET_FILES",
                    "BID_ROUTE_SMOKE_SECRET_CHECK_PASS",
                    "BID_ROUTE_SMOKE_SECRET_CHECK_FAIL",
                    "credential literal",
                    "runBidSmokeAcceptance.mts",
                    "testBidRouteProductionDocsDrift.mts",
                    "testBidRouteProductionDocs.mts",
                    "testBidRouteProductionDocsFailure.mts",
                    "testBidSmokeAcceptanceRunner.mts",
                    "testBidSmokeCommandMatrix.mts",
                    "redact",
                    "process.exit(1)",
                ]
            )
            and "check:bid-smoke-secrets" in frontend_package_json,
        )
    )
    checks.append(
        check(
            "frontend bid route smoke secret guard has failure fixture",
            all(
                token in frontend_bid_route_secret_check
                for token in [
                    "BID_ROUTE_SMOKE_SECRET_CHECK_TARGETS",
                    "path.delimiter",
                    "targetFilesFromEnv",
                ]
            )
            and all(
                token in frontend_bid_route_secret_test
                for token in [
                    "mkdtempSync",
                    "runtime-generated",
                    "BID_ROUTE_SMOKE_SECRET_TEST_PASS",
                    "BID_ROUTE_SMOKE_SECRET_CHECK_FAIL",
                    "<redacted>",
                    "credentialValue",
                    "rmSync",
                ]
            )
            and "test:bid-smoke-secrets" in frontend_package_json,
        )
    )
    checks.append(
        check(
            "frontend bid route smoke acceptance preset is standardized",
            all(
                token in frontend_package_json
                for token in [
                    "acceptance:bid-smoke",
                    "pnpm run check:bid-smoke-secrets && pnpm run test:bid-smoke-secrets && pnpm run test:bid-smoke-acceptance-runner && pnpm run test:bid-smoke-command-matrix && pnpm run test:bid-route-production-docs && pnpm run test:bid-route-production-docs-failure && pnpm run test:bid-route-production-docs-drift && pnpm run smoke:bid-route",
                ]
            )
            and all(
                token in frontend_bid_route_runbook
                for token in [
                    "pnpm run acceptance:bid-smoke",
                    "full local smoke gate",
                    "non-secret static guard",
                    "runtime fixture self-test",
                    "local runner preflight self-test",
                    "command matrix self-test",
                    "production-route docs/storage-state guard",
                    "runtime failure fixture",
                    "path override drift fixture",
                    "real `/bid` route smoke",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend bid route smoke local runner is standardized",
            all(
                token in frontend_bid_route_acceptance_runner
                for token in [
                    "BID_BACKEND_DIR",
                    "BID_ACCEPTANCE_READY_TIMEOUT_MS",
                    "BID_ACCEPTANCE_PREFLIGHT_ONLY",
                    "BID_ACCEPTANCE_VERBOSE",
                    "waitForJsonHealth",
                    "waitForFrontend",
                    "terminateProcess",
                    "process.kill(-child.pid",
                    "acceptance:bid-smoke",
                    "BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS",
                    "BID_SMOKE_ACCEPTANCE_LOCAL_PASS",
                ]
            )
            and "acceptance:bid-smoke:local" in frontend_package_json
            and all(
                token in frontend_bid_route_runbook
                for token in [
                    "pnpm run acceptance:bid-smoke:local",
                    "starts temporary FastAPI and Vite",
                    "tears them down",
                    "BID_ACCEPTANCE_PREFLIGHT_ONLY=1",
                    "BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend bid route smoke local runner has preflight self-test",
            all(
                token in frontend_bid_route_acceptance_runner_test
                for token in [
                    "testBidSmokeAcceptanceRunner",
                    "BID_ACCEPTANCE_PREFLIGHT_ONLY",
                    "reserveFreePort",
                    "Bidding API port is already in use",
                    "BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS",
                    "BID_SMOKE_ACCEPTANCE_RUNNER_TEST_PASS",
                    "BID_SMOKE_ACCEPTANCE_LOCAL_PASS",
                ]
            )
            and "test:bid-smoke-acceptance-runner" in frontend_package_json,
        )
    )
    checks.append(
        check(
            "frontend bid route smoke command matrix has self-test",
            all(
                token in frontend_bid_route_command_matrix_test
                for token in [
                    "README_PATH",
                    "commandMatrixSection",
                    "documentedCommands",
                    "packageCommands",
                    "missingFromPackage",
                    "missingFromMatrix",
                    "missingRequiredPackage",
                    "REQUIRED_MATRIX_COMMANDS",
                    "capture:bid-storage-state:prod",
                    "smoke:bid-route:prod",
                    "BID_SMOKE_COMMAND_MATRIX_TEST_PASS",
                ]
            )
            and "test:bid-smoke-command-matrix" in frontend_package_json
            and "pnpm run test:bid-smoke-command-matrix" in frontend_bid_route_runbook,
        )
    )
    checks.append(
        check(
            "frontend bid route smoke command matrix is documented",
            all(
                token in frontend_package_json
                for token in [
                    "acceptance:bid-smoke:preflight",
                    "BID_ACCEPTANCE_PREFLIGHT_ONLY=1 BID_BACKEND_PORT=18000 BID_FRONTEND_PORT=19876",
                ]
            )
            and all(
                token in frontend_bid_route_runbook
                for token in [
                    "## Command matrix",
                    "Service-free CI/preflight",
                    "Local managed services",
                    "Already-running FastAPI + Vite",
                    "Services started",
                    "Expected artifacts",
                    "pnpm run acceptance:bid-smoke:preflight",
                    "pnpm run acceptance:bid-smoke:local",
                    "pnpm run acceptance:bid-smoke",
                    "BID_SMOKE_ACCEPTANCE_PREFLIGHT_PASS",
                    "BID_SMOKE_ACCEPTANCE_LOCAL_PASS",
                    "BID_ROUTE_SMOKE_PASS",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend bid route production command matrix is documented",
            all(
                token in frontend_bid_route_runbook
                for token in [
                    "## Production command matrix",
                    "Capture storage state",
                    "Smoke with captured state",
                    "pnpm run capture:bid-storage-state:prod",
                    "BID_ROUTE_STORAGE_STATE=.auth/bid-route-storage-state.json pnpm run smoke:bid-route:prod",
                    "BID_ROUTE_LOGIN_REQUIRED",
                    ".auth/bid-route-storage-state.json",
                    "BID_ROUTE_SMOKE_PASS",
                    "storage_state",
                ]
            )
            and all(
                token in frontend_bid_route_command_matrix_test
                for token in [
                    "## Production command matrix",
                    "capture:bid-storage-state:prod",
                    "smoke:bid-route:prod",
                    "REQUIRED_MATRIX_COMMANDS",
                ]
            ),
        )
    )
    checks.append(
        check(
            "frontend bid route production docs guard is executable",
            all(
                token in frontend_bid_route_production_docs_test
                for token in [
                    "STORAGE_STATE_DIR = '.auth/'",
                    "STORAGE_STATE_PATH = '.auth/bid-route-storage-state.json'",
                    "ALLOWED_COMMAND_ASSIGNMENTS",
                    "REQUIRED_PRODUCTION_ENV_NAMES",
                    "markdownSection",
                    "commandExamples",
                    "commandAssignments",
                    "lists environment variable names only",
                    "Production environment list must contain names only",
                    "BID_ROUTE_PRODUCTION_DOCS_README",
                    "BID_ROUTE_PRODUCTION_DOCS_TEST_PASS",
                ]
            )
            and "test:bid-route-production-docs" in frontend_package_json
            and "pnpm run test:bid-route-production-docs" in frontend_bid_route_runbook
            and ".auth/" in frontend_gitignore
            and ".auth/bid-route-storage-state.json" in frontend_bid_route_storage_capture
            and "BID_ROUTE_PRODUCTION_DOCS_TEST_PASS" in frontend_bid_route_runbook
            and "pnpm run test:bid-route-production-docs" in frontend_package_json,
        )
    )
    checks.append(
        check(
            "frontend bid route production docs guard has failure fixture",
            all(
                token in frontend_bid_route_production_docs_failure_test
                for token in [
                    "mkdtempSync",
                    "SAFE_STORAGE_COMMAND",
                    "BID_ROUTE_PRODUCTION_DOCS_README",
                    "sensitiveEnvName",
                    "fixtureValue",
                    "Production command example assigns",
                    "Generated production docs fixture value leaked into guard output",
                    "BID_ROUTE_PRODUCTION_DOCS_FAILURE_TEST_PASS",
                    "rmSync",
                ]
            )
            and "test:bid-route-production-docs-failure" in frontend_package_json
            and "pnpm run test:bid-route-production-docs-failure" in frontend_bid_route_runbook
            and "BID_ROUTE_PRODUCTION_DOCS_FAILURE_TEST_PASS" in frontend_bid_route_runbook
            and "testBidRouteProductionDocsFailure.mts" in frontend_bid_route_secret_check,
        )
    )
    checks.append(
        check(
            "frontend bid route production docs guard has path override drift fixture",
            all(
                token in frontend_bid_route_production_docs_drift_test
                for token in [
                    "SOURCE_PATHS",
                    "BID_ROUTE_PRODUCTION_DOCS_CAPTURE_SCRIPT",
                    "BID_ROUTE_PRODUCTION_DOCS_GITIGNORE",
                    "BID_ROUTE_PRODUCTION_DOCS_README",
                    "BID_ROUTE_PRODUCTION_DOCS_SMOKE_SCRIPT",
                    "BID_ROUTE_PRODUCTION_DOCS_TEST_PASS",
                    "capture script default storage-state path is missing",
                    "smoke script storage-state auth artifact is missing",
                    "BID_ROUTE_PRODUCTION_DOCS_DRIFT_TEST_PASS",
                    "runtime-path-overrides",
                ]
            )
            and "test:bid-route-production-docs-drift" in frontend_package_json
            and "pnpm run test:bid-route-production-docs-drift" in frontend_bid_route_runbook
            and "BID_ROUTE_PRODUCTION_DOCS_DRIFT_TEST_PASS" in frontend_bid_route_runbook
            and "testBidRouteProductionDocsDrift.mts" in frontend_bid_route_secret_check,
        )
    )
    checks.append(
        check(
            "frontend evidence tab has material group presets",
            all(
                token in frontend_evidence_tab
                for token in [
                    "Material Group Presets",
                    "qualification_documents",
                    "commercial_pricing_documents",
                    "technical_scoring_attachments",
                ]
            ),
        )
    )
    checks.append(check("frontend review tab shows attachment readiness", all(token in frontend_review_tab for token in ["attachment_readiness", "Attachment Readiness", "needs_page_hint"])))
    checks.append(check("frontend review tab shows scoring readiness", all(token in frontend_review_tab for token in ["scoring_readiness", "Scoring Readiness", "needs_bidder_evidence"])))
    checks.append(check("frontend review tab shows commercial evidence readiness", all(token in frontend_review_tab for token in ["commercial_evidence_readiness", "Commercial Evidence Readiness", "tender_only"])))
    checks.append(check("frontend review tab shows contract obligation readiness", all(token in frontend_review_tab for token in ["contract_obligation_readiness", "Contract Obligation Readiness", "tender_only"])))
    checks.append(
        check(
            "frontend review tab shows action checklist",
            all(token in frontend_review_tab for token in ["action_checklist", "Action Checklist", "owner"]),
        )
    )
    checks.append(
        check(
            "frontend review tab shows action evidence links",
            all(
                token in frontend_review_tab
                for token in [
                    "Action Evidence",
                    "attachmentByEvidenceId",
                    "evidence_ids",
                    "row_ids",
                    "artifact_refs",
                ]
            ),
        )
    )
    checks.append(check("frontend review tab shows material groups", all(token in frontend_review_tab for token in ["material_groups", "Material Groups", "row_ids"])))
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
