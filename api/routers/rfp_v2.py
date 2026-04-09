import asyncio
import datetime
import os
from pathlib import Path
from typing import List

from pydantic import BaseModel
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.core.logger import get_logger
from api.models.assets_v2 import SourceDocument
from api.models.rfp_v2 import RFPProject, RFPRequirement
from api.services.context_service import get_or_create_primary_company
from api.services.rfp_analysis_service import (
    _extract_project_code,
    build_analysis_payload,
    build_analysis_quality_report,
    start_rfp_analysis,
    summarize_rfp_markdown,
)
from api.services.task_registry import task_registry
from utils.docling_wrapper import DoclingWrapper

router = APIRouter()
logger = get_logger("rfp_router")
PROJECT_ROOT = Path("/root/it-bidding-copilot")


class DeviationItemUpdate(BaseModel):
    id: int
    resp: str
    status: str


class DeviationUpdateRequest(BaseModel):
    items: List[DeviationItemUpdate]


class AnalysisProjectInfoUpdate(BaseModel):
    name: str | None = None
    budget: float | None = None
    deadline: str | None = None


class AnalysisRequirementUpdate(BaseModel):
    id: int
    description: str
    category: str | None = None
    is_fatal: bool | None = None
    evidence_required: str | None = None
    max_score: float | None = None


class AnalysisConfirmRequest(BaseModel):
    project_info: AnalysisProjectInfoUpdate
    requirements: List[AnalysisRequirementUpdate]


def _resolve_rfp_source_path(source_doc: SourceDocument | None) -> str | None:
    if source_doc is None:
        return None
    candidates: list[str] = []
    if source_doc.local_path:
        candidates.append(source_doc.local_path)
    if source_doc.filename:
        candidates.append(str(PROJECT_ROOT / "docs" / source_doc.filename))
        candidates.append(str(PROJECT_ROOT / "uploads" / source_doc.filename))

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


@router.post("/analyze")
async def analyze_rfp(file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = get_or_create_primary_company(db)
    company_id = company.id
    upload_dir = "/root/it-bidding-copilot/uploads"
    file_bytes = await file.read()
    task_id = await start_rfp_analysis(
        company_id=company_id,
        filename=file.filename,
        file_bytes=file_bytes,
        upload_dir=upload_dir,
    )

    return {
        "status": "pending",
        "task_id": task_id,
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    task_record = await task_registry.get(task_id)
    if task_record is not None:
        return task_record.to_dict()

    # Fallback for previously completed historical tasks persisted in DB.
    if task_id.isdigit():
        project = db.query(RFPProject).filter(RFPProject.id == int(task_id)).first()
        if project:
            requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project.id).all()
            return {"status": "completed", "stage": "completed", "result": build_analysis_payload(project, requirements)}

    return {"status": "failed", "stage": "failed", "error": "Task not found"}


@router.get("/projects/{project_id}/deviation")
async def get_deviation_matrix(project_id: int, db: Session = Depends(get_db)):
    requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project_id).all()
    if not requirements:
        return []

    return [
        {
            "id": req.id,
            "req": f"{req.clause_index or ''} {req.description}".strip(),
            "resp": req.match_comment or "未找到匹配资产，需人工核对",
            "status": "compliant" if req.match_status == "PASS" else "partial",
            "is_fatal": req.is_fatal,
            "category": req.category,
            "evidence_required": req.evidence_required,
            "original_section": req.original_section,
        }
        for req in requirements
    ]


@router.put("/projects/{project_id}/deviation")
async def update_deviation_matrix(project_id: int, payload: DeviationUpdateRequest, db: Session = Depends(get_db)):
    project = db.query(RFPProject).filter(RFPProject.id == project_id).first()
    if not project:
        return {"status": "failed", "error": "Project not found"}

    requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project_id).all()
    requirement_map = {req.id: req for req in requirements}
    status_map = {
        "compliant": "PASS",
        "partial": "PARTIAL",
        "gap": "FAIL",
        "unknown": "UNKNOWN",
    }

    updated = 0
    for item in payload.items:
        requirement = requirement_map.get(item.id)
        if requirement is None:
            continue
        requirement.match_comment = item.resp.strip()
        requirement.match_status = status_map.get(item.status, "PARTIAL")
        updated += 1

    db.commit()
    return {"status": "success", "project_id": project_id, "updated": updated}


