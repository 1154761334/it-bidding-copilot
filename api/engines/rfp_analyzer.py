import re
from typing import List, Dict, Any, Optional
import datetime
import asyncio
import json

from pydantic import BaseModel, Field
from api.core.llm_client import LLMClient

class ProjectInfo(BaseModel):
    name: str = Field(description="招标项目全称")
    budget: float = Field(description="招标预算金额(数值)")
    deadline: str = Field(description="投标截止日期")

class RequirementItem(BaseModel):
    original_section: str = Field(description="原始章节名称")
    clause_index: str = Field(description="条款编号")
    category: str = Field(description="分类: QUALIFICATION/TECHNICAL/COMMERCIAL/GENERAL")
    description: str = Field(description="要求描述")
    is_fatal: bool = Field(description="是否为废标项/红线项")
    max_score: float = Field(description="该项最高分值")
    evidence_required: str = Field(description="需要的证明材料")

class RFPAnalysisSchema(BaseModel):
    project_info: ProjectInfo
    requirements: List[RequirementItem]


class RFPReviewProjectInfo(BaseModel):
    name: str = ""
    budget: float = 0.0
    deadline: str = ""


class RFPReviewQualityFlags(BaseModel):
    has_scoring_section: bool = False
    has_requirement_section: bool = False
    has_qualification_section: bool = False


class RFPReviewSchema(BaseModel):
    project_info: RFPReviewProjectInfo
    quality_flags: RFPReviewQualityFlags
    notes: List[str] = Field(default_factory=list)

