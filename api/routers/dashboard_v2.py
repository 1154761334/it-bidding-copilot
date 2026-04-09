from fastapi import APIRouter
from api.core.database import SessionLocal
from api.models import rfp_v2 as rfp_models
from api.services.context_service import get_latest_draft_for_project, get_latest_project, get_primary_company

router = APIRouter()


@router.get("/context")
async def get_dashboard_context():
    db = SessionLocal()
    try:
        company = get_primary_company(db)
        project = get_latest_project(db, company.id if company else None)
        draft = get_latest_draft_for_project(db, project.id) if project else None

        return {
            "current_company_id": company.id if company else None,
            "current_company_name": company.company_name if company else None,
            "current_project_id": project.id if project else None,
            "current_project_name": project.project_name if project else None,
            "current_draft_id": str(draft.id) if draft else None,
        }
    finally:
        db.close()

@router.get("/stats")
async def get_dashboard_stats():
    db = SessionLocal()
    try:
        project_count = db.query(rfp_models.RFPProject).count()
        # 使用 v2 资产库
        from api.models.assets_v2 import EnterpriseCase, EnterpriseCertificate, CompanyAsset
        case_count = db.query(EnterpriseCase).count()
        cert_count = db.query(EnterpriseCertificate).count()
        asset_count = case_count + cert_count
        
        # 统计所有招标需求
        total_requirements = db.query(rfp_models.RFPRequirement).count()
        
        # 计算 Readiness: 如果没有需求则为 0，否则为 基础 30% + 每 2 个资产 + 10%，最高 95%
        readiness = 0.0
        if total_requirements > 0:
            readiness = min(95.0, 30.0 + (asset_count * 5.0))
        elif asset_count > 0:
             readiness = min(80.0, 10.0 + (asset_count * 10.0))
            
        # 检查身份核验：是否存在 'business_license' 类型的资产
        license_exists = db.query(CompanyAsset).filter(CompanyAsset.asset_tag == 'business_license').first() is not None
        
        # 待处理任务：统计 PENDING 状态的 Draft
        from api.models.bid_draft_v2 import BidDraft
        pending_tasks = db.query(BidDraft).filter(BidDraft.generation_status == 'PENDING').count()

        # 近期项目：获取最新的 3 个项目
        active_projects = []
        projects = db.query(rfp_models.RFPProject).order_by(rfp_models.RFPProject.id.desc()).limit(3).all()
        for p in projects:
            # 计算完成度 (基于 Draft 状态)
            from api.models.bid_draft_v2 import BidDraft
            total_drafts = db.query(BidDraft).filter(BidDraft.project_id == p.id).count()
            comp_drafts = db.query(BidDraft).filter(BidDraft.project_id == p.id, BidDraft.generation_status == 'COMPLETED').count()
            progress = (comp_drafts / total_drafts * 100.0) if total_drafts > 0 else 0.0
            
            active_projects.append({
                "name": p.project_name,
                "status": "编标中" if progress < 100 else "已完成",
                "progress": round(progress, 0),
                "time": "近期活跃"
            })

        return {
            "project_count": project_count,
            "asset_count": asset_count,
            "readiness": round(readiness, 1),
            "identity_verified": license_exists or (cert_count > 0),
            "pending_tasks": pending_tasks,
            "active_projects": active_projects
        }
    finally:
        db.close()
