import asyncio
import datetime
import os
import re
import uuid

from sqlalchemy.orm import Session

from api.core.database import SessionLocal
from api.core.logger import get_logger
from api.models.assets_v2 import SourceDocument
from api.models.rfp_v2 import RFPProject, RFPRequirement
from api.services.model_runtime_service import build_parser_trace, get_model_runtime_info
from api.services.task_registry import task_registry
from utils.asset_matcher import AssetMatcher
from utils.docling_wrapper import DoclingWrapper
from utils.rfp_analyzer import RFPAnalyzer

logger = get_logger("rfp_analysis_service")


def build_analysis_payload(
    project: RFPProject,
    requirements: list[RFPRequirement],
    go_no_go: dict | None = None,
    analysis_trace: dict | None = None,
) -> dict:
    commercial_requirements = []
    technical_requirements = []
    veto_clauses = []
    scoring_system = {}

    for req in requirements:
        scoring_system[req.category] = scoring_system.get(req.category, 0) + (req.max_score or 0)

        if req.category in {"QUALIFICATION", "BUSINESS", "COMMERCIAL"}:
            commercial_requirements.append(
                {
                    "id": req.id,
                    "clause_index": req.clause_index,
                    "category": req.category,
                    "item": req.description,
                    "is_mandatory": req.is_fatal,
                    "evidence_required": req.evidence_required,
                    "max_score": req.max_score or 0,
                    "original_section": req.original_section,
                    "source": {"page": 1, "bbox": [], "text": req.description},
                }
            )

        if req.category == "TECHNICAL":
            technical_requirements.append(
                {
                    "id": req.id,
                    "category": req.category,
                    "item": req.description,
                    "param_name": req.clause_index or req.original_section or "技术要求",
                    "required_value": req.description,
                    "component": req.original_section or "技术规范",
                    "evidence_required": req.evidence_required,
                    "max_score": req.max_score or 0,
                    "original_section": req.original_section,
                    "source": {"page": 1, "bbox": [], "text": req.description},
                }
            )

        if req.is_fatal:
            veto_clauses.append(
                {
                    "id": req.id,
                    "clause_index": req.clause_index,
                    "category": req.category,
                    "requirement": req.description,
                    "evidence_required": req.evidence_required,
                    "max_score": req.max_score or 0,
                    "original_section": req.original_section,
                    "source": {"page": 1, "bbox": [], "text": req.description},
                }
            )

    return {
        "project_id": project.id,
        "project_name": project.project_name,
        "project_status": project.status,
        "project_info": {"name": project.project_name, "budget": project.budget},
        "budget": project.budget,
        "bid_deadline": project.deadline.isoformat() if project.deadline else "",
        "go_no_go": go_no_go or {"score": 0, "reasons": [], "status": "PENDING"},
        "commercial_requirements": commercial_requirements,
        "technical_requirements": technical_requirements,
        "veto_clauses": veto_clauses,
        "scoring_system": scoring_system,
        "analysis_trace": analysis_trace or {},
        "quality_report": build_analysis_quality_report(project, requirements, analysis_trace or {}),
    }


def summarize_rfp_markdown(markdown: str) -> dict:
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    headings = [line.lstrip("#").strip() for line in lines if line.startswith("#")]
    key_sections = {
        "announcement": any("招标公告" in heading for heading in headings),
        "requirements": any("采购需求" in heading or "项目详细指标需求" in heading for heading in headings),
        "scoring": any("评标办法" in heading or "评分" in heading for heading in headings),
        "instructions": any("投标人须知" in heading for heading in headings),
        "formats": any("投标文件格式" in heading for heading in headings),
    }
    return {
        "headings_total": len(headings),
        "headings_preview": headings[:20],
        "key_sections": key_sections,
    }


