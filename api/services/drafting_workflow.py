from typing import Annotated, TypedDict, List

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from api.core.config import get_settings
from api.core.llm_client import LLMClient
from api.models.assets_v2 import EnterprisePersonnel
from api.models.rfp_v2 import RFPRequirement
from api.models.rfp_v2 import RFPProject
from api.services.model_runtime_service import get_model_runtime_info
from utils.hybrid_retriever import HybridRetriever
from utils.query_rewriter import StructuredQuery, QueryRewriter

class DraftState(TypedDict):
    """
    编标状态包：在各个 Agent 节点之间传递的上下文
    """
    project_id: int
    draft_id: int
    section_title: str
    requirements: List[str] # 该章节对应的标书要求
    context_materials: List[str] # 供应商方案、参考资料摘要
    
    current_content: str # 当前生成的内容 (Markdown)
    audit_feedback: str # 审计 Agent 的修改意见
    iteration_count: int
    is_approved: bool
    enterprise_context: List[str] # 企业资产匹配内容 (RAG)
    winning_points: str
    channel_id: str | None
    workflow_trace: dict


def build_audit_log_payload(
    existing_logs,
    *,
    phase: str | None = None,
    iteration: int = 0,
    is_approved: bool = False,
    final_feedback: str | None = None,
    workflow_trace: dict | None = None,
):
    if isinstance(existing_logs, dict):
        history = list(existing_logs.get("history", []))
        current_feedback = existing_logs.get("final_feedback", "")
    elif isinstance(existing_logs, list):
        history = list(existing_logs)
        current_feedback = ""
    else:
        history = []
        current_feedback = ""

    if phase is not None:
        import time

        history.append(
            {
                "timestamp": time.time(),
                "phase": phase,
                "iteration": iteration,
                "is_approved": is_approved,
            }
        )

    return {
        "history": history,
        "final_feedback": final_feedback if final_feedback is not None else current_feedback,
        "workflow_trace": workflow_trace if workflow_trace is not None else (existing_logs.get("workflow_trace") if isinstance(existing_logs, dict) else None),
    }