@router.post("/projects/{project_id}/deviation/confirm")
async def confirm_deviation_matrix(project_id: int, db: Session = Depends(get_db)):
    project = db.query(RFPProject).filter(RFPProject.id == project_id).first()
    if not project:
        return {"status": "failed", "error": "Project not found"}

    requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project_id).all()
    if not requirements:
        return {"status": "failed", "error": "No requirements found"}

    completed_items = len([req for req in requirements if (req.match_comment or "").strip()])
    project.status = "DEVIATION_CONFIRMED"
    db.commit()
    return {
        "status": "success",
        "project_id": project_id,
        "project_status": project.status,
        "completed_items": completed_items,
        "total_items": len(requirements),
    }


@router.get("/projects/{project_id}/analysis-check")
async def get_analysis_check(project_id: int, db: Session = Depends(get_db)):
    project = db.query(RFPProject).filter(RFPProject.id == project_id).first()
    if not project:
        return {"status": "failed", "error": "Project not found"}

    requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project_id).all()
    analysis_trace = {}
    if project.rfp_source_id:
        source_doc = db.query(SourceDocument).filter(SourceDocument.id == project.rfp_source_id).first()
        resolved_path = _resolve_rfp_source_path(source_doc)
        if resolved_path:
            parse_result = await asyncio.to_thread(DoclingWrapper().convert, resolved_path)
            analysis_trace = {
                "document_summary": summarize_rfp_markdown(parse_result["markdown"]),
                "project_meta": {"project_code": _extract_project_code(parse_result["markdown"])},
            }
        elif source_doc:
            analysis_trace = {
                "document_summary": {"headings_total": 0, "headings_preview": [], "key_sections": {}},
                "project_meta": {"project_code": "", "source_resolution": "missing_local_file"},
            }

    quality_report = build_analysis_quality_report(project, requirements, analysis_trace)
    return {
        "project_id": project.id,
        "project_name": project.project_name,
        "quality_report": quality_report,
    }


@router.get("/projects/{project_id}")
async def get_project_analysis(project_id: int, db: Session = Depends(get_db)):
    project = db.query(RFPProject).filter(RFPProject.id == project_id).first()
    if not project:
        return {"status": "failed", "error": "Project not found"}

    requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project_id).all()
    return build_analysis_payload(project, requirements)


@router.post("/projects/{project_id}/analysis-confirm")
async def confirm_project_analysis(project_id: int, payload: AnalysisConfirmRequest, db: Session = Depends(get_db)):
    project = db.query(RFPProject).filter(RFPProject.id == project_id).first()
    if not project:
        return {"status": "failed", "error": "Project not found"}

    if payload.project_info.name is not None and payload.project_info.name.strip():
        project.project_name = payload.project_info.name.strip()
    if payload.project_info.budget is not None:
        project.budget = payload.project_info.budget
    if payload.project_info.deadline is not None:
        project.deadline = datetime.date.fromisoformat(payload.project_info.deadline) if payload.project_info.deadline else None

    requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project_id).all()
    requirement_map = {req.id: req for req in requirements}

    updated = 0
    for item in payload.requirements:
        requirement = requirement_map.get(item.id)
        if requirement is None:
            continue
        requirement.description = item.description.strip()
        if item.category is not None:
            requirement.category = item.category
        if item.is_fatal is not None:
            requirement.is_fatal = item.is_fatal
        if item.evidence_required is not None:
            requirement.evidence_required = item.evidence_required.strip()
        if item.max_score is not None:
            requirement.max_score = item.max_score
        updated += 1

    project.status = "ANALYSIS_CONFIRMED"
    db.commit()
    refreshed_requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project_id).all()
    return {
        "status": "success",
        "project_id": project_id,
        "updated_requirements": updated,
        "project_status": project.status,
        "result": build_analysis_payload(project, refreshed_requirements),
    }
