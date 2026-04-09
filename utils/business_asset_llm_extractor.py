import json
import re
from typing import Any

from pydantic import BaseModel, Field

from api.core.llm_client import LLMClient


class CertificateAsset(BaseModel):
    title: str
    cert_name: str
    cert_type: str
    cert_level: str = ""
    scope: str = ""
    issue_date: str = ""
    expiry_date: str = ""
    evidence_text_preview: str = ""
    image_paths: list[str] = Field(default_factory=list)


class PersonnelAsset(BaseModel):
    title: str
    name: str
    role: str
    content_preview: str = ""


class AuthorizationAsset(BaseModel):
    title: str
    authorized_person: str | None = None
    phone: str | None = None
    content_preview: str = ""


class SocialSecurityAsset(BaseModel):
    title: str
    content_preview: str = ""
    image_paths: list[str] = Field(default_factory=list)


class CaseAsset(BaseModel):
    title: str
    project_name: str
    industry: str = ""
    description: str = ""
    compliance_keywords: str | list[str] = ""


class BusinessAssetExtractionPayload(BaseModel):
    certificates: list[CertificateAsset] = Field(default_factory=list)
    cases: list[CaseAsset] = Field(default_factory=list)
    personnel: list[PersonnelAsset] = Field(default_factory=list)
    authorizations: list[AuthorizationAsset] = Field(default_factory=list)
    social_security: list[SocialSecurityAsset] = Field(default_factory=list)


class BusinessAssetLLMExtractor:
    def __init__(self) -> None:
        self.ai = LLMClient(role="ANALYSIS")

    async def standardize(
        self,
        *,
        sections: list[dict[str, Any]],
        fallback_assets: dict[str, Any],
    ) -> dict[str, Any]:
        if not LLMClient.is_configured():
            return {
                "assets": fallback_assets,
                "trace": {
                    "mode": "fallback",
                    "reason": "llm_not_configured",
                    "sections_submitted": 0,
                },
            }

        candidate_sections = self._select_candidate_sections(sections)
        if not candidate_sections:
            return {
                "assets": fallback_assets,
                "trace": {
                    "mode": "fallback",
                    "reason": "no_candidate_sections",
                    "sections_submitted": 0,
                },
            }

        prompt = self._build_prompt(candidate_sections)
        try:
            response = await self.ai.llm.ainvoke(prompt)
            payload = self._parse_response(response.content)
            return {
                "assets": payload,
                "trace": {
                    "mode": "llm_standardized",
                    "reason": None,
                    "sections_submitted": len(candidate_sections),
                },
            }
        except Exception as exc:
            return {
                "assets": fallback_assets,
                "trace": {
                    "mode": "fallback",
                    "reason": str(exc),
                    "sections_submitted": len(candidate_sections),
                },
            }

    def _select_candidate_sections(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ranked: list[tuple[int, dict[str, Any]]] = []
        allow_pattern = re.compile(r"证书|执照|资质|授权|委托书|社保|负责人|简历|人员", re.I)
        for section in sections:
            merged = f"{section['title']}\n{section['content']}"
            if not allow_pattern.search(merged):
                continue
            score = self._score_section(section["title"], section["content"])
            ranked.append(
                (
                    score,
                    {
                        "title": section["title"][:200],
                        "content": section["content"][:1500],
                    },
                )
            )
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [section for _score, section in ranked[:60]]

    def _score_section(self, title: str, content: str) -> int:
        merged = f"{title}\n{content}"
        score = 0
        weight_map = {
            "营业执照": 20,
            "资质证书": 20,
            "体系证书": 18,
            "认证证书": 18,
            "社保证明": 18,
            "项目负责人": 16,
            "团队人员": 16,
            "人员资质": 16,
            "简历": 16,
            "授权": 14,
            "委托书": 14,
            "证书": 12,
            "资质": 12,
            "人员": 10,
            "社保": 10,
        }
        for keyword, weight in weight_map.items():
            if keyword in merged:
                score += weight
        if title:
            score += 5
        if len(content) < 40:
            score += 2
        deny_keywords = ["建设目标", "方案设计", "逻辑架构", "功能模块", "配置", "复杂度"]
        if any(keyword in merged for keyword in deny_keywords):
            score -= 20
        return score

    def _build_prompt(self, sections: list[dict[str, Any]]) -> str:
        return (
            "你是投标资料治理助手。请从下面的商务技术文件章节中，提取可沉淀为企业资质库的结构化信息。"
            "只提取明确出现的信息，不要猜测，不要补全。"
            "输出必须是 JSON 对象，包含 certificates、cases、personnel、authorizations、social_security 五个数组。\n"
            "字段要求：\n"
            "certificates: [{title, cert_name, cert_type, cert_level, scope, issue_date, expiry_date, evidence_text_preview, image_paths}]\n"
            "cases: [{title, project_name, industry, description, compliance_keywords}]\n"
            "personnel: [{title, name, role, content_preview}]\n"
            "authorizations: [{title, authorized_person, phone, content_preview}]\n"
            "social_security: [{title, content_preview, image_paths}]\n"
            "过滤要求：\n"
            "1. 不要把建设目标、方案说明、产品功能说明误判成证书或人员。\n"
            "2. 标题即使没有正文，只要明显是资质/证书/社保/授权章节，也可以输出。\n"
            "3. 人员条目优先保留项目负责人、项目团队、简历、人员资质。\n"
            "4. phone 仅保留 11 位手机号；身份证号不要输出到 phone。\n"
            "5. cases 只保留明确出现的历史项目业绩、案例、项目合同或验收证明，不要把当前投标项目本身当成历史案例。\n"
            "以下是候选章节 JSON：\n"
            f"{json.dumps(sections, ensure_ascii=False)}"
        )

    def _parse_response(self, raw_content: str) -> dict[str, Any]:
        clean_content = re.sub(r"```json\n?|```", "", raw_content).strip()
        try:
            payload = json.loads(clean_content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", clean_content, re.DOTALL)
            if not match:
                raise
            payload = json.loads(match.group(0))
        for case in payload.get("cases", []):
            if isinstance(case.get("compliance_keywords"), list):
                case["compliance_keywords"] = ",".join(str(item) for item in case["compliance_keywords"] if item)
        validated = BusinessAssetExtractionPayload(**payload)
        return validated.model_dump()
