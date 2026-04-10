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
        project = self.db.query(RFPProject).filter(RFPProject.id == project_id).first()
        default_state = {
            "selected_certificate_ids": [],
            "selected_case_ids": [],
            "selected_personnel_ids": [],
            "selected_material_ids": [],
            "drafting_notes": "",
            "confirmed": False,
        }
        if not project:
            return default_state

        # Try DB first
        if project.materials_selection:
            try:
                state = json.loads(project.materials_selection)
                # Ensure types are correct
                return {
                    "selected_certificate_ids": [int(item) for item in state.get("selected_certificate_ids", [])],
                    "selected_case_ids": [int(item) for item in state.get("selected_case_ids", [])],
                    "selected_personnel_ids": [int(item) for item in state.get("selected_personnel_ids", [])],
                    "selected_material_ids": [int(item) for item in state.get("selected_material_ids", [])],
                    "drafting_notes": str(state.get("drafting_notes", "")),
                    "confirmed": bool(state.get("confirmed", False)),
                }
            except Exception:
                pass

        # Fallback to legacy JSON file
        path = self._materials_pack_path(project_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                state = {
                    "selected_certificate_ids": [int(item) for item in payload.get("selected_certificate_ids", [])],
                    "selected_case_ids": [int(item) for item in payload.get("selected_case_ids", [])],
                    "selected_personnel_ids": [int(item) for item in payload.get("selected_personnel_ids", [])],
                    "selected_material_ids": [int(item) for item in payload.get("selected_material_ids", [])],
                    "drafting_notes": str(payload.get("drafting_notes", "")),
                    "confirmed": bool(payload.get("confirmed", False)),
                }
                # Migrate to DB
                project.materials_selection = json.dumps(state, ensure_ascii=False)
                self.db.commit()
                return state
            except Exception:
                pass

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
        project = self.db.query(RFPProject).filter(RFPProject.id == project_id).first()
        if project:
            project.materials_selection = json.dumps(state, ensure_ascii=False)
            self.db.commit()
        
        # Also sync to JSON briefly for safety (optional, but good for transition)
        try:
            with open(self._materials_pack_path(project_id), "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
            
        return state

    def _tokenize_text(self, value: str) -> Set[str]:
        return {token.lower() for token in re.findall(r"[\w\u4e00-\u9fff]{2,}", value or "")}

    def _keyword_score(self, tokens: Set[str], *values: str) -> int:
        haystack = " ".join(value or "" for value in values).lower()
        return sum(1 for token in tokens if token and token in haystack)

    def _serialize_certificate(self, cert: EnterpriseCertificate) -> dict:
        return {
            "id": cert.id,
            "title": cert.raw_name,
            "subtitle": cert.cert_type or "未分类证书",
            "summary": cert.certification_scope or "未提供范围说明",
            "evidence_image_url": cert.image_url,
            "level": cert.cert_level,
        }

    def _serialize_case(self, case: EnterpriseCase) -> dict:
        return {
            "id": case.id,
            "title": case.project_name,
            "subtitle": case.industry or "未分类行业",
            "summary": case.description or "未提供案例说明",
            "contract_amount": case.contract_amount,
        }

    def _serialize_personnel(self, person: EnterprisePersonnel) -> dict:
        return {
            "id": person.id,
            "title": person.name,
            "subtitle": person.role or "未识别角色",
            "summary": person.resume_text or "未提供人员履历",
            "level": person.level,
            "social_security_image_url": person.social_security_image_url,
        }

    def _serialize_material(self, material: ProjectMaterial) -> dict:
        excerpt = (material.parsed_content or "").strip().replace("\n", " ")
        return {
            "id": material.id,
            "title": material.filename,
            "subtitle": material.file_type or "REFERENCE",
            "summary": excerpt[:120] if excerpt else "解析结果暂不可用",
            "filename": material.filename,
            "file_type": material.file_type,
            "upload_date": material.upload_date.isoformat() if material.upload_date else None,
            "parsed_excerpt": excerpt[:120] if excerpt else "",
        }

    def build_materials_pack(self, project: RFPProject) -> dict:
        raw_state = self.load_materials_pack_state(project.id)
        company_id = project.company_id
        if not company_id:
            return {"error": "Project has no bound company"}

        certificates = (
            self.db.query(EnterpriseCertificate)
            .filter(EnterpriseCertificate.company_id == company_id)
            .order_by(EnterpriseCertificate.id.desc())
            .limit(50)
            .all()
        )
        cases = (
            self.db.query(EnterpriseCase)
            .filter(EnterpriseCase.company_id == company_id)
            .order_by(EnterpriseCase.id.desc())
            .limit(30)
            .all()
        )
        personnel = (
            self.db.query(EnterprisePersonnel)
            .filter(EnterprisePersonnel.company_id == company_id)
            .order_by(EnterprisePersonnel.id.desc())
            .limit(50)
            .all()
        )
        extra_materials = (
            self.db.query(ProjectMaterial)
            .filter(ProjectMaterial.project_id == project.id)
            .all()
        )
        
        requirements = self.db.query(RFPRequirement).filter(RFPRequirement.project_id == project.id).all()
        requirement_tokens = self._tokenize_text(
            " ".join([project.project_name or ""] + [req.description or "" for req in requirements[:80]])
        )

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

        sel = {
            "certificate_ids": raw_state.get("selected_certificate_ids", []),
            "case_ids": raw_state.get("selected_case_ids", []),
            "personnel_ids": raw_state.get("selected_personnel_ids", []),
            "material_ids": raw_state.get("selected_material_ids", []),
        }

        return {
            "project_id": project.id,
            "project_name": project.project_name,
            "project_status": project.status,
            "confirmed": raw_state.get("confirmed", False),
            "drafting_notes": raw_state.get("drafting_notes", ""),
            "selection": sel,
            "recommended": {
                "certificate_ids": recommended_cert_ids,
                "case_ids": recommended_case_ids,
                "personnel_ids": recommended_person_ids,
            },
            "available": {
                "certificates": [self._serialize_certificate(c) for c in certificates],
                "cases": [self._serialize_case(c) for c in cases],
                "personnel": [self._serialize_personnel(p) for p in personnel],
                "materials": [self._serialize_material(m) for m in extra_materials],
            },
            "selected": {
                "certificates": [self._serialize_certificate(c) for c in certificates if c.id in sel["certificate_ids"]],
                "cases": [self._serialize_case(c) for c in cases if c.id in sel["case_ids"]],
                "personnel": [self._serialize_personnel(p) for p in personnel if p.id in sel["personnel_ids"]],
                "materials": [self._serialize_material(m) for m in extra_materials if m.id in sel["material_ids"]],
            },
            "summary": {
                "requirements_total": len(requirements),
                "certificates_selected": len(sel["certificate_ids"]),
                "cases_selected": len(sel["case_ids"]),
                "personnel_selected": len(sel["personnel_ids"]),
                "materials_selected": len(sel["material_ids"]),
            }
        }
