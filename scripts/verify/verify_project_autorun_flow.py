import asyncio
import io
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import UploadFile

ROOT = Path("/root/it-bidding-copilot")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.core.database import SessionLocal
from api.routers import drafting_v2, enterprise_v2, rfp_v2
from api.services.context_service import get_or_create_primary_company

REAL_RFP_DOC = ROOT / "docs/定稿-招标文件-浙江省财务开发有限责任公司私有云项目.docx"


def build_upload_file(path: Path) -> UploadFile:
    return UploadFile(filename=path.name, file=io.BytesIO(path.read_bytes()))


def create_demo_vault(vault_root: Path) -> None:
    (vault_root / "资质证书").mkdir(parents=True, exist_ok=True)
    (vault_root / "项目案例").mkdir(parents=True, exist_ok=True)
    (vault_root / "人员简历").mkdir(parents=True, exist_ok=True)
    (vault_root / "资质证书" / "ISO20000.md").write_text("# ISO20000\n适用范围：IT服务管理。", encoding="utf-8")
    (vault_root / "项目案例" / "云平台案例.md").write_text("# 云平台案例\n项目名称：云平台建设项目\n项目内容：私有云与运维服务。", encoding="utf-8")
    (vault_root / "人员简历" / "王五.md").write_text("# 王五\n角色：高级工程师\n工作经验：8年。", encoding="utf-8")


async def wait_for_rfp_task(task_id: str, db, timeout_seconds: int = 120) -> dict:
    for _ in range(timeout_seconds):
        payload = await rfp_v2.get_task_status(task_id, db)
        if payload["status"] in {"completed", "failed"}:
            return payload
        await asyncio.sleep(1)
    raise TimeoutError(f"RFP task timeout: {task_id}")


async def wait_for_batch_task(task_id: str, timeout_seconds: int = 420) -> dict:
    for _ in range(timeout_seconds):
        payload = await drafting_v2.get_draft_task_status(task_id)
        if payload["status"] in {"completed", "failed"}:
            return payload
        await asyncio.sleep(1)
    raise TimeoutError(f"Project batch draft task timeout: {task_id}")


async def main() -> None:
    db = SessionLocal()
    try:
        company = get_or_create_primary_company(db)

        with TemporaryDirectory() as tmp_dir:
            vault_root = Path(tmp_dir) / "obsidian_demo_vault"
            create_demo_vault(vault_root)

            print("=== [1] 导入企业资质库 ===")
            ingest_result = await enterprise_v2.vault_ingest(
                company.id,
                enterprise_v2.VaultIngestRequest(vault_path=str(vault_root)),
                db,
            )
            print({"files_total": ingest_result["files_total"], "results_preview": ingest_result["results"][:3]})

            print("\n=== [2] 解析 RFP 并创建章节目录 ===")
            analyze_result = await rfp_v2.analyze_rfp(build_upload_file(REAL_RFP_DOC), db)
            status_result = await wait_for_rfp_task(analyze_result["task_id"], db)
            if status_result["status"] != "completed":
                raise RuntimeError(status_result)
            project_id = status_result["result"]["project_id"]
            await drafting_v2.get_document_outline(project_id, db)
            print({"project_id": project_id})

            print("\n=== [3] 项目级逐章自动继续验证 ===")
            batch_result = await drafting_v2.start_project_drafting(
                project_id,
                drafting_v2.ProjectDraftBatchRequest(max_sections=3),
                db,
            )
            print(batch_result)
            final_status = await wait_for_batch_task(batch_result["task_id"])
            print(final_status)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