def build_analysis_quality_report(
    project: RFPProject,
    requirements: list[RFPRequirement],
    analysis_trace: dict | None = None,
) -> dict:
    analysis_trace = analysis_trace or {}
    parser_summary = analysis_trace.get("document_summary", {})
    categories: dict[str, int] = {}
    fatal_count = 0
    scoring_count = 0
    evidence_count = 0
    empty_section_count = 0

    for req in requirements:
        categories[req.category] = categories.get(req.category, 0) + 1
        if req.is_fatal:
            fatal_count += 1
        if (req.max_score or 0) > 0:
            scoring_count += 1
        if req.evidence_required:
            evidence_count += 1
        if not req.original_section:
            empty_section_count += 1

    checks = [
        {
            "name": "project_name_present",
            "passed": bool(project.project_name and project.project_name.strip()),
            "detail": project.project_name or "",
        },
        {
            "name": "project_code_detected",
            "passed": bool(re.search(r"[A-Z]{2,}-\d{4,}", jsonish_dump(analysis_trace))),
            "detail": analysis_trace.get("project_meta", {}).get("project_code", ""),
        },
        {
            "name": "budget_detected",
            "passed": bool(project.budget and project.budget > 0),
            "detail": project.budget or 0,
        },
        {
            "name": "deadline_detected",
            "passed": bool(project.deadline),
            "detail": project.deadline.isoformat() if project.deadline else "",
        },
        {
            "name": "requirements_extracted",
            "passed": len(requirements) >= 10,
            "detail": len(requirements),
        },
        {
            "name": "technical_requirements_present",
            "passed": categories.get("TECHNICAL", 0) > 0,
            "detail": categories.get("TECHNICAL", 0),
        },
        {
            "name": "commercial_or_qualification_present",
            "passed": categories.get("QUALIFICATION", 0) + categories.get("COMMERCIAL", 0) + categories.get("BUSINESS", 0) > 0,
            "detail": {
                "qualification": categories.get("QUALIFICATION", 0),
                "commercial": categories.get("COMMERCIAL", 0),
                "business": categories.get("BUSINESS", 0),
            },
        },
        {
            "name": "scoring_items_present",
            "passed": scoring_count > 0,
            "detail": scoring_count,
        },
        {
            "name": "fatal_items_present",
            "passed": fatal_count > 0,
            "detail": fatal_count,
        },
        {
            "name": "document_sections_detected",
            "passed": parser_summary.get("headings_total", 0) >= 5,
            "detail": parser_summary.get("headings_total", 0),
        },
    ]

    warnings = []
    if empty_section_count > 0:
        warnings.append(f"{empty_section_count} requirements are missing original_section.")
    if evidence_count == 0:
        warnings.append("No evidence requirements were extracted.")
    if not parser_summary.get("key_sections", {}).get("scoring"):
        warnings.append("Scoring section was not clearly detected from document headings.")
    if not parser_summary.get("key_sections", {}).get("requirements"):
        warnings.append("Requirement section was not clearly detected from document headings.")

    passed_count = len([check for check in checks if check["passed"]])
    status = "passed" if passed_count >= len(checks) - 1 else "needs_review"
    return {
        "status": status,
        "passed_checks": passed_count,
        "total_checks": len(checks),
        "checks": checks,
        "warnings": warnings,
        "metrics": {
            "requirements_total": len(requirements),
            "fatal_count": fatal_count,
            "scoring_count": scoring_count,
            "evidence_count": evidence_count,
            "category_distribution": categories,
        },
    }


def jsonish_dump(data: dict) -> str:
    return str(data)


async def start_rfp_analysis(*, company_id: int, filename: str, file_bytes: bytes, upload_dir: str) -> str:
    os.makedirs(upload_dir, exist_ok=True)
    task_id = f"rfp_{uuid.uuid4().hex}"
    await task_registry.create(task_id, stage="queued")

    local_path = os.path.join(upload_dir, f"{task_id}_{filename}")
    with open(local_path, "wb") as f:
        f.write(file_bytes)

    asyncio.create_task(
        _run_rfp_analysis_task(
            task_id=task_id,
            company_id=company_id,
            filename=filename,
            local_path=local_path,
        )
    )
    return task_id


