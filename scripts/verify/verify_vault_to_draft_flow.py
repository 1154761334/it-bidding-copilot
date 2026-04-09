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

    (vault_root / "资质证书" / "ISO27001.md").write_text(
        "# ISO27001 信息安全管理认证\n\n适用范围：政企云平台安全管理与运维。\n有效期：2028-12-31\n",
        encoding="utf-8",
    )
    (vault_root / "项目案例" / "金融云案例.md").write_text(
        "# 金融私有云项目案例\n\n项目名称：某金融机构私有云平台建设项目\n合同金额：1200万元\n项目内容：私有云平台建设、迁移、运维保障。\n",
        encoding="utf-8",
    )
    (vault_root / "人员简历" / "李四.md").write_text(
        "# 李四\n\n角色：架构师\n工作经验：10年\n具备私有云架构设计与交付经验。\n",
        encoding="utf-8",
    )


async def wait_for_rfp_task(task_id: str, db, timeout_seconds: int = 120) -> dict:
    for _ in range(timeout_seconds):
        payload = await rfp_v2.get_task_status(task_id, db)
        if payload["status"] in {"completed", "failed"}:
            return payload
        await asyncio.sleep(1)
    raise TimeoutError(f"RFP task timeout: {task_id}")


async def wait_for_draft_task(task_id: str, timeout_seconds: int = 240) -> dict:
    for _ in range(timeout_seconds):
        payload = await drafting_v2.get_draft_task_status(task_id)
        if payload["status"] in {"completed", "failed"}:
            return payload
        await asyncio.sleep(1)
    raise TimeoutError(f"Draft task timeout: {task_id}")


async def main() -> None:
    db = SessionLocal()
    try:
        company = get_or_create_primary_company(db)

        with TemporaryDirectory() as tmp_dir:
            vault_root = Path(tmp_dir) / "obsidian_demo_vault"
            create_demo_vault(vault_root)

            print("=== [1] 导入 Obsidian 企业资质库 ===")
            vault_payload = enterprise_v2.VaultIngestRequest(vault_path=str(vault_root))
            ingest_result = await enterprise_v2.vault_ingest(company.id, vault_payload, db)
            print({"files_total": ingest_result["files_total"], "results_preview": ingest_result["results"][:3]})

            print("\n=== [2] 解析真实 RFP ===")
            analyze_result = await rfp_v2.analyze_rfp(build_upload_file(REAL_RFP_DOC), db)
            status_result = await wait_for_rfp_task(analyze_result["task_id"], db)
            if status_result["status"] != "completed":
                raise RuntimeError(status_result)
            project_id = status_result["result"]["project_id"]
            print({"project_id": project_id, "analysis_trace": status_result["result"].get("analysis_trace", {})})

            print("\n=== [3] 用企业资质库驱动章节生成 ===")
            await drafting_v2.get_document_outline(project_id, db)
            drafts = await drafting_v2.get_drafts(project_id, db)
            target_drafts = drafts[:2]
            chapter_summaries = []
            for draft in target_drafts:
                print(f"--- 生成章节: {draft.section_title} (draft_id={draft.id}) ---")
                draft_start = await drafting_v2.start_drafting_aligned(draft.id, db)
                draft_status = await wait_for_draft_task(draft_start["task_id"])
                if draft_status["status"] != "completed":
                    raise RuntimeError(draft_status)
                db.expire_all()
                refreshed = next(item for item in await drafting_v2.get_drafts(project_id, db) if item.id == draft.id)
                chapter_summaries.append(
                    {
                        "draft_id": refreshed.id,
                        "section_title": refreshed.section_title,
                        "content_length": len((refreshed.content_markdown or "").strip()),
                        "source_fragments_count": len(refreshed.source_fragments or []),
                        "audit_logs": refreshed.audit_logs,
                    }
                )

            print({"chapter_summaries": chapter_summaries})
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
