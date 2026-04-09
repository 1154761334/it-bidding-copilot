import datetime
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import api.models  # noqa: F401
from api.core.database import SessionLocal
from api.models.assets_v2 import Company, EnterpriseCertificate
from api.models.bid_draft_v2 import BidDraft
from api.models.rfp_v2 import RFPProject, RFPRequirement


def main() -> None:
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.company_name == "测试演示公司").first()
        if company is None:
            company = Company(
                company_name="测试演示公司",
                description="用于演示 IT Bidding Copilot 核心流程的示例企业",
                unified_social_credit_code="91330100TEST00001X",
                legal_representative="张三",
                registered_capital="5000万元",
                address="杭州市滨江区测试路88号",
            )
            db.add(company)
            db.commit()
            db.refresh(company)

        cert = db.query(EnterpriseCertificate).filter(EnterpriseCertificate.company_id == company.id).first()
        if cert is None:
            db.add(
                EnterpriseCertificate(
                    company_id=company.id,
                    raw_name="ISO9001质量管理体系认证证书",
                    cert_type="ISO9001",
                    certification_scope="私有云建设、系统集成与运维服务",
                )
            )
            db.commit()

        project = db.query(RFPProject).filter(RFPProject.project_name == "演示私有云项目").first()
        if project is None:
            project = RFPProject(
                company_id=company.id,
                project_name="演示私有云项目",
                budget=9800000,
                deadline=datetime.date(2026, 5, 1),
                status="DRAFTING",
            )
            db.add(project)
            db.commit()
            db.refresh(project)

        if db.query(RFPRequirement).filter(RFPRequirement.project_id == project.id).count() == 0:
            db.add_all(
                [
                    RFPRequirement(
                        project_id=project.id,
                        original_section="项目总体响应",
                        clause_index="3.1.1",
                        category="TECHNICAL",
                        description="投标人应提供私有云总体架构设计方案，覆盖计算、存储、网络与安全域。",
                        is_fatal=False,
                        max_score=15,
                        evidence_required="总体技术方案",
                        match_status="PARTIAL",
                        match_comment="已检索到2个相似案例，可支撑总体架构响应。",
                    ),
                    RFPRequirement(
                        project_id=project.id,
                        original_section="项目总体响应",
                        clause_index="3.1.2",
                        category="QUALIFICATION",
                        description="投标人应具备有效的 ISO9001 质量管理体系认证。",
                        is_fatal=True,
                        max_score=0,
                        evidence_required="ISO9001证书",
                        match_status="PASS",
                        match_comment="已匹配到ISO9001质量管理体系认证证书。",
                    ),
                    RFPRequirement(
                        project_id=project.id,
                        original_section="服务保障方案",
                        clause_index="4.2.1",
                        category="TECHNICAL",
                        description="投标人需提供7x24运维服务与故障分级响应机制。",
                        is_fatal=False,
                        max_score=10,
                        evidence_required="运维服务方案",
                        match_status="PARTIAL",
                        match_comment="运维章节可基于既有服务体系进行响应。",
                    ),
                ]
            )
            db.commit()

        if db.query(BidDraft).filter(BidDraft.project_id == project.id).count() == 0:
            db.add_all(
                [
                    BidDraft(
                        project_id=project.id,
                        section_title="项目总体响应",
                        section_index="1",
                        generation_status="COMPLETED",
                        content_markdown="## 建设目标\n投标人将提供覆盖计算、存储、网络与安全域的一体化私有云架构方案。",
                        audit_logs={"final_feedback": "APPROVED"},
                        source_fragments=["历史项目A：私有云一期建设", "ISO9001证书编号：TEST-ISO-001"],
                        winning_points="具备成熟私有云交付经验与质量体系认证。",
                    ),
                    BidDraft(
                        project_id=project.id,
                        section_title="服务保障方案",
                        section_index="2",
                        generation_status="COMPLETED",
                        content_markdown="## 服务体系\n投标人提供7x24运维保障、故障分级处置与升级机制。",
                        audit_logs={"final_feedback": "APPROVED"},
                        source_fragments=["运维服务手册V2", "历史项目B：驻场运维"],
                        winning_points="已有成熟运维流程与服务台制度。",
                    ),
                ]
            )
            db.commit()

        print({"company_id": company.id, "project_id": project.id})
    finally:
        db.close()


if __name__ == "__main__":
    main()
