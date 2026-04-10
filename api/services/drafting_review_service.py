from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from api.models.bid_draft_v2 import BidDraft
from api.models.rfp_v2 import RFPProject
import os
import re

class DraftingReviewService:
    def __init__(self, db: Session):
        self.db = db

    async def run_red_team_review(self, project_id: int) -> dict:
        drafts = self.db.query(BidDraft).filter(BidDraft.project_id == project_id).all()
        
        section_reviews = []
        approved_count = 0
        
        for draft in drafts:
            is_completed = (draft.generation_status == "COMPLETED")
            content_exists = bool((draft.content_markdown or "").strip())
            feedback = draft.audit_logs.get("final_feedback", "") if isinstance(draft.audit_logs, dict) else ""
            
            # P0 Requirement: Status check + content check
            verdict = "APPROVED" if (is_completed and content_exists and feedback == "APPROVED") else "REJECTED"
            
            if verdict == "APPROVED":
                approved_count += 1
            elif not is_completed:
                feedback = feedback or "章节生成尚未完成，禁止作为最终标书导出"
            elif not content_exists:
                feedback = feedback or "章节内容为空，禁止作为最终标书导出"
            
            section_reviews.append({
                "draft_id": draft.id,
                "section_title": draft.section_title,
                "verdict": verdict,
                "feedback": feedback or "待复核或审标未通过",
                "source_fragments": (draft.source_fragments or [])[:8],
                "generation_status": draft.generation_status
            })
            
        return {
            "project_id": project_id,
            "win_rate": int((approved_count / len(drafts)) * 100) if drafts else 0,
            "critical_risks": ["存在未通过审标的章节"] if approved_count < len(drafts) else [],
            "optimization_suggestions": ["维护响应完整度"] if approved_count == len(drafts) else ["优先修复被拒绝章节"],
            "winning_highlights": ["响应完整度高"] if approved_count == len(drafts) else ["初步证据链已就位"],
            "section_reviews": section_reviews,
            "total_drafts": len(drafts),
            "approved_drafts": approved_count,
            "round": "Round 1 (P0 Recovery)"
        }

    def build_export_readiness(self, project: RFPProject, master_template_available: bool = False) -> dict:
        drafts = self.db.query(BidDraft).filter(BidDraft.project_id == project.id).all()
        
        all_completed = all(d.generation_status == "COMPLETED" for d in drafts) and len(drafts) > 0
        
        # Count [IMAGE:...] pattern in markdown or fragments
        image_count = 0
        for d in drafts:
            image_count += len(re.findall(r"\[IMAGE:.*?\]", d.content_markdown or ""))
            for frag in (d.source_fragments or []):
                image_count += len(re.findall(r"\[IMAGE:.*?\]", str(frag)))

        checks = [
            {"key": "all_drafts_completed", "label": "所有章节生成已完成", "passed": all_completed, "detail": f"共 {len(drafts)} 章节"},
            {"key": "project_status_valid", "label": "项目状态合法", "passed": project.status in ["DEVIATION_CONFIRMED", "COMPLETED"], "detail": f"当前状态: {project.status}"},
            {"key": "master_template_available", "label": "采购文件母版可用", "passed": master_template_available, "detail": "母版已就位" if master_template_available else "未发现可用母版"},
            {"key": "image_evidence_ready", "label": "图片证据统计", "passed": True, "detail": {"image_evidence_count": image_count}},
        ]
        
        rejected_sections = [
            {
                "draft_id": d.id,
                "section_title": d.section_title,
                "generation_status": d.generation_status,
                "audit_feedback": (d.audit_logs.get("final_feedback") if isinstance(d.audit_logs, dict) else "待生成")
            }
            for d in drafts if d.generation_status != "COMPLETED" or (d.audit_logs.get("final_feedback") == "REJECTED" if isinstance(d.audit_logs, dict) else False)
        ]
        
        return {
            "project_id": project.id,
            "project_name": project.project_name,
            "project_status": project.status,
            "ready": all(c["passed"] for c in checks) and not rejected_sections,
            "checks": checks,
            "rejected_sections": rejected_sections
        }
