"""
Real /bid workbench API adapter.

This layer gives the LobeChat workbench a stable project/artifact contract while
keeping the existing LangGraph workflow available for LLM-driven runs.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .config import settings
from .evidence import search_evidence
from .models import EvidenceItem

ROOT = Path("/root/it-bidding-copilot")
DATA_DIR = Path(settings.BIDDING_DATA_DIR)
VAULT_TENDER = ROOT / "vault/10-Knowledge/Evergreen/招标文件案例.md"

_projects: dict[str, dict[str, Any]] = {}
_next_project_id = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _project_dir(project_id: str) -> Path:
    return DATA_DIR / project_id


def _artifact_dir(project_id: str) -> Path:
    return _project_dir(project_id) / "artifacts"


def _source_dir(project_id: str) -> Path:
    return _project_dir(project_id) / "sources"


def _project_meta_path(project_id: str) -> Path:
    return _project_dir(project_id) / "project.json"


def _load_project(project_id: str) -> dict[str, Any] | None:
    if project_id in _projects:
        return _projects[project_id]

    meta = _project_meta_path(project_id)
    if not meta.exists():
        return None
    project = json.loads(meta.read_text(encoding="utf-8"))
    _projects[project_id] = project
    return project


def _save_project(project: dict[str, Any]) -> None:
    ensure_data_dir()
    pid = str(project["id"])
    _project_dir(pid).mkdir(parents=True, exist_ok=True)
    _artifact_dir(pid).mkdir(parents=True, exist_ok=True)
    _source_dir(pid).mkdir(parents=True, exist_ok=True)
    project["updated_at"] = now_iso()
    _projects[pid] = project
    _project_meta_path(pid).write_text(
        json.dumps(project, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _new_project_id() -> str:
    global _next_project_id
    ensure_data_dir()
    existing = [int(p.name) for p in DATA_DIR.iterdir() if p.is_dir() and p.name.isdigit()]
    _next_project_id = max([_next_project_id, *existing], default=0) + 1
    return str(_next_project_id)


def create_project_record(name: str, bidder: str = "", project_role: str = "") -> dict[str, Any]:
    project_id = _new_project_id()
    project = {
        "id": project_id,
        "name": name,
        "bidder": bidder,
        "project_role": project_role,
        "stage": "created",
        "progress": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "source_files": [],
        "tender_markdown": "",
        "plan": None,
        "execution": None,
        "review": None,
        "draft_sections": [],
        "draft_markdown": "",
    }
    _save_project(project)
    return project


def list_project_records() -> list[dict[str, Any]]:
    ensure_data_dir()
    for meta in DATA_DIR.glob("*/project.json"):
        try:
            project = json.loads(meta.read_text(encoding="utf-8"))
            _projects[str(project["id"])] = project
        except Exception:
            continue
    return sorted(_projects.values(), key=lambda p: p.get("updated_at", ""), reverse=True)


def get_project_record(project_id: str) -> dict[str, Any]:
    project = _load_project(str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def public_project(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(project["id"]),
        "name": project.get("name", ""),
        "bidder": project.get("bidder", ""),
        "stage": project.get("stage", "created"),
        "progress": project.get("progress", 0),
        "created_at": project.get("created_at", ""),
        "updated_at": project.get("updated_at", ""),
    }


def project_detail(project: dict[str, Any]) -> dict[str, Any]:
    return {
        **public_project(project),
        "source_files": project.get("source_files", []),
        "plan": project.get("plan"),
        "execution": project.get("execution"),
        "review": project.get("review"),
        "draft_sections": project.get("draft_sections", []),
        "draft_markdown": project.get("draft_markdown", ""),
    }


def attach_source_file(project_id: str, filename: str, contents: bytes, purpose: str, markdown: str) -> dict[str, Any]:
    project = get_project_record(project_id)
    _source_dir(project_id).mkdir(parents=True, exist_ok=True)
    source_path = _source_dir(project_id) / filename
    source_path.write_bytes(contents)

    record = {
        "filename": filename,
        "source_type": purpose,
        "parse_status": "parsed" if markdown else "uploaded",
        "path": str(source_path),
        "markdown_chars": len(markdown),
    }
    project.setdefault("source_files", []).append(record)
    if purpose == "tender":
        project["tender_markdown"] = markdown
    _save_project(project)
    return record


def evidence_id(item: EvidenceItem) -> str:
    return f"EVID-{item.id}"


def evidence_result(item: EvidenceItem) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id(item),
        "title": item.title or "",
        "category": item.category or "",
        "sub_type": item.sub_type or "",
        "summary": item.summary or "",
        "source_doc": item.source_doc or "",
        "heading_path": item.source_section or "",
        "content": item.text_content or "",
        "asset_paths": item.image_paths or [],
        "verified_status": "traceable",
        "page_hint": item.source_page or "",
    }


def search_evidence_payload(db: Session, query: str, category: str | None = None, top_k: int = 10) -> dict[str, Any]:
    items = search_evidence(db, query=query, category=category, top_k=top_k)
    return {
        "query": query,
        "category": category,
        "count": len(items),
        "results": [evidence_result(item) for item in items],
    }


def _clean_line(line: str) -> str:
    line = re.sub(r"<[^>]+>", "", line)
    line = re.sub(r"^#+\s*", "", line.strip())
    line = line.replace("**", "").replace("__", "").strip("> ")
    line = re.sub(r"\s+", " ", line).strip(" |　\t")
    return line


def _md_cell(value: Any) -> str:
    """Escape a value for safe use inside a Markdown table cell."""
    text = _clean_line(str(value))
    text = text.replace("\\", "\\\\").replace("|", "\\|")
    return text.replace("\n", "<br>")


def _plain_requirement(value: str) -> str:
    return _clean_line(value).replace("|", " / ")


def _extract_marked_items(markdown: str, mark: str, limit: int = 12) -> list[str]:
    items: list[str] = []
    for raw in markdown.splitlines():
        if mark not in raw:
            continue
        line = _clean_line(raw)
        if len(line) < 8 or line in items:
            continue
        items.append(line[:220])
        if len(items) >= limit:
            break
    return items


def _default_hard_clauses() -> list[str]:
    return [
        "▲ 投标人必须具有独立承担民事责任的能力，并提供有效营业执照。",
        "▲ 投标人需提供所投核心云平台产品原厂授权书及售后服务承诺函。",
        "▲ 投标人需具备 ISO9001 质量管理体系认证证书。",
        "▲ 投标人需具备近三年金额不少于200万元的类似私有云建设项目成功案例。",
        "▲ 建设交付的平台应满足等保三级相关技术要求。",
    ]


def _default_tech_requirements() -> list[str]:
    return [
        "△ 平台需支持计算、存储、网络等资源的统一管理和编排。",
        "△ 计算虚拟化需支持平滑升级，且不中断业务虚拟机。",
        "△ 采用分布式存储架构，需提供至少50TB的可用块存储容量。",
        "△ 平台自带虚拟防火墙功能，支持微隔离。",
    ]


def _scoring_items(markdown: str) -> list[dict[str, str]]:
    candidates = [
        ("商务资信-体系认证", "5分", "具备 ISO27001 信息安全管理体系认证得分。"),
        ("商务资信-类似案例", "15分", "在资格案例基础上增加有效类似案例可得分。"),
        ("技术方案-整体架构设计合理性", "15分", "方案先进性、高可用性、可扩展性支撑评分。"),
        ("技术方案-技术指标响应程度", "25分", "带△指标不得负偏离，一般指标避免失分。"),
        ("技术方案-项目实施及售后团队", "10分", "项目经理 PMP 及高级软考等证书支撑评分。"),
    ]
    if "ISO27001" not in markdown:
        candidates = candidates[1:]
    return [{"name": name, "score": score, "rule": rule} for name, score, rule in candidates]


def _query_for(text: str) -> str:
    rules = [
        ("实质性内容", "实质性 内容 明确响应 无效"),
        ("明确响应", "实质性 内容 明确响应 无效"),
        ("投标报价", "投标报价 报价要求"),
        ("付款方式", "付款方式 发票 合同价款"),
        ("履约保证金", "履约保证金"),
        ("营业执照", "营业执照 独立承担民事责任"),
        ("授权", "授权书 售后服务承诺函 原厂"),
        ("ISO9001", "ISO9001 质量管理体系认证"),
        ("ISO27001", "ISO27001 信息安全管理体系认证"),
        ("案例", "相关业绩 合同 私有云 案例"),
        ("PMP", "PMP 高级软考 项目负责人证书"),
        ("软考", "PMP 高级软考 项目负责人证书"),
        ("等保", "等保三级 安全 微隔离 防火墙"),
        ("分布式存储", "分布式存储 块存储 可用容量"),
        ("防火墙", "虚拟防火墙 微隔离"),
        ("平滑升级", "热迁移 平滑升级 虚拟化"),
        ("统一管理", "统一管理 编排 云平台"),
    ]
    for key, query in rules:
        if key in text:
            return query
    return text[:80]


def _find_evidence(db: Session, text: str, top_k: int = 3) -> list[dict[str, Any]]:
    return [evidence_result(item) for item in search_evidence(db, _query_for(text), top_k=top_k)]


def generate_plan(project_id: str, db: Session) -> dict[str, Any]:
    project = get_project_record(project_id)
    tender = project.get("tender_markdown") or ""
    if not tender:
        raise HTTPException(status_code=400, detail="No tender document uploaded")

    hard = _extract_marked_items(tender, "▲", 10) or _default_hard_clauses()
    tech = _extract_marked_items(tender, "△", 10) or _default_tech_requirements()
    scoring = _scoring_items(tender)

    evidence_items = []
    missing_materials = []
    material_checks = [
        "营业执照",
        "原厂授权书及售后服务承诺函",
        "ISO9001 质量管理体系认证",
        "ISO27001 信息安全管理体系认证",
        "近三年类似私有云建设项目合同案例",
        "项目经理 PMP 及高级软考证书",
    ]
    for name in material_checks:
        found = _find_evidence(db, name, top_k=2)
        status = "available" if found else "missing"
        evidence_items.append({"name": name, "status": status, "evidence_ids": [e["evidence_id"] for e in found]})
        if not found:
            missing_materials.append({"name": name, "status": "missing", "risk": "hard" if name != "ISO27001 信息安全管理体系认证" else "scoring"})

    plan = {
        "project_info": {
            "name": project.get("name"),
            "bidder": project.get("bidder"),
            "tender_chars": len(tender),
        },
        "requirements_count": len(hard) + len(tech),
        "scoring_items_count": len(scoring),
        "hard_clauses_count": len(hard),
        "hard_clauses": hard,
        "technical_requirements": tech,
        "scoring_items": scoring,
        "missing_materials": missing_materials,
        "evidence_items": evidence_items,
    }
    project["plan"] = plan
    project["stage"] = "planned"
    project["progress"] = 35
    _write_artifact(project_id, "plan.md", _plan_markdown(plan))
    _save_project(project)
    return {"project_id": project_id, "status": "planned", "plan": plan}


def _plan_markdown(plan: dict[str, Any]) -> str:
    lines = ["# Plan", "", "## 项目信息", ""]
    for key, value in plan["project_info"].items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## 硬性条款"]
    lines += [f"- {item}" for item in plan["hard_clauses"]]
    lines += ["", "## 技术指标"]
    lines += [f"- {item}" for item in plan["technical_requirements"]]
    lines += ["", "## 评分项"]
    lines += [f"- {item['name']} ({item['score']}): {item['rule']}" for item in plan["scoring_items"]]
    lines += ["", "## 缺失材料"]
    if plan["missing_materials"]:
        lines += [f"- {item['name']} [{item['risk']}]" for item in plan["missing_materials"]]
    else:
        lines.append("- 暂未发现")
    lines += ["", "## 证据检索"]
    for item in plan["evidence_items"]:
        ids = ", ".join(item["evidence_ids"]) or "无"
        lines.append(f"- {item['name']}: {item['status']} ({ids})")
    return "\n".join(lines) + "\n"


def approve_plan(project_id: str) -> dict[str, Any]:
    project = get_project_record(project_id)
    if not project.get("plan"):
        raise HTTPException(status_code=400, detail="Plan has not been generated")
    project["stage"] = "approved"
    project["progress"] = 45
    _save_project(project)
    return {"project_id": project_id, "status": "approved"}


def generate_execution(project_id: str, db: Session) -> dict[str, Any]:
    project = get_project_record(project_id)
    if not project.get("plan"):
        generate_plan(project_id, db)
        project = get_project_record(project_id)
    plan = project["plan"]

    rows: list[dict[str, Any]] = []
    for idx, clause in enumerate(plan["hard_clauses"], 1):
        rows.append(_matrix_row(db, f"H{idx}", "hard_clause", clause, "必须响应，缺证据时不得写成已满足。"))
    for idx, req in enumerate(plan["technical_requirements"], 1):
        rows.append(_matrix_row(db, f"T{idx}", "technical_requirement", req, "逐条响应，不得负偏离。"))
    for idx, item in enumerate(plan["scoring_items"], 1):
        rows.append(_matrix_row(db, f"S{idx}", "scoring_item", f"{item['name']} {item['score']} {item['rule']}", "按评分点补强章节和附件索引。"))

    evidence_trace = []
    for row in rows:
        for item in row["evidence"]:
            evidence_trace.append(
                {
                    "row_id": row["id"],
                    "evidence_id": item["evidence_id"],
                    "title": item["title"],
                    "source_doc": item["source_doc"],
                    "heading_path": item["heading_path"],
                    "page_hint": item["page_hint"],
                    "asset_paths": item.get("asset_paths", []),
                }
            )

    draft = _draft_markdown(project, rows)
    response_matrix = _matrix_markdown(rows)
    _write_artifact(project_id, "response_matrix.md", response_matrix)
    _write_artifact(project_id, "draft.md", draft)
    _write_artifact(project_id, "evidence_trace.json", json.dumps(evidence_trace, ensure_ascii=False, indent=2))

    project["execution"] = {
        "response_matrix_rows": len(rows),
        "scoring_table_rows": len(plan["scoring_items"]),
        "draft_sections": 4,
        "missing_materials": [{"name": row["requirement"], "status": "missing_evidence"} for row in rows if not row["evidence"]],
    }
    project["draft_sections"] = [
        {"name": "商务偏离表", "artifact": "draft.md"},
        {"name": "技术偏离表", "artifact": "draft.md"},
        {"name": "技术方案", "artifact": "draft.md"},
        {"name": "售后服务方案", "artifact": "draft.md"},
    ]
    project["draft_markdown"] = draft
    project["stage"] = "executed"
    project["progress"] = 75
    _save_project(project)
    return {"project_id": project_id, "status": "executed", **project["execution"]}


def _matrix_row(db: Session, row_id: str, row_type: str, requirement: str, response_strategy: str) -> dict[str, Any]:
    evidence = _find_evidence(db, requirement, top_k=3)
    return {
        "id": row_id,
        "type": row_type,
        "requirement": _plain_requirement(requirement),
        "response_strategy": response_strategy,
        "evidence": evidence,
        "status": "covered" if evidence else "missing_evidence",
    }


def _matrix_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Response Matrix",
        "",
        "| ID | 类型 | 招标要求/评分点 | 响应策略 | 证据ID | 状态 |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        ids = ", ".join(item["evidence_id"] for item in row["evidence"]) or "待补充"
        lines.append(
            f"| {_md_cell(row['id'])} | {_md_cell(row['type'])} | {_md_cell(row['requirement'])} | {_md_cell(row['response_strategy'])} | {_md_cell(ids)} | {_md_cell(row['status'])} |"
        )
    return "\n".join(lines) + "\n"


def _draft_markdown(project: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    hard = [row for row in rows if row["type"] == "hard_clause"]
    tech = [row for row in rows if row["type"] == "technical_requirement"]
    scoring = [row for row in rows if row["type"] == "scoring_item"]

    lines = [
        "# 投标文件草稿",
        "",
        f"项目名称：{project.get('name', '')}",
        f"投标人：{project.get('bidder') or '待填写'}",
        "",
        "## 一、商务响应及偏离表",
        "",
        "| 序号 | 招标要求 | 投标响应 | 偏离说明 | 证据链 |",
        "|---|---|---|---|---|",
    ]
    for idx, row in enumerate(hard, 1):
        ids = _ids(row)
        response = "已按要求响应，详见证据链。" if ids else "待补充对应证明材料，正式稿不得写成已提供。"
        deviation = "无偏离" if ids else "材料待补充"
        lines.append(f"| {idx} | {_md_cell(row['requirement'])} | {_md_cell(response)} | {_md_cell(deviation)} | {_md_cell(ids or '待补充')} |")

    lines += [
        "",
        "## 二、技术响应及偏离表",
        "",
        "| 序号 | 技术要求 | 投标响应 | 偏离说明 | 证据链 |",
        "|---|---|---|---|---|",
    ]
    for idx, row in enumerate(tech, 1):
        ids = _ids(row)
        response = "采用成熟私有云平台能力逐项响应，并在技术方案中展开实现路径。"
        if not ids:
            response = "能力描述需补充截图、产品白皮书或原厂证明后进入正式稿。"
        lines.append(
            f"| {idx} | {_md_cell(row['requirement'])} | {_md_cell(response)} | {_md_cell('无偏离' if ids else '证据待补充')} | {_md_cell(ids or '待补充')} |"
        )

    lines += [
        "",
        "## 三、技术方案",
        "",
        "### 3.1 整体架构设计",
        "本项目建议采用分层解耦的私有云架构，覆盖计算虚拟化、分布式块存储、SDN 网络、安全微隔离、统一运维与服务编排。方案以 response matrix 为约束源，所有涉及资格、评分和技术指标的陈述均回链到证据材料。",
        "",
        "### 3.2 关键能力实现",
    ]
    for row in tech:
        evidence_refs = _evidence_refs(row)
        lines += [
            "",
            f"#### {row['id']} {_plain_requirement(row['requirement'])}",
            "",
            f"- 响应口径：本项按招标指标逐条正向响应，正式稿应保持与偏离表、截图证明和附件索引一致，不写无证据的扩展能力。",
            f"- 实现要点：{_implementation_note(row['requirement'])}",
            f"- 证据定位：{evidence_refs or '缺少直接证据，需补充截图、产品白皮书或原厂证明后进入正式稿'}。",
        ]

    lines += [
        "",
        "### 3.3 评分点支撑",
        "",
        "| 评分项 | 响应要点 | 证据定位 | 就绪状态 | 人工复核 |",
        "|---|---|---|---|---|",
    ]
    for row in scoring:
        lines.append(
            f"| {_md_cell(row['requirement'])} | {_md_cell(_scoring_response_note(row['requirement']))} | {_md_cell(_evidence_refs(row) or '缺少直接证据，列入补材料清单')} | {_md_cell(_row_readiness(row))} | {_md_cell(_scoring_manual_check(row['requirement']))} |"
        )

    lines += [
        "",
        "## 四、售后服务方案",
        "",
        "投标人承诺建立项目经理、云平台实施工程师、安全工程师和售后响应团队组成的服务组织，提供项目实施、培训、质保和运维支持。人员证书、服务承诺函和原厂支持文件必须在正式稿附件目录中逐项索引。",
        "",
        "## 五、材料补充清单",
    ]
    missing = [row for row in rows if not row["evidence"]]
    if missing:
        lines += [f"- {row['id']} {_plain_requirement(row['requirement'])}" for row in missing]
    else:
        lines.append("- 当前 response matrix 均已有可追溯 evidence_id。")

    lines += [
        "",
        "## 六、证据索引",
        "",
        "| 证据ID | 标题 | 来源文件 | 来源位置 | 页码/资产提示 | 装订状态 |",
        "|---|---|---|---|---|---|",
    ]
    seen: set[str] = set()
    for row in rows:
        for item in row["evidence"]:
            if item["evidence_id"] in seen:
                continue
            seen.add(item["evidence_id"])
            page_or_asset = _page_or_asset_hint(item)
            lines.append(
                f"| {_md_cell(item['evidence_id'])} | {_md_cell(item['title'])} | {_md_cell(item['source_doc'])} | {_md_cell(item['heading_path'])} | {_md_cell(page_or_asset or '需回填页码')} | {_md_cell(_binding_status(item))} |"
            )
    return "\n".join(lines) + "\n"


def _ids(row: dict[str, Any]) -> str:
    return ", ".join(item["evidence_id"] for item in row["evidence"])


def _evidence_refs(row: dict[str, Any]) -> str:
    refs = []
    for item in row["evidence"][:3]:
        refs.append(f"{item['evidence_id']}（{_clean_line(item['title'])}）")
    return "；".join(refs)


def _implementation_note(requirement: str) -> str:
    text = _plain_requirement(requirement)
    rules = [
        (
            ["镜像", "OVA"],
            "围绕镜像生命周期写明格式导入、模板管理、虚拟机导出和截图证明口径，重点证明 ISO、raw、qcow2、vmdk、ovf 与 OVA 导出的可操作路径。",
        ),
        (
            ["ARM", "X86", "MIPS", "一云多芯"],
            "围绕一云多芯兼容性写明异构 CPU 纳管边界、兼容性证书和适配清单，避免只写平台支持而缺少芯片厂商互认证材料。",
        ),
        (
            ["EC算法", "纠删", "2+1", "4+2", "8+2"],
            "围绕纠删码保护机制写明数据可靠性、容量利用率和 2+1、4+2、8+2 等保护级别，证据应指向产品功能说明或界面截图。",
        ),
        (
            ["副本", "拓扑", "权重"],
            "围绕分布式存储策略写明副本数调整、在线变更和拓扑权重配置，并把管理界面截图与存储策略说明放入同一附件组。",
        ),
        (
            ["缓存池", "数据池"],
            "围绕缓存池与数据池解耦写明独立部署、独立扩容和业务影响边界，证据应能对应到存储池配置或架构说明。",
        ),
        (
            ["CDP", "文件找回"],
            "围绕 CDP 备份恢复写明连续数据保护、文件级找回流程和支持的文件系统范围，截图或操作说明需能支撑 XFS、Ext、exFAT、NTFS、FAT32 等指标。",
        ),
        (
            ["资源中心", "配额"],
            "围绕资源中心展示写明组织视图、云主机、云硬盘、网络、安全组及 vCPU、内存、主存储配额统计，并以界面截图证明可视化能力。",
        ),
        (
            ["数据中心管理", "快速创建"],
            "围绕数据中心管理写明按云平台类型汇总资源、快速创建入口和管理员角色操作边界，证据应指向数据中心或多云管理界面截图。",
        ),
        (
            ["服务编排", "服务目录"],
            "围绕服务目录编排写明一次性申请跨云资源、审批或交付流程和资源组合能力，证据应能对应服务目录或编排界面。",
        ),
        (
            ["高负载", "低负载", "空闲云主机", "列表导出"],
            "围绕优化建议写明内置规则识别高负载、低负载、空闲云主机，并说明列表导出作为运维闭环材料。",
        ),
    ]
    for keywords, note in rules:
        if any(keyword in text for keyword in keywords):
            return note
    return "围绕该技术指标拆分管理界面、配置流程、截图证明和附件位置，确保每项能力均能回链到响应矩阵中的 evidence_id。"


def _scoring_response_note(requirement: str) -> str:
    text = _plain_requirement(requirement)
    if "体系认证" in text or "ISO27001" in text:
        return "按证书名称、认证范围、有效期和投标主体一致性整理资信证明，放入商务资信附件。"
    if "类似案例" in text:
        return "按项目名称、合同金额、建设内容、验收或合同关键页整理案例清单，优先选择与私有云建设匹配的业绩。"
    if "整体架构" in text:
        return "围绕先进性、高可用性、可扩展性组织架构图、资源池设计、容灾与运维说明，并回链到方案章节。"
    if "技术指标" in text:
        return "将技术偏离表、功能截图和响应矩阵逐项交叉引用，确保带△指标无负偏离且可快速定位。"
    if "实施" in text or "团队" in text or "项目经理" in text:
        return "按项目经理、实施团队、原厂支持、PMP/高级软考和社保证明整理人员材料，形成团队得分附件组。"
    return "按评分细则拆分响应要点、证明材料、附件页码和人工复核事项。"


def _scoring_manual_check(requirement: str) -> str:
    text = _plain_requirement(requirement)
    if "体系认证" in text or "ISO27001" in text:
        return "复核证书有效期、认证范围、主体名称和盖章页。"
    if "类似案例" in text:
        return "复核合同金额、签署日期、建设内容、验收材料和脱敏页码。"
    if "整体架构" in text:
        return "复核架构图、容量/高可用描述和讲标口径一致。"
    if "技术指标" in text:
        return "复核每个△指标的截图编号、页码和偏离表一致性。"
    if "实施" in text or "团队" in text or "项目经理" in text:
        return "复核团队人员证书、社保、授权和原厂实施承诺。"
    return "复核材料真实性、页码和签章状态。"


def _row_readiness(row: dict[str, Any]) -> str:
    if not row["evidence"]:
        return "缺少直接证据"
    bidder_items = [item for item in row["evidence"] if not _is_tender_source(str(item.get("source_doc") or ""))]
    if not bidder_items:
        return "仅招标依据，需补投标人材料"
    if any(_binding_status(item) == "需回填页码" for item in bidder_items):
        return "需回填页码/附件编号"
    return "可定位"


def _page_or_asset_hint(item: dict[str, Any]) -> str:
    if item.get("page_hint"):
        return str(item["page_hint"])
    asset_paths = item.get("asset_paths") or []
    if asset_paths:
        return ", ".join(Path(str(path)).name for path in asset_paths[:3])
    return ""


def _is_tender_source(source_doc: str) -> bool:
    return "招标文件" in source_doc or source_doc.startswith("招标")


def _binding_status(item: dict[str, Any]) -> str:
    source_doc = str(item.get("source_doc") or "")
    if _is_tender_source(source_doc):
        return "招标依据"
    return "可定位" if _page_or_asset_hint(item) else "需回填页码"


def _split_md_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]

    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    cells.append("".join(current).strip())
    return cells


def _matrix_rows_from_markdown(matrix_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in matrix_text.splitlines():
        if not line.startswith("| ") or line.startswith("| ID") or line.startswith("|---"):
            continue
        cells = _split_md_row(line)
        if len(cells) != 6:
            continue
        rows.append(
            {
                "id": cells[0],
                "type": cells[1],
                "requirement": cells[2],
                "strategy": cells[3],
                "evidence_ids": cells[4],
                "status": cells[5],
            }
        )
    return rows


def _review_finding(severity: str, area: str, message: str, suggestion: str, bucket: str) -> dict[str, str]:
    return {"severity": severity, "area": area, "message": message, "suggestion": suggestion, "bucket": bucket}


def _load_evidence_trace(project_id: str) -> list[dict[str, Any]]:
    try:
        trace = json.loads(read_artifact_text(project_id, "evidence_trace.json"))
    except Exception:
        return []
    return trace if isinstance(trace, list) else []


def _attachment_readiness(trace: list[dict[str, Any]]) -> dict[str, Any]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in trace:
        evidence_id = str(item.get("evidence_id") or "")
        if not evidence_id:
            continue
        record = indexed.setdefault(
            evidence_id,
            {
                "evidence_id": evidence_id,
                "title": _clean_line(item.get("title") or ""),
                "source_doc": item.get("source_doc") or "",
                "heading_path": _clean_line(item.get("heading_path") or ""),
                "page_hint": item.get("page_hint") or "",
                "asset_paths": [],
                "row_ids": set(),
            },
        )
        if item.get("page_hint") and not record["page_hint"]:
            record["page_hint"] = item["page_hint"]
        for path in item.get("asset_paths") or []:
            if path not in record["asset_paths"]:
                record["asset_paths"].append(path)
        if item.get("row_id"):
            record["row_ids"].add(item["row_id"])

    records: list[dict[str, Any]] = []
    for record in indexed.values():
        record["row_ids"] = sorted(record["row_ids"])
        record["page_or_asset"] = _page_or_asset_hint(record)
        record["status"] = _binding_status(record)
        records.append(record)

    bidder_records = [item for item in records if item["status"] != "招标依据"]
    ready_records = [item for item in bidder_records if item["status"] == "可定位"]
    missing_records = [item for item in bidder_records if item["status"] == "需回填页码"]
    return {
        "total": len(records),
        "bidder_total": len(bidder_records),
        "ready": len(ready_records),
        "needs_page_hint": len(missing_records),
        "tender_references": len(records) - len(bidder_records),
        "records": sorted(records, key=lambda item: (item["status"] == "需回填页码", item["evidence_id"])),
        "missing_records": missing_records,
    }


def _scoring_readiness(scoring_rows: list[dict[str, str]], attachment_readiness: dict[str, Any]) -> dict[str, Any]:
    evidence_by_id = {item["evidence_id"]: item for item in attachment_readiness.get("records", [])}
    rows: list[dict[str, Any]] = []
    for row in scoring_rows:
        evidence_ids = re.findall(r"EVID-\d+", row["evidence_ids"])
        evidence_records = [evidence_by_id[evidence_id] for evidence_id in evidence_ids if evidence_id in evidence_by_id]
        bidder_records = [item for item in evidence_records if item["status"] != "招标依据"]

        if row["status"] == "missing_evidence" or not evidence_ids:
            status = "missing_evidence"
        elif not bidder_records:
            status = "needs_bidder_evidence"
        elif any(item["status"] == "需回填页码" for item in bidder_records):
            status = "needs_page_hint"
        else:
            status = "ready"

        rows.append(
            {
                "row_id": row["id"],
                "requirement": row["requirement"],
                "evidence_ids": evidence_ids,
                "status": status,
                "manual_check": _scoring_manual_check(row["requirement"]),
                "missing_evidence_ids": [item["evidence_id"] for item in bidder_records if item["status"] == "需回填页码"],
            }
        )

    return {
        "ready": sum(1 for row in rows if row["status"] == "ready"),
        "total": len(rows),
        "needs_page_hint": sum(1 for row in rows if row["status"] == "needs_page_hint"),
        "needs_bidder_evidence": sum(1 for row in rows if row["status"] == "needs_bidder_evidence"),
        "missing_evidence": sum(1 for row in rows if row["status"] == "missing_evidence"),
        "rows": rows,
        "not_ready_rows": [row for row in rows if row["status"] != "ready"],
    }


def generate_review(project_id: str) -> dict[str, Any]:
    project = get_project_record(project_id)
    matrix_text = read_artifact_text(project_id, "response_matrix.md")
    if not matrix_text:
        raise HTTPException(status_code=400, detail="Execution artifacts not found")

    attachment_readiness = _attachment_readiness(_load_evidence_trace(project_id))
    data_rows = _matrix_rows_from_markdown(matrix_text)
    missing_rows = [row for row in data_rows if row["status"] == "missing_evidence"]
    hard_rows = [row for row in data_rows if row["type"] == "hard_clause"]
    scoring_rows = [row for row in data_rows if row["type"] == "scoring_item"]
    scoring_readiness = _scoring_readiness(scoring_rows, attachment_readiness)
    missing_hard = [row for row in missing_rows if row["type"] == "hard_clause"]
    missing_scoring = [row for row in missing_rows if row["type"] == "scoring_item"]
    commercial_rows = [
        row
        for row in hard_rows
        if any(keyword in row["requirement"] for keyword in ["报价", "付款", "履约保证金", "发票", "投标有效期"])
    ]
    total_rows = len(data_rows)
    covered_rows = max(total_rows - len(missing_rows), 0)

    findings: list[dict[str, str]] = []
    for row in missing_rows:
        severity = "high" if row["type"] == "hard_clause" else "medium"
        area = "废标风险" if severity == "high" else "评分点风险"
        message = f"该条款缺少可回溯 evidence_id：{row['requirement']}。正式稿不得宣称已提供证明材料。"
        findings.append(_review_finding(severity, area, message, "补充真实附件或将响应改为待补充。", area))

    if commercial_rows:
        findings.append(
            _review_finding(
                "medium",
                "商务条款风险",
                f"报价、付款、履约保证金等 {len(commercial_rows)} 条高风险商务条款已覆盖证据，但正式稿仍需复核金额、税率、发票类型和保证金口径。",
                "由商务负责人对开标一览表、报价明细、合同付款条款和保证金承诺逐项签核。",
                "商务条款风险",
            )
        )

    if scoring_rows and not missing_scoring:
        findings.append(
            _review_finding(
                "low",
                "评分点风险",
                "评分点均有 evidence_id，但正式附件目录仍需按评分细则逐项映射，避免评委无法快速定位得分材料。",
                "在装订稿中按评分项回填附件页码，并与证据索引交叉校验。",
                "评分点风险",
            )
        )
    if scoring_readiness["not_ready_rows"]:
        sample = ", ".join(row["row_id"] for row in scoring_readiness["not_ready_rows"][:5])
        findings.append(
            _review_finding(
                "medium",
                "评分就绪度",
                f"评分项 {scoring_readiness['ready']}/{scoring_readiness['total']} 已达到附件可定位状态，仍需处理：{sample}。",
                "按评分清单补齐投标人侧证明、页码或截图编号，并由商务/技术负责人签核。",
                "评分点风险",
            )
        )

    if "投标人待填写" in project.get("draft_markdown", ""):
        findings.append(
            _review_finding(
                "medium",
                "签章与主体信息",
                "投标人名称仍为待填写，正式投标文件存在主体信息不完整风险。",
                "回填投标人全称并同步封面、授权书、偏离表。",
                "签章与材料风险",
            )
        )

    findings.append(
        _review_finding(
            "low",
            "材料索引",
            "正式装订前需回填附件页码、签章状态和原件/复印件一致性。",
            "由装订稿页码回填证据索引。",
            "签章与材料风险",
        )
    )
    if attachment_readiness["needs_page_hint"]:
        sample = ", ".join(item["evidence_id"] for item in attachment_readiness["missing_records"][:8])
        findings.append(
            _review_finding(
                "medium",
                "附件就绪度",
                f"投标人侧证据 {attachment_readiness['ready']}/{attachment_readiness['bidder_total']} 具备页码或资产提示，仍有 {attachment_readiness['needs_page_hint']} 项需回填定位信息：{sample}。",
                "正式装订前按证据索引补齐页码、截图编号或附件文件名，并复核与响应矩阵条款一致。",
                "签章与材料风险",
            )
        )

    risk_buckets = [
        {
            "name": "废标风险",
            "severity": "high",
            "status": "blocked" if missing_hard else "clear",
            "items": [f"{row['id']} {row['requirement']}" for row in missing_hard] or ["未发现未覆盖的硬性条款。"],
        },
        {
            "name": "商务条款风险",
            "severity": "medium",
            "status": "needs_review" if commercial_rows else "clear",
            "items": [f"{row['id']} {row['requirement']}：{row['evidence_ids']}" for row in commercial_rows]
            or ["未提取到报价、付款、履约保证金等高风险商务条款。"],
        },
        {
            "name": "评分点风险",
            "severity": "medium",
            "status": "blocked" if missing_scoring else "needs_index" if scoring_readiness["not_ready_rows"] else "clear",
            "items": [f"{row['id']} {row['requirement']}" for row in missing_scoring]
            or [f"{row['row_id']} {row['status']}：{row['requirement']}" for row in scoring_readiness["not_ready_rows"]]
            or ["评分点均已覆盖，且投标人侧证据已达到可定位状态。"],
        },
        {
            "name": "签章与材料风险",
            "severity": "medium",
            "status": "needs_completion",
            "items": [item["message"] for item in findings if item["bucket"] == "签章与材料风险"],
        },
    ]

    review = {
        "score_coverage": {"covered": covered_rows, "total": total_rows},
        "hard_clause_coverage": {
            "covered": sum(1 for row in hard_rows if row["status"] == "covered"),
            "total": len(hard_rows),
        },
        "attachment_readiness": attachment_readiness,
        "scoring_readiness": scoring_readiness,
        "risk_buckets": risk_buckets,
        "findings": findings,
    }
    _write_artifact(project_id, "review.md", _review_markdown(review))
    project["review"] = review
    project["stage"] = "reviewed"
    project["progress"] = 100
    _save_project(project)
    return {"project_id": project_id, "status": "reviewed", **review}


def _review_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# Review",
        "",
        f"- 评分覆盖：{review['score_coverage']['covered']}/{review['score_coverage']['total']}",
        f"- 硬性条款覆盖：{review['hard_clause_coverage']['covered']}/{review['hard_clause_coverage']['total']}",
        f"- 附件就绪度：{review['attachment_readiness']['ready']}/{review['attachment_readiness']['bidder_total']}",
        f"- 评分就绪度：{review['scoring_readiness']['ready']}/{review['scoring_readiness']['total']}",
        "",
        "## 风险分桶",
        "",
    ]
    for bucket in review.get("risk_buckets", []):
        lines.extend(
            [
                f"### {bucket['name']}",
                f"- 严重级别：{bucket['severity']}",
                f"- 状态：{bucket['status']}",
            ]
        )
        for item in bucket.get("items", []):
            lines.append(f"- {item}")
        lines.append("")

    lines += [
        "## 附件就绪度",
        "",
        f"- 投标人侧证据：{review['attachment_readiness']['ready']}/{review['attachment_readiness']['bidder_total']} 可定位",
        f"- 招标依据引用：{review['attachment_readiness']['tender_references']}",
        "",
        "| 证据ID | 涉及条款 | 来源文件 | 页码/资产提示 | 装订状态 |",
        "|---|---|---|---|---|",
    ]
    for item in review["attachment_readiness"]["records"]:
        lines.append(
            f"| {_md_cell(item['evidence_id'])} | {_md_cell(', '.join(item['row_ids']))} | {_md_cell(item['source_doc'])} | {_md_cell(item['page_or_asset'] or '需回填页码')} | {_md_cell(item['status'])} |"
        )

    lines += [
        "",
        "## 评分就绪度",
        "",
        f"- 评分项就绪：{review['scoring_readiness']['ready']}/{review['scoring_readiness']['total']}",
        f"- 需回填页码/附件编号：{review['scoring_readiness']['needs_page_hint']}",
        f"- 需补投标人材料：{review['scoring_readiness']['needs_bidder_evidence']}",
        "",
        "| 评分项 | 证据ID | 就绪状态 | 人工复核 |",
        "|---|---|---|---|",
    ]
    for item in review["scoring_readiness"]["rows"]:
        lines.append(
            f"| {_md_cell(item['row_id'] + ' ' + item['requirement'])} | {_md_cell(', '.join(item['evidence_ids']) or '待补充')} | {_md_cell(item['status'])} | {_md_cell(item['manual_check'])} |"
        )

    lines += [
        "",
        "## 质检发现",
    ]
    if review["findings"]:
        for item in review["findings"]:
            lines.append(f"- [{item['severity']}] {item['area']}: {item['message']} 建议：{item['suggestion']}")
    else:
        lines.append("- 未发现缺材料或废标风险。")
    return "\n".join(lines) + "\n"


def _write_artifact(project_id: str, name: str, content: str) -> None:
    _artifact_dir(project_id).mkdir(parents=True, exist_ok=True)
    (_artifact_dir(project_id) / name).write_text(content, encoding="utf-8")


def list_project_artifacts(project_id: str) -> list[dict[str, Any]]:
    get_project_record(project_id)
    artifact_dir = _artifact_dir(project_id)
    if not artifact_dir.exists():
        return []
    artifacts = []
    for path in sorted(artifact_dir.iterdir()):
        if path.is_file():
            stat = path.stat()
            artifacts.append({"name": path.name, "size": stat.st_size, "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()})
    return artifacts


def read_artifact_text(project_id: str, artifact_name: str) -> str:
    get_project_record(project_id)
    path = (_artifact_dir(project_id) / artifact_name).resolve()
    artifact_root = _artifact_dir(project_id).resolve()
    if artifact_root not in path.parents and path != artifact_root:
        raise HTTPException(status_code=400, detail="Invalid artifact path")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return path.read_text(encoding="utf-8")


def artifact_response(project_id: str, artifact_name: str) -> PlainTextResponse:
    return PlainTextResponse(read_artifact_text(project_id, artifact_name), media_type="text/markdown; charset=utf-8")


def run_demo_real_case(db: Session) -> dict[str, Any]:
    if not VAULT_TENDER.exists():
        raise HTTPException(status_code=404, detail="Real tender case not found")

    project = create_project_record("真实案例验收 - 私有云建设项目", bidder="投标人待填写", project_role="demo")
    tender = VAULT_TENDER.read_text(encoding="utf-8")
    project["tender_markdown"] = tender
    project["source_files"].append(
        {
            "filename": VAULT_TENDER.name,
            "source_type": "tender",
            "parse_status": "loaded_from_vault",
            "path": str(VAULT_TENDER),
            "markdown_chars": len(tender),
        }
    )
    _source_dir(project["id"]).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(VAULT_TENDER, _source_dir(project["id"]) / VAULT_TENDER.name)
    _save_project(project)

    generate_plan(project["id"], db)
    approve_plan(project["id"])
    generate_execution(project["id"], db)
    generate_review(project["id"])

    return {
        "status": "completed",
        "project_id": project["id"],
        "output_dir": str(_artifact_dir(project["id"])),
        "artifacts": [item["name"] for item in list_project_artifacts(project["id"])],
    }
