import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path("/root/it-bidding-copilot")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.core.database import SessionLocal
from api.routers import enterprise_v2
from api.services.context_service import get_or_create_primary_company


def create_demo_vault(vault_root: Path) -> None:
    (vault_root / "资质证书").mkdir(parents=True, exist_ok=True)
    (vault_root / "项目案例").mkdir(parents=True, exist_ok=True)
    (vault_root / "人员简历").mkdir(parents=True, exist_ok=True)
    (vault_root / "商务模板").mkdir(parents=True, exist_ok=True)

    (vault_root / "资质证书" / "ISO9001.md").write_text(
        "# ISO9001 质量管理体系认证\n\n证书名称：ISO9001\n有效期：2028-12-31\n适用范围：政企云平台建设与运维服务\n",
        encoding="utf-8",
    )
    (vault_root / "项目案例" / "政务云案例.md").write_text(
        "# 政务云项目案例\n\n项目名称：某省政务云扩容项目\n合同金额：860万元\n项目内容：私有云平台建设、迁移与运维服务\n",
        encoding="utf-8",
    )
    (vault_root / "人员简历" / "张三.md").write_text(
        "# 张三\n\n角色：项目经理\n工作经验：12年\n参与多个政企云平台项目交付与运维。\n",
        encoding="utf-8",
    )
    (vault_root / "商务模板" / "投标承诺书.md").write_text(
        "# 投标承诺书\n\n本文件作为商务模板素材留存。\n",
        encoding="utf-8",
    )


async def main() -> None:
    db = SessionLocal()
    try:
        company = get_or_create_primary_company(db)

        with TemporaryDirectory() as tmp_dir:
            vault_root = Path(tmp_dir) / "obsidian_demo_vault"
            create_demo_vault(vault_root)

            print("=== [1] Obsidian Vault 导入场景验证 ===")
            payload = enterprise_v2.VaultIngestRequest(vault_path=str(vault_root))
            ingest_result = await enterprise_v2.vault_ingest(company.id, payload, db)
            print(
                {
                    "status": ingest_result["status"],
                    "files_total": ingest_result["files_total"],
                    "results_preview": ingest_result["results"][:4],
                }
            )

            print("\n=== [1.1] 重复导入去重验证 ===")
            second_ingest_result = await enterprise_v2.vault_ingest(company.id, payload, db)
            print(
                {
                    "status": second_ingest_result["status"],
                    "files_total": second_ingest_result["files_total"],
                    "results_preview": second_ingest_result["results"][:4],
                }
            )

            print("\n=== [2] 导入后资产检索验证 ===")
            cert_search = await enterprise_v2.search_assets(company.id, "ISO9001 质量管理", db)
            print({"certificates": cert_search["certificates"][:2], "cases": cert_search["cases"][:2]})

            case_search = await enterprise_v2.search_assets(company.id, "政务云 项目案例 私有云", db)
            print({"certificates": case_search["certificates"][:2], "cases": case_search["cases"][:2]})

            trust_score = await enterprise_v2.get_trust_score(db)
            print({"trust_score": trust_score})
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
