import asyncio
import io
import sys
from pathlib import Path

from fastapi import UploadFile

ROOT = Path("/root/it-bidding-copilot")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.core.database import SessionLocal
from api.routers import drafting_v2, enterprise_v2, rfp_v2
from api.services.context_service import get_or_create_primary_company

REAL_ENTERPRISE_DOC = ROOT / "docs/商务技术文件.docx"
REAL_RFP_DOC = ROOT / "docs/定稿-招标文件-浙江省财务开发有限责任公司私有云项目.docx"


def build_upload_file(path: Path) -> UploadFile:
    return UploadFile(filename=path.name, file=io.BytesIO(path.read_bytes()))


async def wait_for_rfp_task(task_id: str, db, timeout_seconds: int = 120) -> dict:
    for _ in range(timeout_seconds):
        payload = await rfp_v2.get_task_status(task_id, db)
        if payload["status"] in {"completed", "failed"}:
            return payload
        await asyncio.sleep(1)
    raise TimeoutError(f"RFP task timeout: {task_id}")


async def wait_for_draft_task(task_id: str, timeout_seconds: int = 120) -> dict:
    for _ in range(timeout_seconds):
        payload = await drafting_v2.get_draft_task_status(task_id)
        if payload["status"] in {"completed", "failed"}:
            return payload
        await asyncio.sleep(1)
    raise TimeoutError(f"Draft task timeout: {task_id}")


async def main() -> None:
    if not REAL_ENTERPRISE_DOC.exists() or not REAL_RFP_DOC.exists():
        raise FileNotFoundError("真实联调文档不存在，请检查 docs/ 下的 docx 文件。")

    db = SessionLocal()
    try:
        company = get_or_create_primary_company(db)

        print("=== [1] 企业资产 bulk-ingest 真实联调 ===")
        ingest_result = await enterprise_v2.bulk_ingest(
            company.id,
            [build_upload_file(REAL_ENTERPRISE_DOC)],
            db,
        )
        print(ingest_result)

        print("\n=== [2] RFP analyze -> status -> deviation 真实联调 ===")
        analyze_result = await rfp_v2.analyze_rfp(build_upload_file(REAL_RFP_DOC), db)
        print(analyze_result)
        status_result = await wait_for_rfp_task(analyze_result["task_id"], db)
        print(status_result["status"], status_result["stage"])
        if status_result["status"] != "completed":
            raise RuntimeError(status_result)

        project_id = status_result["result"]["project_id"]
        print({"analysis_trace": status_result["result"].get("analysis_trace", {})})
        deviation_result = await rfp_v2.get_deviation_matrix(project_id, db)
        print(f"project_id={project_id}, deviation_count={len(deviation_result)}")

        print("\n=== [3] bid draft 章节逐章生成真实联调 ===")
        outline = await drafting_v2.get_document_outline(project_id, db)
        print(f"outline_count={len(outline['outline'])}")
        drafts = await drafting_v2.get_drafts(project_id, db)
        if not drafts:
            raise RuntimeError("未生成任何章节草稿。")

        chapter_results = []
        for index, draft in enumerate(drafts, start=1):
            print(f"\n--- [3.{index}] 生成章节: {draft.section_title} (draft_id={draft.id}) ---")
            draft_start = await drafting_v2.start_drafting_aligned(draft.id, db)
            print(draft_start)
            draft_status = await wait_for_draft_task(draft_start["task_id"], timeout_seconds=240)
            print(draft_status["status"], draft_status["stage"])
            if draft_status["status"] != "completed":
                raise RuntimeError(draft_status)
            workflow_trace = draft_status.get("result", {}).get("workflow_trace", {})
            print({"workflow_trace": workflow_trace})

            db.expire_all()
            refreshed_draft = next(item for item in await drafting_v2.get_drafts(project_id, db) if item.id == draft.id)
            content_length = len((refreshed_draft.content_markdown or "").strip())
            if content_length == 0:
                raise RuntimeError(f"章节 {refreshed_draft.section_title} 生成完成但正文为空")

            chapter_results.append(
                {
                    "draft_id": refreshed_draft.id,
                    "section_title": refreshed_draft.section_title,
                    "content_length": content_length,
                    "approved": workflow_trace.get("approved"),
                }
            )

        print({"chapter_results_preview": chapter_results[:5], "total_generated": len(chapter_results)})

        review_result = await drafting_v2.run_red_team_review(project_id, db)
        print(
            {
                "project_id": review_result["project_id"],
                "win_rate": review_result["win_rate"],
                "approved_drafts": review_result["approved_drafts"],
                "total_drafts": review_result["total_drafts"],
            }
        )

        export_response = await drafting_v2.export_docx(project_id, db)
        print({"exported_filename": export_response.filename})
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
