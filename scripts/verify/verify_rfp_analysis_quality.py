import asyncio
import io
import sys
from pathlib import Path

from fastapi import UploadFile

ROOT = Path("/root/it-bidding-copilot")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.core.database import SessionLocal
from api.models.assets_v2 import SourceDocument
from api.models.rfp_v2 import RFPProject, RFPRequirement
from api.routers import rfp_v2


REAL_RFP_DOC = ROOT / "docs/定稿-招标文件-浙江省财务开发有限责任公司私有云项目.docx"


def build_upload_file(path: Path) -> UploadFile:
    return UploadFile(filename=path.name, file=io.BytesIO(path.read_bytes()))


async def wait_for_rfp_task(task_id: str, db, *, started_after_source_id: int, timeout_seconds: int = 180) -> dict:
    for _ in range(timeout_seconds):
        payload = await rfp_v2.get_task_status(task_id, db)
        if payload["status"] in {"completed", "failed"}:
            return payload
        fallback_payload = build_db_fallback_result(db, started_after_source_id=started_after_source_id)
        if fallback_payload is not None:
            return fallback_payload
        await asyncio.sleep(1)
    raise TimeoutError(f"RFP task timeout: {task_id}")


def build_db_fallback_result(db, *, started_after_source_id: int) -> dict | None:
    source_doc = (
        db.query(SourceDocument)
        .filter(SourceDocument.filename == REAL_RFP_DOC.name)
        .order_by(SourceDocument.id.desc())
        .first()
    )
    if source_doc is None:
        return None
    if source_doc.id <= started_after_source_id:
        return None
    if source_doc.parse_status != "COMPLETED":
        return None

    project = (
        db.query(RFPProject)
        .filter(RFPProject.rfp_source_id == source_doc.id)
        .order_by(RFPProject.id.desc())
        .first()
    )
    if project is None:
        return None

    requirements = db.query(RFPRequirement).filter(RFPRequirement.project_id == project.id).all()
    if not requirements:
        return None

    return {
        "status": "completed",
        "stage": "completed",
        "result": {
            "project_id": project.id,
            "project_name": project.project_name,
            "analysis_trace": {"fallback_mode": "db_project_lookup"},
        },
    }


async def main() -> None:
    db = SessionLocal()
    try:
        print("=== [1] 真实采购文件识别 ===")
        latest_source_before = (
            db.query(SourceDocument)
            .filter(SourceDocument.filename == REAL_RFP_DOC.name)
            .order_by(SourceDocument.id.desc())
            .first()
        )
        started_after_source_id = latest_source_before.id if latest_source_before else 0
        analyze_result = await rfp_v2.analyze_rfp(build_upload_file(REAL_RFP_DOC), db)
        print(analyze_result)
        final_status = await wait_for_rfp_task(
            analyze_result["task_id"],
            db,
            started_after_source_id=started_after_source_id,
        )
        print(
            {
                "status": final_status["status"],
                "stage": final_status["stage"],
                "project_id": final_status.get("result", {}).get("project_id"),
                "project_name": final_status.get("result", {}).get("project_name"),
                "analysis_trace": final_status.get("result", {}).get("analysis_trace", {}),
            }
        )

        if final_status["status"] != "completed":
            raise RuntimeError(final_status)

        project_id = final_status["result"]["project_id"]

        print("\n=== [2] 项目建档质量校验 ===")
        quality = await rfp_v2.get_analysis_check(project_id, db)
        print(quality)

        print("\n=== [3] 偏离矩阵抽样 ===")
        deviation = await rfp_v2.get_deviation_matrix(project_id, db)
        print(
            {
                "deviation_count": len(deviation),
                "deviation_preview": deviation[:8],
            }
        )
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