class RFPAnalyzer:
    """
    采购文件智能拆解引擎：
    1. 识别项目基础信息 (名称、预算、截止日期)
    2. 提取废标项 (带星号或强转项)
    3. 结构化评分表 (技术/商务/报价)
    """
    def __init__(self):
        # 结构化提取优先通过提示词约束与鲁棒 JSON 解析完成，避免模型对
        # response_format 支持不一致时直接阻断真实链路。
        self.ai = LLMClient(role="ANALYSIS")

    async def analyze_full_document(self, markdown_content: str) -> Dict[str, Any]:
        """
        利用大模型进行的标书全量结构化分析 (带工业级容错)
        """
        from api.core.logger import get_logger
        logger = get_logger("rfp_analyzer")
        
        logger.info("Starting RFP full document analysis...")
        prompt = f"""
        你是一个资深的政府/企业采购评标专家。请深入解析以下招标文件的 Markdown 内容，
        并严格按照要求的 JSON 格式提取出项目关键信息、所有资格门槛（废标项）以及所有评分细节。

        【招标文件 Markdown 内容开始】
        {markdown_content[:20000]}
        【招标文件 Markdown 内容结束】

        【输出要求】
        必须输出有效的 JSON 对象，包含:
        1. project_info: 包含 name, budget, deadline。
        2. requirements: 数组，包含所有评分点和废标项。
        """
        
        try:
            if not LLMClient.is_configured():
                raise RuntimeError("LLM is not configured")

            import json
            response = await asyncio.wait_for(self.ai.llm.ainvoke(prompt), timeout=25)
            raw_content = response.content
            
            # --- 工业级容错解析逻辑 ---
            # 1. 剥离 Markdown 语法糖
            clean_content = re.sub(r"```json\n?|```", "", raw_content).strip()
            
            try:
                # 优先尝试标准解析
                data = json.loads(clean_content)
            except json.JSONDecodeError:
                # 2. 启发式正则提取 (处理 LLM 在 JSON 前后塞废话的情况)
                match = re.search(r'\{.*\}', clean_content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                else:
                    raise
            
            # 3. Pydantic 结构化校验
            validated_data = RFPAnalysisSchema(**data)
            return await self._post_process_analysis(validated_data.model_dump(), markdown_content)
        except Exception as e:
            print(f"❌ [RFPAnalyzer] Extraction Failed, fallback enabled: {e}")
            return self._fallback_analysis(markdown_content)

    def generate_evaluator_mirror(self, extracted_requirements: List[Dict]):
        """
        生成“评标师对照表”
        """
        if not extracted_requirements:
            return []
        # 对需求进行优先级排序：废标项在前，高分项在后
        sorted_reqs = sorted(extracted_requirements, key=lambda x: (not x.get("is_fatal", False), -x.get("max_score", 0)))
        return sorted_reqs

    async def calculate_go_no_go_score(self, analyzed_rfp: Dict, enterprise_assets: List[Dict]) -> Dict[str, Any]:
        """
        根据标书需求项与企业资产的“语义重合度”计算真实的 Go/No-Go 评分
        """
        from api.core.logger import get_logger
        logger = get_logger("rfp_analyzer")
        logger.info("Calculating Go/No-Go score...")
        
        requirements = analyzed_rfp.get("requirements", [])
        if not requirements:
            return {"score": 0, "reason": "未发现有效需求项"}
        
        # 简化逻辑：计算有多少个强制性要求(is_fatal)在资产库中有匹配
        fatal_reqs = [r for r in requirements if r.get("is_fatal")]
        if not fatal_reqs:
            # 如果没有强制项，给一个基础分
            return {"score": 85, "reason": "未发现废标性红线，基本资质符合"}

        # 这里未来应该对接向量数据库进行语义匹配
        # 目前先用关键词碰撞模拟真实算法
        matches = 0
        reasons = []
        for freq in fatal_reqs:
            desc = freq.get("description", "").lower()
            found = False
            for asset in enterprise_assets:
                if any(keyword in asset.get("content", "").lower() for keyword in desc.split()):
                    found = True
                    break
            if found:
                matches += 1
            else:
                reasons.append(f"缺少关键项证明: {freq.get('clause_index')} - {freq.get('description')}")

        score = int((matches / len(fatal_reqs)) * 100)
        return {
            "score": score,
            "reasons": reasons[:2], # 只返回前两个原因
            "status": "GO" if score > 70 else "NO-GO"
        }

    def _fallback_analysis(self, markdown_content: str) -> Dict[str, Any]:
        project_name = self._extract_project_name(markdown_content)
        deadline = self._extract_deadline(markdown_content)
        budget = self._extract_budget(markdown_content)
        requirements = self._extract_requirements(markdown_content)

        if not requirements:
            requirements = [
                {
                    "original_section": "自动识别章节",
                    "clause_index": "AUTO-1",
                    "category": "GENERAL",
                    "description": "需人工复核原文并补充结构化需求。",
                    "is_fatal": False,
                    "max_score": 0.0,
                    "evidence_required": "原始招标文件",
                }
            ]

        payload = {
            "project_info": {
                "name": project_name,
                "budget": budget,
                "deadline": deadline,
            },
            "requirements": requirements,
        }
        validated = RFPAnalysisSchema(**payload)
        return self._post_process_analysis_sync(validated.model_dump(), markdown_content)

    def _extract_project_name(self, markdown_content: str) -> str:
        patterns = [
            r"项目名称[：:\s]+([^\n]+)",
            r"招标项目名称[：:\s]+([^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, markdown_content)
            if match:
                return match.group(1).strip()
        for line in markdown_content.splitlines():
            if "项目" in line and len(line.strip()) <= 60:
                return line.strip()
        return "未命名招标项目"

    def _extract_budget(self, markdown_content: str) -> float:
        match = re.search(r"(预算|最高限价|采购金额)[^\d]{0,10}(\d+(?:\.\d+)?)\s*(万|万元|元)", markdown_content)
        if not match:
            return 0.0
        value = float(match.group(2))
        unit = match.group(3)
        return value * 10000 if "万" in unit else value

    def _extract_deadline(self, markdown_content: str) -> str:
        match = re.search(
            r"(投标截止时间|开标时间)[：:\s]*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})",
            markdown_content,
        )
        if not match:
            return ""
        year, month, day = int(match.group(2)), int(match.group(3)), int(match.group(4))
        return datetime.date(year, month, day).isoformat()

    def _extract_requirements(self, markdown_content: str) -> List[Dict[str, Any]]:
        requirements: List[Dict[str, Any]] = []
        current_section = "自动识别章节"
        clause_counter = 1
        seen_descriptions: set[str] = set()

        for raw_line in markdown_content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                current_section = line.lstrip("#").strip()
                continue

            if not self._looks_like_requirement(line):
                continue
            if self._is_noise_requirement(line, current_section=current_section):
                continue
            normalized_description = self._normalize_requirement_text(line)
            if normalized_description in seen_descriptions:
                continue

            is_fatal = "★" in line or "必须" in line or "不得" in line
            category = "GENERAL"
            if any(keyword in line for keyword in ["资格", "资质", "证书", "执照", "社保", "信用中国"]):
                category = "QUALIFICATION"
            elif any(keyword in line for keyword in ["技术", "平台", "云", "接口", "兼容", "性能", "运维", "服务"]):
                category = "TECHNICAL"
            elif any(keyword in line for keyword in ["评分", "评审", "商务", "报价"]):
                category = "COMMERCIAL"

            score_match = re.search(r"(\d+(?:\.\d+)?)\s*分", line)
            evidence_required = "相关证明材料" if any(keyword in line for keyword in ["提供", "证明材料", "截图", "合同"]) else ""
            requirements.append(
                {
                    "original_section": current_section,
                    "clause_index": f"AUTO-{clause_counter}",
                    "category": category,
                    "description": normalized_description[:2000],
                    "is_fatal": is_fatal,
                    "max_score": float(score_match.group(1)) if score_match else 0.0,
                    "evidence_required": evidence_required,
                }
            )
            seen_descriptions.add(normalized_description)
            clause_counter += 1

        return requirements[:80]

    def _extract_scoring_items(self, markdown_content: str) -> List[Dict[str, Any]]:
        scoring_items: List[Dict[str, Any]] = []
        current_group = "评标办法"
        scoring_counter = 1
        in_scoring_region = False
        table_header_detected = False

        for raw_line in markdown_content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                current_group = line.lstrip("#").strip()
                if in_scoring_region and (current_group.startswith("六、") or current_group.startswith("第六章")):
                    break
                continue
            if "评分因素及分值范围" in line or "商务技术分" in line or "价格分" in line:
                in_scoring_region = True
                continue
            if not line.startswith("|"):
                continue
            if not in_scoring_region and "评分因素" not in line:
                continue

            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) < 4:
                continue
            joined_header = "|".join(cells[:4])
            if "评分因素" in joined_header and ("评分细则" in joined_header or "评分内容及细则" in joined_header):
                table_header_detected = True
                in_scoring_region = True
                continue
            if not table_header_detected:
                continue
            if any(keyword in cells[0] for keyword in ["---", "序号"]):
                continue
            if all(cell == "总分" for cell in cells[:3]):
                continue

            score_value = self._extract_score_from_cells(cells)
            if score_value is None:
                continue

            if "分" in cells[0] and len(set(cells[:4])) == 1:
                current_group = cells[0]
                continue

            item_name = cells[1] if len(cells) > 1 else cells[0]
            detail = cells[2] if len(cells) > 2 else ""
            description = f"{item_name}：{detail}".strip("：")
            if not description or description == item_name:
                continue

            scoring_items.append(
                {
                    "original_section": current_group or "评标办法",
                    "clause_index": f"SCORE-{scoring_counter}",
                    "category": "COMMERCIAL" if "商务" in current_group else "TECHNICAL",
                    "description": description[:2000],
                    "is_fatal": "不得分" in detail and any(keyword in detail for keyword in ["缺少", "不满足", "不提供"]),
                    "max_score": score_value,
                    "evidence_required": "相关证明材料" if any(keyword in detail for keyword in ["证明材料", "证书", "合同", "社保", "截图"]) else "",
                }
            )
            scoring_counter += 1

        return scoring_items

    def _extract_score_from_cells(self, cells: List[str]) -> float | None:
        for cell in reversed(cells):
            match = re.search(r"(\d+(?:\.\d+)?)", cell)
            if match:
                return float(match.group(1))
        return None

    async def _post_process_analysis(self, payload: Dict[str, Any], markdown_content: str) -> Dict[str, Any]:
        requirements = list(payload.get("requirements", []))
        scoring_items = self._extract_scoring_items(markdown_content)
        existing_descriptions = {item["description"] for item in requirements}
        for item in scoring_items:
            if item["description"] not in existing_descriptions:
                requirements.append(item)
        payload["requirements"] = requirements[:120]
        review_trace = await self._review_and_resolve(payload, markdown_content)
        if review_trace:
            payload["_review_trace"] = review_trace
        return payload

    def _post_process_analysis_sync(self, payload: Dict[str, Any], markdown_content: str) -> Dict[str, Any]:
        requirements = list(payload.get("requirements", []))
        scoring_items = self._extract_scoring_items(markdown_content)
        existing_descriptions = {item["description"] for item in requirements}
        for item in scoring_items:
            if item["description"] not in existing_descriptions:
                requirements.append(item)
        payload["requirements"] = requirements[:120]
        return payload

    async def _review_and_resolve(self, payload: Dict[str, Any], markdown_content: str) -> Dict[str, Any] | None:
        if not LLMClient.is_configured():
            return None

        review_input = self._build_review_input(payload, markdown_content)
        prompt = f"""
你是采购文件识别复核员。请检查第一轮抽取结果是否遗漏了项目元信息或章节覆盖判断。
你只做复核，不重写 requirements 明细。

输入 JSON:
{json.dumps(review_input, ensure_ascii=False)}

输出必须是 JSON 对象，格式如下:
{{
  "project_info": {{
    "name": "修正后的项目名称，若无需修正则返回原值",
    "budget": 预算数值，若未知返回 0,
    "deadline": "YYYY-MM-DD，若未知返回空字符串"
  }},
  "quality_flags": {{
    "has_scoring_section": true,
    "has_requirement_section": true,
    "has_qualification_section": true
  }},
  "notes": ["最多3条简短复核意见"]
}}
"""
        try:
            response = await asyncio.wait_for(self.ai.llm.ainvoke(prompt), timeout=12)
            review_payload = self._parse_review_response(response.content)
            resolved = self._apply_review_resolution(payload, review_payload)
            return {
                "mode": "llm_reviewed",
                "review": review_payload,
                "applied": resolved,
            }
        except Exception as exc:
            return {
                "mode": "review_skipped",
                "reason": str(exc),
            }

    def _build_review_input(self, payload: Dict[str, Any], markdown_content: str) -> Dict[str, Any]:
        headings = [line.lstrip("#").strip() for line in markdown_content.splitlines() if line.strip().startswith("#")]
        requirement_categories: Dict[str, int] = {}
        scoring_count = 0
        for req in payload.get("requirements", []):
            category = req.get("category", "GENERAL")
            requirement_categories[category] = requirement_categories.get(category, 0) + 1
            if (req.get("max_score") or 0) > 0:
                scoring_count += 1
        return {
            "project_info": payload.get("project_info", {}),
            "headings_preview": headings[:25],
            "requirements_total": len(payload.get("requirements", [])),
            "scoring_count": scoring_count,
            "category_distribution": requirement_categories,
        }

    def _parse_review_response(self, raw_content: str) -> Dict[str, Any]:
        clean_content = re.sub(r"```json\n?|```", "", raw_content).strip()
        try:
            data = json.loads(clean_content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", clean_content, re.DOTALL)
            if not match:
                raise
            data = json.loads(match.group(0))
        validated = RFPReviewSchema(**data)
        return validated.model_dump()

    def _apply_review_resolution(self, payload: Dict[str, Any], review_payload: Dict[str, Any]) -> Dict[str, bool]:
        applied = {
            "project_name": False,
            "budget": False,
            "deadline": False,
        }
        project_info = payload.get("project_info", {})
        reviewed_project = review_payload.get("project_info", {})

        if not project_info.get("name") and reviewed_project.get("name"):
            project_info["name"] = reviewed_project["name"]
            applied["project_name"] = True
        if not project_info.get("budget") and reviewed_project.get("budget"):
            project_info["budget"] = reviewed_project["budget"]
            applied["budget"] = True
        if not project_info.get("deadline") and reviewed_project.get("deadline"):
            project_info["deadline"] = reviewed_project["deadline"]
            applied["deadline"] = True
        payload["project_info"] = project_info
        return applied

    def _looks_like_requirement(self, line: str) -> bool:
        if len(line) < 8:
            return False
        keywords = ["要求", "应", "需", "必须", "提供", "评分", "得分", "证明", "投标人", "供应商", "支持", "具备"]
        return any(keyword in line for keyword in keywords)

    def _normalize_requirement_text(self, line: str) -> str:
        normalized = re.sub(r"^[（(]?[一二三四五六七八九十0-9]+[）).、.\s]+", "", line.strip())
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip("：:;；。 ")

    def _is_noise_requirement(self, line: str, current_section: str = "") -> bool:
        normalized = line.strip()
        if not normalized:
            return True
        if normalized.startswith("|"):
            return True
        if re.fullmatch(r"[一二三四五六七八九十0-9]+[、.)）]?", normalized):
            return True
        if re.fullmatch(r"(项目名称|项目编号|采购单位|采购内容|预算金额|最高限价|投标截止时间|开标时间)[：:]?", normalized):
            return True

        boilerplate_patterns = [
            "欢迎国内合格的供应商前来投标",
            "招标项目概况",
            "投标人购买标书时应提交的资料",
            "未按招标公告要求获取采购文件",
            "招标文件发售截止时间之后",
            "投标人认为招标文件使自己的权益受到损害",
            "具体要求详见招标文件",
            "各投标人须按国家有关标准及规范完成",
            "凡对本次招标提出询问",
            "以书面形式提出质疑",
            "采购代理机构",
            "获取招标文件",
            "购买采购文件",
            "报名时间",
            "报名地点",
            "联系方式",
            "联系人",
            "联系电话",
            "电子邮箱",
            "开户银行",
            "银行账号",
            "递交投标文件地点",
            "投标保证金",
            "公告期限",
        ]
        if any(pattern in normalized for pattern in boilerplate_patterns):
            return True

        if normalized.endswith("：") and len(normalized) <= 20:
            return True

        if re.search(r"(联系人|联系电话|邮箱|地址|邮编|传真)[：:]", normalized):
            return True
        if re.search(r"(北京时间|工作日|法定节假日|上午|下午)", normalized) and any(
            keyword in normalized for keyword in ["获取", "购买", "报名", "递交", "提交"]
        ):
            return True
        if re.search(r"\d{4}年\d{1,2}月\d{1,2}日", normalized) and any(
            keyword in normalized for keyword in ["报名", "发售", "获取", "购买", "质疑"]
        ):
            return True
        if current_section and any(keyword in current_section for keyword in ["项目建设背景", "项目概况", "采购背景", "建设现状"]):
            hard_requirement_keywords = ["要求", "应", "需", "必须", "支持", "具备", "不得", "满足"]
            narrative_prefixes = ["目前", "现状", "背景", "根据", "为", "本项目", "公司", "系统"]
            if not any(keyword in normalized for keyword in hard_requirement_keywords):
                return True
            if any(normalized.startswith(prefix) for prefix in narrative_prefixes) and "要求" not in normalized:
                return True

        if "详见需求" in normalized and len(normalized) <= 40:
            return True

        return False
