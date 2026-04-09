import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from api.core.database import SessionLocal
from api.models.assets_v2 import Company, EnterpriseCertificate, EnterprisePersonnel, EnterpriseCase

class AssetStatisticsProvider:
    """
    资产库看板数据提供者：
    输出资质、人员、业绩的量化统计，用于支撑“家底展示”与“差异分析”。
    """
    def __init__(self, db: Session):
        self.db = db

    def get_full_dashboard(self) -> dict:
        company = self.db.query(Company).first()
        if not company:
            return {"error": "No company data found"}

        stats = {
            "company_info": {
                "name": company.company_name,
                "credit_code": company.unified_social_credit_code,
                "capital": company.registered_capital,
                "representative": company.legal_representative
            },
            "certificates": self._get_cert_stats(company.id),
            "personnel": self._get_personnel_stats(company.id),
            "cases": self._get_case_stats(company.id)
        }
        return stats

    def _get_cert_stats(self, company_id: int):
        # 按类型统计资质数量
        results = (
            self.db.query(EnterpriseCertificate.cert_type, func.count(EnterpriseCertificate.id))
            .filter(EnterpriseCertificate.company_id == company_id)
            .group_by(EnterpriseCertificate.cert_type)
            .all()
        )
        cert_list = self.db.query(EnterpriseCertificate).filter(EnterpriseCertificate.company_id == company_id).all()
        
        return {
            "total": sum(count for _, count in results),
            "by_type": {t: c for t, c in results},
            "details": [{"name": c.raw_name, "level": c.cert_level, "expiry": str(c.expiry_date)} for c in cert_list]
        }

    def _get_personnel_stats(self, company_id: int):
        # 按职级统计人数
        results = (
            self.db.query(EnterprisePersonnel.level, func.count(EnterprisePersonnel.id))
            .filter(EnterprisePersonnel.company_id == company_id)
            .group_by(EnterprisePersonnel.level)
            .all()
        )
        return {
            "total": sum(count for _, count in results),
            "by_level": {l: c for l, c in results}
        }

    def _get_case_stats(self, company_id: int):
        total = self.db.query(EnterpriseCase).filter(EnterpriseCase.company_id == company_id).count()
        return {"total": total}

if __name__ == "__main__":
    db = SessionLocal()
    try:
        provider = AssetStatisticsProvider(db)
        data = provider.get_full_dashboard()
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
    finally:
        db.close()
