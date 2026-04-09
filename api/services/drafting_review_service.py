from typing import List, Dict, Any
from sqlalchemy.orm import Session
from api.models.bid_draft_v2 import BidDraft
from api.models.rfp_v2 import RFPProject

class DraftingReviewService:
    def __init__(self, db: Session):
        self.db = db

    def run_red_team_review(self, project_id: int) -> dict:
        drafts = self.db.query(BidDraft).filter(BidDraft.project_id == project_id).all()
        
        section_reviews = []
        approved_count = 0
        
        for draft in drafts:
            feedback = draft.audit_logs.get("final_feedback", "") if isinstance(draft.audit_logs, dict) else ""
            is_approved = feedback == "APPROVED"
            if is_approved:
                approved_count += 1
            
            section_reviews.append({
                "section_title": draft.section_title,
                "verdict": "APPROVED" if is_approved else "REJECTED",
                "feedback": feedback or "未完成自动评审或评审未通过"
            })
            
        return {
            "project_id": project_id,
            "total_drafts": len(drafts),
            "approved_drafts": approved_count,
            "section_reviews": section_reviews
        }

    def build_export_readiness(self, project: RFPProject) -> dict:
        drafts = self.db.query(BidDraft).filter(BidDraft.project_id == project.id).all()
        
        all_completed = all(d.generation_status == "COMPLETED" for d in drafts) and len(drafts) > 0
        
        checks = [
            {"key": "all_drafts_completed", "label": "所有章节生成已完成", "passed": all_completed},
            {"key": "project_status_valid", "label": "项目状态合法", "passed": project.status in ["DEVIATION_CONFIRMED", "COMPLETED"]},
        ]
        
        return {
            "project_id": project.id,
            "ready": all(c["passed"] for c in checks),
            "checks": checks
        }