async def _run_rfp_analysis_task(*, task_id: str, company_id: int, filename: str, local_path: str) -> None:
    db: Session = SessionLocal()
    try:
        await task_registry.update(task_id, status="running", stage="ingesting_source")
        source_doc = SourceDocument(
            company_id=company_id,
            filename=filename,
            file_type="RFP",
            local_path=local_path,
            upload_date=datetime.date.today(),
        )
        db.add(source_doc)
        db.commit()
        db.refresh(source_doc)

        logger.info("Starting async analysis for file: %s", filename)

        await task_registry.update(task_id, status="running", stage="parsing_document")
        parser = DoclingWrapper()
        parse_result = await asyncio.to_thread(parser.convert, local_path)
        analysis_trace = {
            "model_runtime": get_model_runtime_info(),
            "parser": build_parser_trace(strategy="docling_wrapper", parse_result=parse_result),
        }

        await task_registry.update(task_id, status="running", stage="extracting_project_meta")
        analyzer = RFPAnalyzer()
        analysis = await analyzer.analyze_full_document(parse_result["markdown"])
        review_trace = analysis.pop("_review_trace", None)
        analysis_trace["document_summary"] = summarize_rfp_markdown(parse_result["markdown"])
        analysis_trace["project_meta"] = {
            "project_name": analysis.get("project_info", {}).get("name", ""),
            "project_code": _extract_project_code(parse_result["markdown"]),
            "budget": analysis.get("project_info", {}).get("budget"),
            "deadline": analysis.get("project_info", {}).get("deadline"),
        }
        if review_trace is not None:
            analysis_trace["review_round"] = review_trace
        await task_registry.update(task_id, status="running", stage="classifying_sections")
        analysis_trace["requirements"] = {
            "count": len(analysis.get("requirements", [])),
            "project_name": analysis.get("project_info", {}).get("name", ""),
        }

        project = RFPProject(
            company_id=company_id,
            project_name=analysis["project_info"]["name"],
            rfp_source_id=source_doc.id,
            budget=analysis["project_info"].get("budget"),
            status="ANALYZING",
        )
        deadline_text = analysis["project_info"].get("deadline")
        if deadline_text:
            try:
                project.deadline = datetime.date.fromisoformat(deadline_text)
            except ValueError:
                project.deadline = None

        db.add(project)
        db.commit()
        db.refresh(project)

        await task_registry.update(task_id, status="running", stage="extracting_requirements")
        matcher = AssetMatcher(db)
        final_requirements = []

        await task_registry.update(task_id, status="running", stage="matching_assets")
        for req_data in analysis["requirements"]:
            requirement = RFPRequirement(
                project_id=project.id,
                original_section=req_data.get("original_section"),
                clause_index=req_data.get("clause_index"),
                category=req_data["category"],
                description=req_data["description"],
                is_fatal=req_data["is_fatal"],
                max_score=req_data["max_score"],
                evidence_required=req_data.get("evidence_required"),
            )
            matcher.match_requirement(requirement, company_id)
            db.add(requirement)
            final_requirements.append(requirement)

        project.status = "MATCHED"
        db.commit()

        await task_registry.update(task_id, status="running", stage="calculating_decision")
        all_assets = db.query(SourceDocument).filter(SourceDocument.company_id == company_id).all()
        asset_data = [{"content": f"{asset.filename} {asset.local_path or ''}"} for asset in all_assets]
        decision = await analyzer.calculate_go_no_go_score(analysis, asset_data)
        analysis_trace["assets"] = {
            "source_documents_count": len(all_assets),
            "matched_requirements_count": len(final_requirements),
        }
        await task_registry.update(task_id, status="running", stage="validating_analysis")
        payload = build_analysis_payload(project, final_requirements, decision, analysis_trace)

        project.status = "DRAFTING"
        db.commit()
        await task_registry.update(task_id, status="completed", stage="completed", result=payload)
    except Exception as exc:
        logger.exception("RFP analysis task failed: %s", task_id)
        await task_registry.update(task_id, status="failed", stage="failed", error=str(exc))
    finally:
        db.close()


def _extract_project_code(markdown: str) -> str:
    match = re.search(r"(?:项目编号|招标项目编号)[：:\s]*([A-Z]{2,}-\d{4,})", markdown)
    return match.group(1) if match else ""
