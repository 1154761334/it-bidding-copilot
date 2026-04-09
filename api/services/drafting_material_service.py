import os
import json
import re
from typing import Optional, Set, Any
from sqlalchemy.orm import Session
from api.core.config import get_settings
from api.models.assets_v2 import EnterpriseCertificate, EnterpriseCase, EnterprisePersonnel
from api.models.bid_draft_v2 import ProjectMaterial
from api.models.rfp_v2 import RFPProject, RFPRequirement

settings = get_settings()

class DraftingMaterialService:
    def __init__(self, db: Session):
        self.db = db

    def _materials_pack_dir(self) -> str:
        path = settings.DATA_DIR / "project_material_packs"
        os.makedirs(path, exist_ok=True)
        return str(path)

    def _materials_pack_path(self, project_id: int) -> str:
        return os.path.join(self._materials_pack_dir(), f"{project_id}.json")

    def load_materials_pack_state(self, project_id: int) -> dict:
        path = self._materials_pack_path(project_id)
        default_state = {
            "selected_certificate_ids": [],
            "selected_case_ids": [],
            "selected_personnel_ids": [],
            "selected_material_ids": [],
            "drafting_notes": "",
            "confirmed": False,
        }
        if not os.path.exists(path):
            return default_state
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return {
                "selected_certificate_ids": [int(item) for item in payload.get("selected_certificate_ids", [])],
                "selected_case_ids": [int(item) for item in payload.get("selected_case_ids", [])],
                "selected_personnel_ids": [int(item) for item in payload.get("selected_personnel_ids", [])],
                "selected_material_ids": [int(item) for item in payload.get("selected_material_ids", [])],
                "drafting_notes": str(payload.get("drafting_notes", "")),
                "confirmed": bool(payload.get("confirmed", False)),
            }
        except Exception:
            return default_state

    def save_materials_pack_state(self, project_id: int, payload: Any) -> dict:
        state = {
            "selected_certificate_ids": payload.selected_certificate_ids,
            "selected_case_ids": payload.selected_case_ids,
            "selected_personnel_ids": payload.selected_personnel_ids,
            "selected_material_ids": payload.selected_material_ids,
            "drafting_notes": payload.drafting_notes,
            "confirmed": payload.confirmed,
        }
        with open(self._materials_pack_path(project_id), "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return state

    def _tokenize_text(self, value: str) -> Set[str]:
        return {token.lower() for token in re.findall(r"[\w\u4e00-\u9fff]{2,}", value or "")}

    def _keyword_score(self, tokens: Set[str], *values: str) -> int:
        haystack = " ".join(value or "" for value in values).lower()
        return sum(1 for token in tokens if token and token in haystack)

    def build_materials_pack(self, project: RFPProject) -> dict:
        state = self.load_materials_pack_state(project.id)
        company_id = project.company_id
        if not company_id:
            return {"error": "Project has no bound company"}

        certificates = (
            self.db.query(EnterpriseCertificate)
            .filter(EnterpriseCertificate.company_id == company_id)
            .order_by(EnterpriseCertificate.id.desc())
            .limit(30)
            .all()
        )
        cases = (
            self.db.query(EnterpriseCase)
            .filter(EnterpriseCase.company_id == company_id)
            .order_by(EnterpriseCase.id.desc())
            .limit(20)
            .all()
        )
        personnel = (
            self.db.query(EnterprisePersonnel)
            .filter(EnterprisePersonnel.company_id == company_id)
            .order_by(EnterprisePersonnel.id.desc())
            .limit(30)
            .all()
        )
        
        requirements = self.db.query(RFPRequirement).filter(RFPRequirement.project_id == project.id).all()
        requirement_tokens = self._tokenize_text(
            " ".join([project.project_name or ""] + [req.description or "" for req in requirements[:80]])
        )

        # Recommendation logic (simplified here, but following the original pattern)
        def get_top_ids(items, token_fields_func, limit):
            sorted_items = sorted(
                items,
                key=lambda item: (self._keyword_score(requirement_tokens, *token_fields_func(item)), item.id),
                reverse=True
            )
            return [item.id for item in sorted_items[:limit]]

        recommended_cert_ids = get_top_ids(certificates, lambda c: (c.raw_name, c.cert_type, c.certification_scope), 6)
        recommended_case_ids = get_top_ids(cases, lambda c: (c.project_name, c.industry, c.description), 4)
        recommended_person_ids = get_top_ids(personnel, lambda p: (p.name, p.role, p.resume_text), 6)

        return {
            "state": state,
            "recommendations": {
                "certificate_ids": recommended_cert_ids,
                "case_ids": recommended_case_ids,
                "personnel_ids": recommended_person_ids,
            },
            "available": {
                "certificates": [{"id": c.id, "name": c.raw_name} for c in certificates],
                "cases": [{"id": c.id, "name": c.project_name} for c in cases],
                "personnel": [{"id": p.id, "name": p.name} for p in personnel],
            }
        }
