import datetime
import os
from types import SimpleNamespace
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.models.assets_v2 import (
    Company,
    CompanyAsset,
    EnterpriseCase,
    EnterpriseCertificate,
    EnterprisePersonnel,
    SourceDocument,
)
from api.services.enterprise_asset_service import EnterpriseAssetService
from api.services.enterprise_ingest_service import EnterpriseIngestService
from api.core.config import get_settings
from utils.asset_classifier import AssetClassifier
from utils.hybrid_retriever import HybridRetriever

settings = get_settings()

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md", ".png", ".jpg", ".jpeg"}


class CompanyCreate(BaseModel):
    name: str
    desc: Optional[str] = None
    credit_code: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_capital: Optional[str] = None
    address: Optional[str] = None


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    unified_social_credit_code: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_capital: Optional[str] = None
    address: Optional[str] = None


class VaultIngestRequest(BaseModel):
    vault_path: str


class BusinessDocIngestRequest(BaseModel):
    file_path: str
    display_name: Optional[str] = None


class CertificateUpdateRequest(BaseModel):
    raw_name: Optional[str] = None
    cert_type: Optional[str] = None
    cert_level: Optional[str] = None
    certification_scope: Optional[str] = None
    expiry_date: Optional[str] = None


class CaseUpdateRequest(BaseModel):
    project_name: Optional[str] = None
    industry: Optional[str] = None
    contract_amount: Optional[float] = None
    description: Optional[str] = None
    compliance_keywords: Optional[str] = None


class PersonnelUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    level: Optional[str] = None
    years_of_experience: Optional[int] = None
    resume_text: Optional[str] = None


class AssetBatchDeleteItem(BaseModel):
    kind: str
    id: int


class AssetBatchDeleteRequest(BaseModel):
    items: List[AssetBatchDeleteItem]


