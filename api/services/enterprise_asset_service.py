from typing import List, Optional, Any
from sqlalchemy.orm import Session
from api.models.assets_v2 import (
    Company,
    EnterpriseCase,
    EnterpriseCertificate,
    EnterprisePersonnel,
    SourceDocument,
    CompanyAsset,
)

class EnterpriseAssetService:
    def __init__(self, db: Session):
        self.db = db

    def build_assets_overview(self, company: Company) -> dict:
        cert_count = self.db.query(EnterpriseCertificate).filter(EnterpriseCertificate.company_id == company.id).count()
        case_count = self.db.query(EnterpriseCase).filter(EnterpriseCase.company_id == company.id).count()
        personnel_count = self.db.query(EnterprisePersonnel).filter(EnterprisePersonnel.company_id == company.id).count()
        source_count = self.db.query(SourceDocument).filter(SourceDocument.company_id == company.id).count()
        image_count = self.db.query(CompanyAsset).filter(CompanyAsset.company_id == company.id, CompanyAsset.asset_type == "image").count()

        latest_certs = (
            self.db.query(EnterpriseCertificate)
            .filter(EnterpriseCertificate.company_id == company.id)
            .order_by(EnterpriseCertificate.id.desc())
            .limit(5)
            .all()
        )
        latest_cases = (
             self.db.query(EnterpriseCase)
            .filter(EnterpriseCase.company_id == company.id)
            .order_by(EnterpriseCase.id.desc())
            .limit(5)
            .all()
        )
        latest_personnel = (
             self.db.query(EnterprisePersonnel)
            .filter(EnterprisePersonnel.company_id == company.id)
            .order_by(EnterprisePersonnel.id.desc())
            .limit(5)
            .all()
        )
        latest_sources = (
            self.db.query(SourceDocument)
            .filter(SourceDocument.company_id == company.id)
            .order_by(SourceDocument.id.desc())
            .limit(5)
            .all()
        )
        latest_images = (
            self.db.query(CompanyAsset)
            .filter(CompanyAsset.company_id == company.id, CompanyAsset.asset_type == "image")
            .order_by(CompanyAsset.upload_date.desc())
            .limit(5)
            .all()
        )

        return {
            "company_id": company.id,
            "counts": {
                "certificates": cert_count,
                "cases": case_count,
                "personnel": personnel_count,
                "source_documents": source_count,
                "images": image_count,
            },
            "certificates": [
                {
                    "id": c.id,
                    "raw_name": c.raw_name,
                    "cert_type": c.cert_type,
                    "cert_level": c.cert_level,
                    "scope": c.certification_scope,
                    "expiry_date": c.expiry_date.isoformat() if c.expiry_date else None,
                    "image_url": c.image_url,
                }
                for c in latest_certs
            ],
            "cases": [
                {
                    "id": c.id,
                    "project_name": c.project_name,
                    "industry": c.industry,
                    "contract_amount": c.contract_amount,
                    "description": c.description,
                }
                for c in latest_cases
            ],
            "personnel": [
                {
                    "id": c.id,
                    "name": c.name,
                    "role": c.role,
                    "level": c.level,
                    "years_of_experience": c.years_of_experience,
                    "social_security_image_url": c.social_security_image_url,
                }
                for c in latest_personnel
            ],
            "source_documents": [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "upload_date": d.upload_date.isoformat() if d.upload_date else None,
                }
                for d in latest_sources
            ],
            "images": [
                {
                    "id": asset.id,
                    "asset_name": asset.asset_name,
                    "asset_tag": asset.asset_tag,
                    "local_path": asset.local_path,
                }
                for asset in latest_images
            ],
        }

    def build_assets_browser(self, company: Company, asset_kind: str = "all", query: str = "") -> dict:
        items = []
        q = query.strip().lower()

        def matches(*fields):
            if not q:
                return True
            for field in fields:
                if field and q in str(field).lower():
                    return True
            return False

        if asset_kind in {"all", "certificate"}:
            certs = (
                self.db.query(EnterpriseCertificate)
                .filter(EnterpriseCertificate.company_id == company.id)
                .order_by(EnterpriseCertificate.id.desc())
                .all()
            )
            for cert in certs:
                if not matches(cert.raw_name, cert.cert_type, cert.certification_scope):
                    continue
                items.append({
                    "id": f"certificate-{cert.id}",
                    "kind": "certificate",
                    "title": cert.raw_name,
                    "subtitle": cert.cert_type or "未分类证书",
                    "summary": cert.certification_scope or "未提供范围说明",
                    "meta": {
                        "record_id": cert.id,
                        "cert_type": cert.cert_type,
                        "cert_level": cert.cert_level,
                        "certification_scope": cert.certification_scope,
                        "expiry_date": cert.expiry_date.isoformat() if cert.expiry_date else None,
                    },
                })

        if asset_kind in {"all", "case"}:
            cases = (
                self.db.query(EnterpriseCase)
                .filter(EnterpriseCase.company_id == company.id)
                .order_by(EnterpriseCase.id.desc())
                .all()
            )
            for case in cases:
                if not matches(case.project_name, case.industry, case.description):
                    continue
                items.append({
                    "id": f"case-{case.id}",
                    "kind": "case",
                    "title": case.project_name,
                    "subtitle": case.industry or "未分类行业",
                    "summary": case.description or "未提供案例说明",
                    "meta": {
                        "record_id": case.id,
                        "industry": case.industry,
                        "contract_amount": case.contract_amount,
                        "compliance_keywords": case.compliance_keywords,
                    },
                })

        if asset_kind in {"all", "personnel"}:
            personnel = (
                self.db.query(EnterprisePersonnel)
                .filter(EnterprisePersonnel.company_id == company.id)
                .order_by(EnterprisePersonnel.id.desc())
                .all()
            )
            for person in personnel:
                if not matches(person.name, person.role, person.resume_text):
                    continue
                items.append({
                    "id": f"personnel-{person.id}",
                    "kind": "personnel",
                    "title": person.name,
                    "subtitle": person.role or "未识别角色",
                    "summary": person.resume_text or "未提取人员说明",
                    "meta": {
                        "record_id": person.id,
                        "level": person.level,
                        "years_of_experience": person.years_of_experience,
                        "resume_text": person.resume_text,
                    },
                })

        if asset_kind in {"all", "source_document"}:
            documents = (
                self.db.query(SourceDocument)
                .filter(SourceDocument.company_id == company.id)
                .order_by(SourceDocument.id.desc())
                .all()
            )
            for source in documents:
                if not matches(source.filename, source.file_type):
                    continue
                items.append({
                    "id": f"source_document-{source.id}",
                    "kind": "source_document",
                    "title": source.filename,
                    "subtitle": source.file_type or "UNKNOWN",
                    "meta": {
                        "record_id": source.id,
                        "upload_date": source.upload_date.isoformat() if source.upload_date else None,
                    },
                })

        if asset_kind in {"all", "image"}:
            images = (
                self.db.query(CompanyAsset)
                .filter(CompanyAsset.company_id == company.id, CompanyAsset.asset_type == "image")
                .order_by(CompanyAsset.upload_date.desc())
                .all()
            )
            for asset in images:
                if not matches(asset.asset_name, asset.asset_tag, asset.category):
                    continue
                items.append({
                    "id": f"image-{asset.id}",
                    "kind": "image",
                    "title": asset.asset_name,
                    "subtitle": asset.asset_tag or asset.category or "图片证据",
                    "meta": {
                        "asset_id": asset.id,
                        "preview_url": f"/api/v1/enterprise/assets-image/{asset.id}",
                    },
                })

        order_priority = {"certificate": 0, "case": 1, "personnel": 2, "source_document": 3, "image": 4}
        items.sort(key=lambda item: (order_priority.get(item["kind"], 99), item["title"]))

        return {
            "company_id": company.id,
            "asset_kind": asset_kind,
            "query": query,
            "total": len(items),
            "items": items,
        }

    def build_enterprise_intake_readiness(self, company: Company) -> dict:
        cert_count = self.db.query(EnterpriseCertificate).filter(EnterpriseCertificate.company_id == company.id).count()
        case_count = self.db.query(EnterpriseCase).filter(EnterpriseCase.company_id == company.id).count()
        personnel_count = self.db.query(EnterprisePersonnel).filter(EnterprisePersonnel.company_id == company.id).count()
        source_count = self.db.query(SourceDocument).filter(SourceDocument.company_id == company.id).count()
        
        business_license_count = (
            self.db.query(EnterpriseCertificate)
            .filter(EnterpriseCertificate.company_id == company.id, EnterpriseCertificate.raw_name.contains("营业执照"))
            .count()
        )

        checks = [
            {
                "key": "company_profile_ready",
                "label": "企业主体基础信息已建立",
                "passed": bool(company.company_name and company.company_name.strip()),
                "detail": company.company_name or "",
            },
            {
                "key": "core_identity_ready",
                "label": "统一社会信用代码或营业执照已具备",
                "passed": bool(company.unified_social_credit_code or business_license_count > 0),
                "detail": company.unified_social_credit_code or "",
            },
            {
                "key": "source_documents_ready",
                "label": "企业源材料已入库",
                "passed": source_count > 0,
                "detail": source_count,
            },
            {
                "key": "certificates_ready",
                "label": "资质证书已沉淀",
                "passed": cert_count > 0,
                "detail": cert_count,
            },
            {
                "key": "cases_ready",
                "label": "历史案例已沉淀",
                "passed": case_count > 0,
                "detail": case_count,
            },
            {
                "key": "personnel_ready",
                "label": "人员履历已沉淀",
                "passed": personnel_count > 0,
                "detail": personnel_count,
            },
        ]
        warnings = [
            check["label"]
            for check in checks
            if not check["passed"]
        ]

        return {
            "company_id": company.id,
            "company_name": company.company_name,
            "ready": all(check["passed"] for check in checks),
            "checks": checks,
            "warnings": warnings,
        }

    def build_latest_ingest_batch(self, company: Company) -> dict:
        latest_date = (
            self.db.query(SourceDocument.upload_date)
            .filter(SourceDocument.company_id == company.id, SourceDocument.file_type != "RFP")
            .order_by(SourceDocument.upload_date.desc())
            .limit(1)
            .scalar()
        )
        if not latest_date:
            return {"company_id": company.id, "has_batch": False}

        source_documents = (
            self.db.query(SourceDocument)
            .filter(SourceDocument.company_id == company.id, SourceDocument.upload_date == latest_date)
            .all()
        )

        cert_count = self.db.query(EnterpriseCertificate).filter(EnterpriseCertificate.company_id == company.id).count() 
        case_count = self.db.query(EnterpriseCase).filter(EnterpriseCase.company_id == company.id).count() 
        image_count = self.db.query(CompanyAsset).filter(CompanyAsset.company_id == company.id, CompanyAsset.asset_type == "image").count()
        
        return {
            "company_id": company.id,
            "has_batch": True,
            "batch_date": latest_date.isoformat(),
            "counts": {
                "source_documents": len(source_documents),
                "certificates": cert_count,
                "cases": case_count,
                "images": image_count,
            },
            "source_documents": [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "local_path": d.local_path,
                }
                for d in source_documents
            ],
            "notes": [
                "优先核对本轮新入库源文件与结构化结果是否准确。",
                "当前批次统计为企业历史累计结果，不代表仅本轮新增数量。",
            ],
        }
