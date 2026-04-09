from sqlalchemy.orm import Session

from api.models.assets_v2 import Company
from api.models.bid_draft_v2 import BidDraft
from api.models.rfp_v2 import RFPProject


def get_primary_company(db: Session) -> Company | None:
    return db.query(Company).order_by(Company.id.asc()).first()


def get_or_create_primary_company(db: Session) -> Company:
    company = get_primary_company(db)
    if company is not None:
        return company

    company = Company(company_name="未命名企业")
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def get_latest_project(db: Session, company_id: int | None = None) -> RFPProject | None:
    query = db.query(RFPProject)
    if company_id is not None:
        query = query.filter(RFPProject.company_id == company_id)
    return query.order_by(RFPProject.id.desc()).first()


def get_latest_draft_for_project(db: Session, project_id: int) -> BidDraft | None:
    return (
        db.query(BidDraft)
        .filter(BidDraft.project_id == project_id)
        .order_by(BidDraft.section_index.asc(), BidDraft.id.asc())
        .first()
    )
