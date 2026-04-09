import asyncio
import sys
import uuid
from pathlib import Path

ROOT = Path("/root/it-bidding-copilot")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.core.database import SessionLocal
from api.models.assets_v2 import Company, CompanyAsset, EnterpriseCase, EnterpriseCertificate, EnterprisePersonnel, SourceDocument
from api.routers import enterprise_v2


BUSINESS_DOC = ROOT / "docs/商务技术文件.docx"


async def main() -> None:
    db = SessionLocal()
    try:
        company = Company(company_name=f"商务技术文件预提验证企业-{uuid.uuid4().hex[:8]}")
        db.add(company)
        db.commit()
        db.refresh(company)

        print("=== [1] 商务技术文件预提资质入库 ===")
        payload = enterprise_v2.BusinessDocIngestRequest(
            file_path=str(BUSINESS_DOC),
            display_name=BUSINESS_DOC.name,
        )
        ingest_result = await enterprise_v2.business_doc_ingest(company.id, payload, db)
        print(ingest_result)

        print("\n=== [2] 重复导入去重验证 ===")
        second_result = await enterprise_v2.business_doc_ingest(company.id, payload, db)
        print(second_result)

        print("\n=== [3] 数据库沉淀结果 ===")
        source_doc = (
            db.query(SourceDocument)
            .filter(
                SourceDocument.company_id == company.id,
                SourceDocument.filename == BUSINESS_DOC.name,
                SourceDocument.local_path == str(BUSINESS_DOC.resolve()),
            )
            .first()
        )
        certs = db.query(EnterpriseCertificate).filter(EnterpriseCertificate.source_doc_id == source_doc.id).all()
        cases = db.query(EnterpriseCase).filter(EnterpriseCase.source_doc_id == source_doc.id).all()
        personnel = db.query(EnterprisePersonnel).filter(EnterprisePersonnel.company_id == company.id).all()
        text_assets = (
            db.query(CompanyAsset)
            .filter(
                CompanyAsset.company_id == company.id,
                CompanyAsset.asset_tag.in_(["authorization", "social_security", "business_doc_image"]),
            )
            .all()
        )
        print(
            {
                "source_doc_id": source_doc.id,
                "certificates_total": len(certs),
                "cases_total": len(cases),
                "personnel_total": len(personnel),
                "certificates_with_images": len([cert for cert in certs if cert.image_url]),
                "personnel_with_social_security_images": len([person for person in personnel if person.social_security_image_url]),
                "text_assets_total": len([asset for asset in text_assets if asset.asset_type == "text"]),
                "images_total": len([asset for asset in text_assets if asset.asset_tag == "business_doc_image"]),
                "certificates_preview": [cert.raw_name for cert in certs[:8]],
                "cases_preview": [case.project_name for case in cases[:8]],
                "personnel_preview": [person.name for person in personnel[:8]],
                "text_asset_preview": [
                    {"tag": asset.asset_tag, "name": asset.asset_name}
                    for asset in text_assets[:8]
                ],
            }
        )

        print("\n=== [4] 检索验证 ===")
        cert_search = await enterprise_v2.search_assets(company.id, "营业执照 ISO9001 项目负责人证书", db)
        case_search = await enterprise_v2.search_assets(company.id, "国资云 混合云 项目业绩", db)
        print(
            {
                "certificates_preview": cert_search["certificates"][:5],
                "cases_preview": cert_search["cases"][:3],
                "case_search_preview": case_search["cases"][:5],
            }
        )
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
