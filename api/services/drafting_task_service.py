import asyncio
import uuid

from sqlalchemy.orm import Session

from api.core.database import SessionLocal
from api.core.logger import get_logger
from api.models.bid_draft_v2 import BidDraft
from api.services.drafting_workflow import DraftingWorkflow
from api.services.task_registry import task_registry

logger = get_logger("drafting_task_service")


def _has_meaningful_content(draft: BidDraft) -> bool:
    return bool((draft.content_markdown or "").strip())


def _select_project_drafts(
    drafts: list[BidDraft], *, only_incomplete: bool = False, max_drafts: int | None = None
) -> list[BidDraft]:
    selected = drafts
    if only_incomplete:
        selected = [
            draft
            for draft in drafts
            if draft.generation_status != "COMPLETED" or not _has_meaningful_content(draft)
        ]
    return selected[:max_drafts] if max_drafts else selected


async def start_draft_generation(*, draft_id: int, channel_id: str | None = None) -> str:
    task_id = f"draft_{uuid.uuid4().hex}"
    await task_registry.create(task_id, stage="queued")
    asyncio.create_task(_run_draft_generation_task(task_id=task_id, draft_id=draft_id, channel_id=channel_id))
    return task_id


async def start_project_draft_generation(
    *, project_id: int, max_drafts: int | None = None, only_incomplete: bool = False
) -> str:
    task_id = f"draft_project_{uuid.uuid4().hex}"
    await task_registry.create(task_id, stage="queued")
    asyncio.create_task(
        _run_project_draft_generation_task(
            task_id=task_id,
            project_id=project_id,
            max_drafts=max_drafts,
            only_incomplete=only_incomplete,
        )
    )
    return task_id


async def _run_draft_generation_task(*, task_id: str, draft_id: int, channel_id: str | None = None) -> None:
    db: Session = SessionLocal()
    try:
        draft = db.query(BidDraft).filter(BidDraft.id == draft_id).first()
        if draft is None:
            await task_registry.update(task_id, status="failed", stage="failed", error=f"Draft {draft_id} not found")
            return

        draft.generation_status = "DRAFTING"
        db.commit()

        await task_registry.update(task_id, status="running", stage="researching")
        workflow = DraftingWorkflow(db)
        final_state = await workflow.run(draft_id, channel_id)

        draft = db.query(BidDraft).filter(BidDraft.id == draft_id).first()
        if draft is not None:
            draft.generation_status = "COMPLETED" if final_state.get("is_approved", False) else "REVIEWING"
            db.commit()

        await task_registry.update(
            task_id,
            status="completed",
            stage="completed",
            result={
                "draft_id": draft_id,
                "project_id": draft.project_id,
                "content": final_state["current_content"],
                "audit_feedback": final_state.get("audit_feedback", ""),
                "workflow_trace": final_state.get("workflow_trace", {}),
            },
        )
    except Exception as exc:
        logger.exception("Draft generation task failed: %s", task_id)
        draft = db.query(BidDraft).filter(BidDraft.id == draft_id).first()
        if draft is not None:
            draft.generation_status = "PENDING"
            draft.audit_logs = {"final_feedback": f"TASK_FAILED: {str(exc)}"}
            db.commit()
        await task_registry.update(task_id, status="failed", stage="failed", error=str(exc))
    finally:
        db.close()


async def _run_project_draft_generation_task(
    *, task_id: str, project_id: int, max_drafts: int | None = None, only_incomplete: bool = False
) -> None:
    db: Session = SessionLocal()
    try:
        drafts = (
            db.query(BidDraft)
            .filter(BidDraft.project_id == project_id)
            .order_by(BidDraft.section_index.asc(), BidDraft.id.asc())
            .all()
        )
        if not drafts:
            await task_registry.update(task_id, status="failed", stage="failed", error=f"Project {project_id} has no drafts")
            return

        selected_drafts = _select_project_drafts(drafts, only_incomplete=only_incomplete, max_drafts=max_drafts)
        if not selected_drafts:
            await task_registry.update(
                task_id,
                status="completed",
                stage="completed",
                result={
                    "project_id": project_id,
                    "total_sections": 0,
                    "completed_sections": [],
                    "selection_mode": "only_incomplete" if only_incomplete else "all",
                },
            )
            return
        workflow = DraftingWorkflow(db)
        completed_sections = []

        await task_registry.update(
            task_id,
            status="running",
            stage="starting",
            result={"project_id": project_id, "total_sections": len(selected_drafts), "completed_sections": []},
        )

        for index, draft in enumerate(selected_drafts, start=1):
            draft.generation_status = "DRAFTING"
            db.commit()

            await task_registry.update(
                task_id,
                status="running",
                stage="generating_section",
                result={
                    "project_id": project_id,
                    "total_sections": len(selected_drafts),
                    "current_section_index": index,
                    "current_section_title": draft.section_title,
                    "selection_mode": "only_incomplete" if only_incomplete else "all",
                    "completed_sections": completed_sections,
                },
            )

            final_state = await workflow.run(draft.id, str(draft.id))
            db.refresh(draft)
            draft.generation_status = "COMPLETED" if final_state.get("is_approved", False) else "REVIEWING"
            db.commit()

            completed_sections.append(
                {
                    "draft_id": draft.id,
                    "section_title": draft.section_title,
                    "content_length": len((final_state.get("current_content") or "").strip()),
                    "approved": final_state.get("is_approved", False),
                }
            )

        await task_registry.update(
            task_id,
            status="completed",
            stage="completed",
            result={
                "project_id": project_id,
                "total_sections": len(selected_drafts),
                "selection_mode": "only_incomplete" if only_incomplete else "all",
                "completed_sections": completed_sections,
            },
        )
    except Exception as exc:
        logger.exception("Project draft generation task failed: %s", task_id)
        await task_registry.update(task_id, status="failed", stage="failed", error=str(exc))
    finally:
        db.close()