class DraftingWorkflow:
    def __init__(self, db: Session):
        self.db = db
        self.workflow = StateGraph(DraftState)
        self._build_graph()

    def _build_graph(self):
        # 定义节点
        self.workflow.add_node("researcher", self.research_node)
        self.workflow.add_node("writer", self.writing_node)
        self.workflow.add_node("auditor", self.auditing_node)
        self.workflow.add_node("refiner", self.refining_node)

        # 定义连线
        self.workflow.set_entry_point("researcher")
        self.workflow.add_edge("researcher", "writer")
        self.workflow.add_edge("writer", "auditor")
        
        # 条件路由：根据审计结果判定是结束还是进入润色迭代
        self.workflow.add_conditional_edges(
            "auditor",
            self.should_continue,
            {
                "continue": "refiner",
                "end": END
            }
        )
        self.workflow.add_edge("refiner", "auditor")

    async def research_node(self, state: DraftState) -> DraftState:
        """检索代理节点 (Researcher)：在企业资产库中寻找相关证据"""
        from api.core.logger import get_logger
        logger = get_logger("drafting_workflow")
        logger.info(f"--- [Researcher] Searching enterprise assets for: {state['section_title']} ---")
        
        channel_id = state.get("channel_id")
        if channel_id:
            from api.agents.callbacks import WebSockectStreamingCallback
            WebSockectStreamingCallback(channel_id, "Researcher Agent")._push(
                f"🔍 正在从企业知识库中探测与章节“{state['section_title']}”核心能力要求的匹配度...", status="searching"
            )
            
        retriever = HybridRetriever(self.db)
        
        # 使用 LLM 进行意图消歧
        raw_context = f"章节: {state['section_title']}\n要求: {chr(10).join(state['requirements'])}"
        sq = self._rewrite_query(raw_context)
        
        # 1. 语义搜索历史案例 (由 sq 驱动 SQL 过滤)
        cases = await retriever.search_cases(sq)
        case_texts = [f"【历史项目经验】{c.project_name} (ID: {c.id}): {c.description[:600]}" for c in cases]
        
        # 2. 搜索相关资质
        project = self.db.query(RFPProject).filter(RFPProject.id == state["project_id"]).first()
        company_id = project.company_id if project else None

        certs = await retriever.search_certificates(sq.semantic_context, company_id=company_id)
        cert_texts = []
        for ct in certs:
            line = f"【证照能力】{ct.raw_name} (ID: {ct.id}, 有效期至: {ct.expiry_date})"
            if ct.image_url:
                line += f"\n[IMAGE:{ct.image_url}]"
            cert_texts.append(line)

        personnel_texts = self._search_personnel_evidence(
            company_id=company_id,
            section_title=state["section_title"],
            requirements=state["requirements"],
        )

        # 3. [NEW] 搜索原子级证据分块 (表格、关键段落)
        chunks = await retriever.search_chunks(sq.semantic_context, company_id=company_id, limit=4)
        chunk_texts = [f"【原子级证据 - {ck.chunk_type}】来源文档ID: {ck.source_doc_id}\n内容: {ck.content}" for ck in chunks]
        
        # 4. [NEW] 胜手分析 (Winning Points Extraction)
        # 利用 LLM 对比案例与要求，总结“为什么是我们”
        state["winning_points"] = await self._generate_winning_points(
            section_title=state["section_title"],
            requirements=state["requirements"],
            case_texts=case_texts,
            cert_texts=cert_texts,
            chunk_texts=chunk_texts + personnel_texts,
        )
        workflow_trace = {
            **state.get("workflow_trace", {}),
            "enterprise_context_count": len(case_texts + cert_texts + personnel_texts + chunk_texts),
            "case_hits": len(case_texts),
            "certificate_hits": len(cert_texts),
            "personnel_hits": len(personnel_texts),
            "chunk_hits": len(chunk_texts),
        }

        new_state = {**state, "enterprise_context": case_texts + cert_texts + personnel_texts + chunk_texts, "workflow_trace": workflow_trace}
        self._save_checkpoint(new_state, "RESEARCH_COMPLETED")
        return new_state

    async def writing_node(self, state: DraftState) -> DraftState:
        """主笔代理节点 (Writer)：生成循证驱动的初稿"""
        from api.core.logger import get_logger
        logger = get_logger("drafting_workflow")
        logger.info(f"--- [Writer] Generating grounded draft for: {state['section_title']} ---")
        
        channel_id = state.get("channel_id")
        from api.agents.callbacks import WebSockectStreamingCallback
        callback = WebSockectStreamingCallback(channel_id, "Writer Agent") if channel_id else None
        
        if callback:
            callback._push(f"✍️ 正在基于 {len(state.get('enterprise_context', []))} 条企业证据撰写标书正文...", status="writing")
            
        content = await self._generate_draft_content(state)
        new_state = {
            **state,
            "current_content": content,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "workflow_trace": {
                **state.get("workflow_trace", {}),
                "draft_content_length": len(content),
            },
        }
        self._save_checkpoint(new_state, "DRAFT_COMPLETED")
        return new_state

    async def auditing_node(self, state: DraftState) -> DraftState:
        """审计代理节点 (Auditor)：验证响应真实性与合规性"""
        from api.core.logger import get_logger
        logger = get_logger("drafting_workflow")
        logger.info(f"--- [Auditor] Verifying citations for: {state['section_title']} ---")
        
        channel_id = state.get("channel_id")
        if channel_id:
            from api.agents.callbacks import WebSockectStreamingCallback
            WebSockectStreamingCallback(channel_id, "Auditor Agent")._push(
                "🛡️ 正在进行红队合规性审计，查验所有证据来源的真实性...", status="thinking"
            )
            
        feedback = await self._audit_draft(state)
        is_approved = "APPROVED" in feedback.upper()
        
        new_state = {
            **state,
            "audit_feedback": feedback,
            "is_approved": is_approved,
            "workflow_trace": {
                **state.get("workflow_trace", {}),
                "audit_feedback_length": len(feedback),
                "approved": is_approved,
            },
        }
        self._save_checkpoint(new_state, "AUDIT_COMPLETED")
        return new_state

    def _save_checkpoint(self, state: DraftState, phase: str):
        """将当前状态持久化到数据库，用于断点续传"""
        import time
        from api.models.bid_draft_v2 import BidDraft
        draft = self.db.query(BidDraft).filter(BidDraft.id == state["draft_id"]).first()
        if draft:
            # 记录审计日志快照
            draft.audit_logs = build_audit_log_payload(
                draft.audit_logs,
                phase=phase,
                iteration=state.get("iteration_count", 0),
                is_approved=state.get("is_approved", False),
                workflow_trace=state.get("workflow_trace"),
            )
            draft.content_markdown = state.get("current_content", "")
            if state.get("winning_points"):
                draft.winning_points = state["winning_points"]
            self.db.commit()

    async def refining_node(self, state: DraftState) -> DraftState:
        """润色代理节点 (Refiner)：修正与提升"""
        from api.core.logger import get_logger
        logger = get_logger("drafting_workflow")
        logger.info(f"--- [Refiner] Refining draft based on feedback ---")
        
        refined_content = await self._refine_draft(state)
        return {
            **state,
            "current_content": refined_content,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "workflow_trace": {
                **state.get("workflow_trace", {}),
                "refine_rounds": state.get("workflow_trace", {}).get("refine_rounds", 0) + 1,
            },
        }

    def should_continue(self, state: DraftState):
        if state["is_approved"] or state["iteration_count"] >= 3:
            return "end"
        return "continue"

    async def run(self, draft_id: int, channel_id: str = None) -> dict:
        """主入口：运行章节生成工作流 (异步)"""
        from api.models.bid_draft_v2 import BidDraft, ProjectMaterial
        from api.core.logger import get_logger
        logger = get_logger("drafting_workflow")
        
        draft = self.db.query(BidDraft).filter(BidDraft.id == draft_id).first()
        if not draft:
            raise ValueError(f"Draft {draft_id} not found")

        # 1. 组装标书要求 (RFP Requirements)
        reqs = self.db.query(RFPRequirement).filter(
            RFPRequirement.project_id == draft.project_id,
            RFPRequirement.original_section == draft.section_title
        ).all()
        req_list = [f"[{r.clause_index}] {r.description} (分值: {r.max_score})" for r in reqs]
        
        # 2. 组装项目素材 (Context Materials)
        materials = self.db.query(ProjectMaterial).filter(
            ProjectMaterial.project_id == draft.project_id
        ).all()
        material_list = [f"参考文件: {m.filename}\n内容摘要: {m.parsed_content or '未解析'}" for m in materials]
        
        initial_state = {
            "project_id": draft.project_id,
            "draft_id": draft.id,
            "section_title": draft.section_title,
            "requirements": req_list,
            "context_materials": material_list,
            "enterprise_context": [],
            "current_content": "",
            "audit_feedback": "",
            "iteration_count": 0,
            "is_approved": False,
            "winning_points": "",
            "channel_id": channel_id,
            "workflow_trace": {
                "model_runtime": get_model_runtime_info(),
                "requirements_count": len(req_list),
                "context_materials_count": len(material_list),
            },
        }
        
        app = self.workflow.compile()
        logger.info(f"Invoking workflow for draft {draft_id}...")
        final_state = await app.ainvoke(initial_state)
        
        # 更新数据库
        draft.content_markdown = final_state["current_content"]
        draft.generation_status = "COMPLETED" if final_state.get("is_approved", False) else "REVIEWING"
        draft.audit_logs = build_audit_log_payload(
            draft.audit_logs,
            final_feedback=final_state["audit_feedback"],
            iteration=final_state.get("iteration_count", 0),
            is_approved=final_state.get("is_approved", False),
            workflow_trace=final_state.get("workflow_trace"),
        )
        draft.source_fragments = final_state.get("enterprise_context", []) + final_state.get("context_materials", [])
        if final_state.get("winning_points"):
            draft.winning_points = final_state["winning_points"]
        self.db.commit()
        logger.info(f"Workflow completed for draft {draft_id}")
        return final_state

    def _llm_enabled(self) -> bool:
        settings = get_settings()
        return bool(settings.resolved_llm_api_key and settings.resolved_llm_model)

    def _search_personnel_evidence(self, *, company_id: int | None, section_title: str, requirements: List[str]) -> List[str]:
        if not company_id:
            return []

        merged = f"{section_title}\n{chr(10).join(requirements)}"
        role_keywords = ["项目负责人", "项目经理", "实施团队", "信息安全专员", "团队人员", "工程师", "社保"]
        if not any(keyword in merged for keyword in role_keywords):
            return []

        personnel = (
            self.db.query(EnterprisePersonnel)
            .filter(EnterprisePersonnel.company_id == company_id)
            .order_by(EnterprisePersonnel.id.desc())
            .limit(5)
            .all()
        )
        texts = []
        for person in personnel:
            line = f"【人员能力】{person.name} ({person.role or '角色待核验'}, 等级: {person.level or '待核验'})"
            if person.resume_text:
                line += f"\n{person.resume_text[:400]}"
            if person.social_security_image_url:
                line += f"\n[IMAGE:{person.social_security_image_url}]"
            texts.append(line)
        return texts

    def _rewrite_query(self, raw_context: str) -> StructuredQuery:
        if self._llm_enabled():
            try:
                client = LLMClient(role="ANALYSIS")
                rewriter = QueryRewriter(client.llm)
                return rewriter.rewrite_requirement(raw_context)
            except Exception:
                pass
        return QueryRewriter(llm=None)._fallback_rewrite(raw_context)

    async def _generate_winning_points(
        self,
        *,
        section_title: str,
        requirements: List[str],
        case_texts: List[str],
        cert_texts: List[str],
        chunk_texts: List[str],
    ) -> str:
        if self._llm_enabled():
            try:
                client = LLMClient(role="ANALYSIS")
                strategy_prompt = f"""
                对比以下要求与我司匹配案例，总结 2-3 条针对本项目的“核心竞争优势(Winning Points)”。
                项目章节: {section_title}
                要求摘要: {chr(10).join(requirements)}
                匹配案例: {chr(10).join(case_texts)}
                """
                strategy_res = await client.llm.ainvoke(strategy_prompt)
                return strategy_res.content
            except Exception:
                pass

        points = []
        if cert_texts:
            points.append("已检索到相关资质证照，可支撑资格与合规性响应。")
        if case_texts:
            points.append("已检索到同类项目案例，可作为实施经验与交付能力证明。")
        if chunk_texts:
            points.append("已定位到原子级证据片段，可用于支撑关键技术条款与截图要求。")
        if not points:
            points.append("当前企业证据较弱，需补充更直接的项目案例或资质材料。")
        return "\n".join(f"- {point}" for point in points[:3])

    async def _generate_draft_content(self, state: DraftState) -> str:
        if self._llm_enabled():
            try:
                client = LLMClient(role="WRITER", callbacks=[])
                prompt = f"""
                你是一名资深投标主笔。请根据以下资料撰写标书章节。
                【目标章节】：{state['section_title']}
                【目标标书要求】：
                {chr(10).join(state['requirements'])}
                【可引用的参考物料 (项目相关)】：
                {chr(10).join(state['context_materials'])}
                【可引用的企业资产 (RAG 检索结果)】：
                {chr(10).join(state.get('enterprise_context', []))}
                【本项目核心胜手分析 (Winning Points)】：
                {state.get('winning_points', '暂无针对性优势，请通用撰写')}
                【撰写准则】：
                1. 证据驱动。
                2. 拒绝虚构。
                3. 使用 Markdown。
                """
                response = await client.llm.ainvoke(prompt)
                return response.content
            except Exception:
                pass

        lines = [
            f"# {state['section_title']}",
            "## 章节响应说明",
            "投标人已依据招标文件相关条款对本章节进行逐项响应，以下内容仅引用当前项目物料与企业资产库中可核验的信息。",
            "## 条款逐项响应",
        ]
        for idx, requirement in enumerate(state["requirements"], start=1):
            lines.append(f"### 要求 {idx}")
            lines.append(f"- 招标要求: {requirement}")
            evidence = state.get("enterprise_context", [])
            if evidence:
                lines.append(f"- 响应说明: 投标人已结合现有企业证据进行响应，重点证据见资产片段 {idx}。")
                lines.append(f"- 证据摘要: {evidence[min(idx - 1, len(evidence) - 1)][:500]}")
            else:
                lines.append("- 响应说明: 当前企业资产库暂无直接证据，相关信息以 [待补充数据] 标识，需人工补齐。")
        if state.get("context_materials"):
            lines.append("## 项目参考物料")
            for material in state["context_materials"][:3]:
                lines.append(f"- {material[:500]}")
        if state.get("winning_points"):
            lines.append("## 核心竞争优势")
            lines.append(state["winning_points"])
        return "\n".join(lines)

    async def _audit_draft(self, state: DraftState) -> str:
        if self._llm_enabled():
            try:
                client = LLMClient(role="AUDITOR")
                audit_prompt = f"""
                你是一名拥有 10 年丰富经验的政府采招办评标委员会主任。
                任务：对照以下标书原始要求，严格审计 AI 生成的投标文件草稿。
                【标书原始要求】：
                {chr(10).join(state['requirements'])}
                【AI 生成的草稿】：
                {state['current_content']}
                输出要求：
                - 如果合规，请回复 "APPROVED"。
                - 如果不合规，请逐条列出“修改意见”，并回复 "FIX_REQUIRED"。
                """
                response = await client.llm.ainvoke(audit_prompt)
                return response.content.strip()
            except Exception:
                pass

        missing = []
        for requirement in state["requirements"]:
            snippet = requirement[:24]
            if snippet and snippet not in state["current_content"]:
                missing.append(requirement)
        if "[待补充数据]" in state["current_content"]:
            missing.append("存在待补充数据占位符")
        if missing:
            return "FIX_REQUIRED\n" + "\n".join(f"- {item[:120]}" for item in missing[:5])
        return "APPROVED"

    async def _refine_draft(self, state: DraftState) -> str:
        if self._llm_enabled():
            try:
                client = LLMClient(role="SYNTHESIS")
                refine_prompt = f"""
                你是一名专业的商务文书润色专家。
                任务：根据审计组长的反馈，修正并润色投标文件草稿。
                【原始草稿】：
                {state['current_content']}
                【审计反馈】：
                {state['audit_feedback']}
                """
                response = await client.llm.ainvoke(refine_prompt)
                return response.content
            except Exception:
                pass

        refined = state["current_content"].replace("[待补充数据]", "待招标人进一步澄清后补充")
        if "FIX_REQUIRED" in state["audit_feedback"] and "## 风险说明" not in refined:
            refined += "\n\n## 风险说明\n- 本章节仍存在需人工补证的条目，提交前需完成最终核验。"
        return refined

    async def rewrite_selection(self, draft_id: int, text: str) -> str:
        """根据选中的文本进行定向润色"""
        from api.models.bid_draft_v2 import BidDraft
        if not self._llm_enabled():
            return f"{text} (已尝试润色，但 LLM 未启用)"

        draft = self.db.query(BidDraft).filter(BidDraft.id == draft_id).first()
        section_title = draft.section_title if draft else "标书章节"

        try:
            client = LLMClient(role="SYNTHESIS")
            prompt = f"""
            你是一名专业的标书专家。请对以下选中的文本进行“专业润色”，使其更符合技术标书的语言风格。
            
            【所属章节】：{section_title}
            【待润色文本】：
            {text}
            
            【润色要求】：
            1. 语气专业、客观、严谨。
            2. 强化竞争优势，避免口语化。
            3. 保持 Markdown 格式（如果原文有）。
            4. 直接输出润色后的文本，不要带前言和解释。
            """
            response = await client.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception as e:
            from api.core.logger import get_logger
            get_logger("drafting_workflow").error(f"Error in rewrite_selection: {e}")
            return text