def _normalize_query(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _parse_optional_date(value: Optional[str]) -> datetime.date | None:
    if not value:
        return None
    return datetime.date.fromisoformat(value)


def _resolve_asset_model(kind: str):
    return {
        "certificate": EnterpriseCertificate,
        "case": EnterpriseCase,
        "personnel": EnterprisePersonnel,
    }.get(kind)


def serialize_company(company: Company) -> dict:
    return {
        "id": company.id,
        "name": company.company_name,
        "company_name": company.company_name,
        "description": company.description,
        "unified_social_credit_code": company.unified_social_credit_code,
        "registered_capital": company.registered_capital,
        "address": company.address,
        "legal_representative": company.legal_representative,
    }


def get_primary_company(db: Session) -> Optional[Company]:
    return db.query(Company).order_by(Company.id.asc()).first()





@router.get("/profile")
async def get_profile(db: Session = Depends(get_db)):
    company = get_primary_company(db)
    if not company:
        return {
            "id": None,
            "company_name": "",
            "unified_social_credit_code": "",
            "legal_representative": "",
            "registered_capital": "",
            "address": "",
        }
    return serialize_company(company)


@router.get("/assets-overview/{company_id}")
async def get_assets_overview(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    service = EnterpriseAssetService(db)
    return service.build_assets_overview(company)


@router.get("/assets-browser/{company_id}")
async def get_assets_browser(company_id: int, asset_kind: str = "all", query: str = "", db: Session = Depends(get_db)):
    allowed_kinds = {"all", "certificate", "case", "personnel", "source_document", "image"}
    if asset_kind not in allowed_kinds:
        raise HTTPException(status_code=400, detail=f"Unsupported asset_kind: {asset_kind}")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    service = EnterpriseAssetService(db)
    return service.build_assets_browser(company, asset_kind=asset_kind, query=query)


@router.get("/intake-readiness/{company_id}")
async def get_enterprise_intake_readiness(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    service = EnterpriseAssetService(db)
    return service.build_enterprise_intake_readiness(company)


@router.get("/latest-ingest-batch/{company_id}")
async def get_latest_ingest_batch(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    service = EnterpriseAssetService(db)
    return service.build_latest_ingest_batch(company)


@router.get("/assets-image/{asset_id}")
async def get_asset_image(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(CompanyAsset).filter(CompanyAsset.id == asset_id, CompanyAsset.asset_type == "image").first()
    if not asset:
        raise HTTPException(status_code=404, detail="Image asset not found")
    if not asset.local_path or not os.path.exists(asset.local_path):
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(asset.local_path)


@router.post("/assets/certificate")
async def create_certificate(payload: CertificateUpdateRequest, db: Session = Depends(get_db)):
    company = get_primary_company(db)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    certificate = EnterpriseCertificate(
        company_id=company.id,
        raw_name=payload.raw_name or "未命名证书",
        cert_type=payload.cert_type,
        cert_level=payload.cert_level,
        certification_scope=payload.certification_scope,
        expiry_date=_parse_optional_date(payload.expiry_date),
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return {"status": "created", "id": certificate.id}


@router.post("/assets/case")
async def create_case(payload: CaseUpdateRequest, db: Session = Depends(get_db)):
    company = get_primary_company(db)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    case = EnterpriseCase(
        company_id=company.id,
        project_name=payload.project_name or "未命名案例",
        industry=payload.industry,
        contract_amount=payload.contract_amount,
        description=payload.description,
        compliance_keywords=payload.compliance_keywords,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {"status": "created", "id": case.id}


@router.post("/assets/personnel")
async def create_personnel(payload: PersonnelUpdateRequest, db: Session = Depends(get_db)):
    company = get_primary_company(db)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    person = EnterprisePersonnel(
        company_id=company.id,
        name=payload.name or "未命名人员",
        role=payload.role,
        level=payload.level,
        years_of_experience=payload.years_of_experience or 0,
        resume_text=payload.resume_text,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return {"status": "created", "id": person.id}


@router.put("/assets/certificate/{certificate_id}")
async def update_certificate(certificate_id: int, payload: CertificateUpdateRequest, db: Session = Depends(get_db)):
    certificate = db.query(EnterpriseCertificate).filter(EnterpriseCertificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if payload.raw_name is not None:
        certificate.raw_name = payload.raw_name
    if payload.cert_type is not None:
        certificate.cert_type = payload.cert_type
    if payload.cert_level is not None:
        certificate.cert_level = payload.cert_level
    if payload.certification_scope is not None:
        certificate.certification_scope = payload.certification_scope
    if payload.expiry_date is not None:
        certificate.expiry_date = _parse_optional_date(payload.expiry_date)

    db.commit()
    db.refresh(certificate)
    return {"status": "updated", "id": certificate.id}


@router.put("/assets/case/{case_id}")
async def update_case(case_id: int, payload: CaseUpdateRequest, db: Session = Depends(get_db)):
    case = db.query(EnterpriseCase).filter(EnterpriseCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if payload.project_name is not None:
        case.project_name = payload.project_name
    if payload.industry is not None:
        case.industry = payload.industry
    if payload.contract_amount is not None:
        case.contract_amount = payload.contract_amount
    if payload.description is not None:
        case.description = payload.description
    if payload.compliance_keywords is not None:
        case.compliance_keywords = payload.compliance_keywords

    db.commit()
    db.refresh(case)
    return {"status": "updated", "id": case.id}


@router.put("/assets/personnel/{personnel_id}")
async def update_personnel(personnel_id: int, payload: PersonnelUpdateRequest, db: Session = Depends(get_db)):
    person = db.query(EnterprisePersonnel).filter(EnterprisePersonnel.id == personnel_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Personnel not found")

    if payload.name is not None:
        person.name = payload.name
    if payload.role is not None:
        person.role = payload.role
    if payload.level is not None:
        person.level = payload.level
    if payload.years_of_experience is not None:
        person.years_of_experience = payload.years_of_experience
    if payload.resume_text is not None:
        person.resume_text = payload.resume_text

    db.commit()
    db.refresh(person)
    return {"status": "updated", "id": person.id}


@router.delete("/assets/certificate/{certificate_id}")
async def delete_certificate(certificate_id: int, db: Session = Depends(get_db)):
    certificate = db.query(EnterpriseCertificate).filter(EnterpriseCertificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    db.delete(certificate)
    db.commit()
    return {"status": "deleted", "id": certificate_id}


@router.delete("/assets/case/{case_id}")
async def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(EnterpriseCase).filter(EnterpriseCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()
    return {"status": "deleted", "id": case_id}


@router.delete("/assets/personnel/{personnel_id}")
async def delete_personnel(personnel_id: int, db: Session = Depends(get_db)):
    person = db.query(EnterprisePersonnel).filter(EnterprisePersonnel.id == personnel_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Personnel not found")
    db.delete(person)
    db.commit()
    return {"status": "deleted", "id": personnel_id}


@router.post("/assets/batch-delete")
async def batch_delete_assets(payload: AssetBatchDeleteRequest, db: Session = Depends(get_db)):
    deleted: list[dict] = []
    for item in payload.items:
        model = _resolve_asset_model(item.kind)
        if model is None:
            continue
        record = db.query(model).filter(model.id == item.id).first()
        if record is None:
            continue
        db.delete(record)
        deleted.append({"kind": item.kind, "id": item.id})
    db.commit()
    return {"status": "deleted", "deleted": deleted, "count": len(deleted)}


@router.put("/profile")
async def update_profile(payload: CompanyUpdate, db: Session = Depends(get_db)):
    company = get_primary_company(db)
    if not company:
        company = Company(company_name=payload.company_name or "未命名企业")
        db.add(company)
        db.flush()

    if payload.company_name is not None:
        company.company_name = payload.company_name
    if payload.unified_social_credit_code is not None:
        company.unified_social_credit_code = payload.unified_social_credit_code
    if payload.legal_representative is not None:
        company.legal_representative = payload.legal_representative
    if payload.registered_capital is not None:
        company.registered_capital = payload.registered_capital
    if payload.address is not None:
        company.address = payload.address

    db.commit()
    db.refresh(company)
    return {"profile": serialize_company(company)}


@router.get("/trust-score")
async def get_trust_score(db: Session = Depends(get_db)):
    company = get_primary_company(db)
    if not company:
        return {
            "score": 0,
            "identity_verified": False,
            "compliance_status": "未建档",
            "financial_health": "未评级",
        }

    cert_count = db.query(EnterpriseCertificate).filter(EnterpriseCertificate.company_id == company.id).count()
    case_count = db.query(EnterpriseCase).filter(EnterpriseCase.company_id == company.id).count()
    personnel_count = db.query(EnterprisePersonnel).filter(EnterprisePersonnel.company_id == company.id).count()
    asset_score = min(100, cert_count * 20 + case_count * 15 + personnel_count * 5)

    return {
        "score": asset_score,
        "identity_verified": bool(company.unified_social_credit_code or cert_count > 0),
        "compliance_status": "已扫描" if cert_count > 0 else "待补充",
        "financial_health": "A" if case_count > 0 else "未评级",
    }


@router.post("")
async def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    company = Company(
        company_name=payload.name,
        description=payload.desc,
        unified_social_credit_code=payload.credit_code,
        legal_representative=payload.legal_representative,
        registered_capital=payload.registered_capital,
        address=payload.address,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return serialize_company(company)


@router.get("")
async def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.id.asc()).all()
    return [serialize_company(company) for company in companies]


@router.get("/{company_id}")
async def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return serialize_company(company)


@router.post("/bulk-ingest/{company_id}")
async def bulk_ingest(company_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    upload_dir = str(settings.DATA_DIR / "uploads")
    service = EnterpriseIngestService(db)
    try:
        return await service.ingest_upload_files(company_id=company_id, files=files, upload_dir=upload_dir)
    except ValueError:
        raise HTTPException(status_code=404, detail="Company not found")

@router.post("/vault-ingest/{company_id}")
async def vault_ingest(company_id: int, payload: VaultIngestRequest, db: Session = Depends(get_db)):
    service = EnterpriseIngestService(db)
    try:
        return await service.ingest_vault_directory(
            company_id=company_id,
            vault_path=payload.vault_path,
            upload_dir=str(settings.DATA_DIR / "uploads"),
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "Company" in message or "Vault path" in message else 400
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.post("/business-doc-ingest/{company_id}")
async def business_doc_ingest(company_id: int, payload: BusinessDocIngestRequest, db: Session = Depends(get_db)):
    service = EnterpriseIngestService(db)
    try:
        return await service.ingest_business_document(
            company_id=company_id,
            local_path=payload.file_path,
            display_name=payload.display_name,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "Company" in message or "not found" in message else 400
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/search-assets")
async def search_assets(company_id: int, query: str, db: Session = Depends(get_db)):
    retriever = HybridRetriever(db)
    structured_query = SimpleNamespace(
        semantic_context=query,
        min_amount=None,
        earliest_date=None,
        target_category=None,
    )
    cases = await retriever.search_cases(structured_query, company_id=company_id)
    certs = await retriever.search_certificates(query, company_id=company_id)
    return {
        "cases": [{"id": case.id, "project_name": case.project_name, "description": case.description} for case in cases],
        "certificates": [{"id": cert.id, "raw_name": cert.raw_name, "scope": cert.certification_scope} for cert in certs],
    }
