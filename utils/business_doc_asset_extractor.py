import re
from typing import Any


class BusinessDocAssetExtractor:
    def extract(self, markdown: str, images: list[str] | None = None) -> dict[str, Any]:
        sections = self._split_sections(markdown)
        return {
            "sections": sections,
            "certificates": self._extract_certificates(sections),
            "cases": self._extract_cases(sections),
            "personnel": self._extract_personnel(sections),
            "authorizations": self._extract_authorizations(sections),
            "social_security": self._extract_social_security(sections),
            "images": images or [],
        }

    def _split_sections(self, markdown: str) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        current_title = "ROOT"
        current_level = 0
        current_lines: list[str] = []

        for raw_line in markdown.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                sections.append(
                    {
                        "title": current_title,
                        "level": current_level,
                        "content": "\n".join(current_lines),
                    }
                )
                current_level = len(line) - len(line.lstrip("#"))
                current_title = line.lstrip("#").strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_title != "ROOT" or current_lines:
            sections.append(
                {
                    "title": current_title,
                    "level": current_level,
                    "content": "\n".join(current_lines),
                }
            )
        return sections

    def _extract_certificates(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        seen_keys: set[str] = set()
        for section in sections:
            title = section["title"]
            content = section["content"]
            merged = f"{title}\n{content}"
            if not self._looks_like_certificate_section(title, content):
                continue
            cert_name = self._normalize_certificate_name(title)
            signature = self._normalize_signature(cert_name or title)
            if signature in seen_keys:
                continue
            seen_keys.add(signature)
            results.append(
                {
                    "title": title,
                    "cert_name": cert_name,
                    "cert_type": self._infer_certificate_type(title, content),
                    "cert_level": self._infer_certificate_level(title, content),
                    "scope": self._extract_scope(content),
                    "issue_date": self._extract_date(content, "issue"),
                    "expiry_date": self._extract_date(content, "expiry"),
                    "evidence_text_preview": content[:300],
                    "image_paths": self._extract_image_paths(content),
                }
            )
        return results

    def _extract_personnel(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        seen_keys: set[str] = set()
        for section in sections:
            title = section["title"]
            content = section["content"]
            merged = f"{title}\n{content}"
            if not re.search(r"项目负责人|团队人员|简历|工程师|人员资质|售前|运维|负责人", merged):
                continue
            if self._is_noise_personnel_section(title, content):
                continue

            extracted_people = self._extract_personnel_entries(title, content)
            for person in extracted_people:
                signature = self._normalize_signature(f"{person['name']}|{person['role']}")
                if signature in seen_keys:
                    continue
                seen_keys.add(signature)
                results.append(person)
        return results

    def _extract_cases(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for section in sections:
            title = section["title"]
            content = section["content"]
            merged = f"{title}\n{content}"
            if not re.search(r"业绩|案例|项目合同|验收材料|项目负责人证明书", merged):
                continue

            seen_names: set[str] = set()
            numbered_projects = re.findall(r"(?:^|\n)\d+、([^\n]+项目[^\n]*)", content)
            if not numbered_projects:
                numbered_projects = re.findall(r"与([^\n]{4,80}?项目[^\n]{0,40})签订", content)

            for project_name in numbered_projects:
                normalized_name = project_name.strip("：:，,。；;（）() ")
                if not normalized_name or normalized_name in seen_names:
                    continue
                seen_names.add(normalized_name)
                results.append(
                    {
                        "title": title,
                        "project_name": normalized_name,
                        "industry": self._infer_case_industry(normalized_name, content),
                        "description": content[:500],
                        "compliance_keywords": self._infer_case_keywords(normalized_name, content),
                    }
                )

        return results

    def _extract_authorizations(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for section in sections:
            title = section["title"]
            content = section["content"]
            merged = f"{title}\n{content}"
            if not re.search(r"法定代表人|授权|委托书", merged):
                continue
            phone_match = re.search(r"1\d{10}", content)
            results.append(
                {
                    "title": title,
                    "authorized_person": self._extract_authorized_person(content),
                    "phone": phone_match.group(0) if phone_match else None,
                    "content_preview": content[:300],
                }
            )
        return results

    def _extract_social_security(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for section in sections:
            title = section["title"]
            content = section["content"]
            if "社保" not in title and "社保" not in content:
                continue
            results.append(
                {
                    "title": title,
                    "content_preview": content[:300],
                    "image_paths": self._extract_image_paths(content),
                }
            )
        return results

    def _normalize_certificate_name(self, title: str) -> str:
        normalized = re.sub(r"^\d+(?:\.\d+)*", "", title).strip()
        return normalized or title

    def _normalize_signature(self, value: str) -> str:
        normalized = re.sub(r"[\s\-—_:/：|]+", "", value or "")
        return normalized.lower()

    def _looks_like_certificate_section(self, title: str, content: str) -> bool:
        merged = f"{title}\n{content}"
        allow_keywords = ["营业执照", "证书", "认证", "资质", "互认证明", "可信云", "体系"]
        deny_keywords = [
            "偏离表",
            "方案设计",
            "建设目标",
            "逻辑架构",
            "功能模块",
            "机房配置",
            "高级功能",
            "开放性",
            "计算虚拟化",
            "相关业绩表",
        ]
        if any(keyword in merged for keyword in deny_keywords):
            return False
        if not any(keyword in merged for keyword in allow_keywords):
            return False
        return any(keyword in title for keyword in ["营业执照", "证书", "认证", "资质", "互认证明"])

    def _infer_certificate_type(self, title: str, content: str) -> str:
        merged = f"{title}\n{content}"
        if "营业执照" in merged:
            return "营业执照"
        if "ISO" in merged.upper():
            return "ISO体系认证"
        if "可信云" in merged:
            return "平台认证"
        if "资质" in merged:
            return "企业资质"
        return "证书材料"

    def _extract_scope(self, content: str) -> str:
        for line in content.splitlines():
            if any(keyword in line for keyword in ["适用范围", "覆盖范围", "项目内容", "服务范围"]):
                return line[:200]
        return content[:200]

    def _infer_certificate_level(self, title: str, content: str) -> str:
        merged = f"{title}\n{content}"
        for keyword in ["先进级", "甲级", "乙级", "一级", "二级", "三级", "高级"]:
            if keyword in merged:
                return keyword
        return ""

    def _extract_date(self, content: str, mode: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if mode == "expiry":
            priority_keywords = ["有效期至", "有效期", "截止日期", "到期"]
        else:
            priority_keywords = ["发证日期", "颁发日期", "批准日期", "签发日期", "初次发证"]

        for line in lines:
            if not any(keyword in line for keyword in priority_keywords):
                continue
            matched = self._find_date_in_text(line)
            if matched:
                return matched

        for line in lines[:8]:
            matched = self._find_date_in_text(line)
            if matched:
                return matched
        return ""

    def _find_date_in_text(self, text: str) -> str:
        match = re.search(r"(20\d{2})[年./-](\d{1,2})[月./-](\d{1,2})", text)
        if not match:
            return ""
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    def _infer_personnel_role(self, title: str, content: str) -> str:
        merged = f"{title}\n{content}"
        for keyword in ["项目负责人", "项目经理", "架构师", "工程师", "信息安全专员", "售前"]:
            if keyword in merged:
                return keyword
        return "人员材料"

    def _extract_personnel_entries(self, title: str, content: str) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        role = self._infer_personnel_role(title, content)

        inline_matches = re.findall(
            r"([\u4e00-\u9fa5]\s*[\u4e00-\u9fa5]{1,2})--([^-\n]{1,20})--([^\n]{1,40})",
            content,
        )
        for name, inline_role, _credential in inline_matches:
            normalized_name = self._normalize_person_name(name)
            if not self._looks_like_person_name(normalized_name):
                continue
            entries.append(
                {
                    "title": title,
                    "name": normalized_name,
                    "role": inline_role.strip() or role,
                    "content_preview": content[:300],
                }
            )

        listed_names = re.findall(
            r"(?:^|\n)\d+[、.]\s*([\u4e00-\u9fa5]{2,4})(?:简历|同志|--|简历及技术资质证书|资质证书)",
            content,
        )
        for listed_name in listed_names:
            normalized_name = self._normalize_person_name(listed_name)
            if not self._looks_like_person_name(normalized_name):
                continue
            entries.append(
                {
                    "title": title,
                    "name": normalized_name,
                    "role": role,
                    "content_preview": content[:300],
                }
            )

        field_patterns = [
            r"授权代表姓名[：:\s]+([\u4e00-\u9fa5]{2,4})",
            r"姓名[：:\s]+([\u4e00-\u9fa5]{2,4})",
        ]
        for pattern in field_patterns:
            match = re.search(pattern, content)
            if match:
                normalized_name = self._normalize_person_name(match.group(1))
                if self._looks_like_person_name(normalized_name):
                    entries.append(
                        {
                            "title": title,
                            "name": normalized_name,
                            "role": role,
                            "content_preview": content[:300],
                        }
                    )

        if entries:
            return entries

        name_match = re.search(r"([张王李赵刘陈杨黄周吴徐孙朱马胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董潘袁于余叶蒋杜苏魏程吕丁沈任姚卢傅钟姜崔谭廖范汪陆金石戴贾韦夏邱方侯邹熊孟秦白江阎薛尹段雷黎史龙陶贺顾毛郝龚邵万钱严赖覃洪武莫孔向汤])[\u4e00-\u9fa5]{1,2}", title)
        if name_match:
            normalized_name = self._normalize_person_name(name_match.group(0))
            if self._looks_like_person_name(normalized_name):
                return [
                    {
                        "title": title,
                        "name": normalized_name,
                        "role": role,
                        "content_preview": content[:300],
                    }
                ]
        return []

    def _normalize_person_name(self, value: str) -> str:
        return re.sub(r"\s+", "", (value or "").strip())

    def _looks_like_person_name(self, value: str) -> bool:
        if not value:
            return False
        if not re.fullmatch(r"[\u4e00-\u9fa5]{2,4}", value):
            return False
        deny_names = {"商务技术文件", "项目负责人", "项目团队", "人员资质", "实施团队", "服务承诺"}
        return value not in deny_names

    def _is_noise_personnel_section(self, title: str, content: str) -> bool:
        merged = f"{title}\n{content}"
        deny_keywords = [
            "物理机页面",
            "云主机页面",
            "路由器页面",
            "虚拟IP页面",
            "三层网络页面",
            "建设目标",
            "项目建设目标",
            "逻辑架构",
            "运维管理",
            "产品功能场景",
            "培训目的",
            "培训对象",
            "消息中心",
            "资源编排",
            "高可用",
            "机房配置",
            "知识库管理",
            "工单管理",
            "变更管理",
        ]
        return any(keyword in merged for keyword in deny_keywords)

    def _extract_authorized_person(self, content: str) -> str | None:
        match = re.search(r"授权代表姓名[：:\s]+([\u4e00-\u9fa5]{2,4})", content)
        return match.group(1) if match else None

    def _extract_image_paths(self, content: str) -> list[str]:
        return re.findall(r"\[IMAGE:([^\]]+)\]", content)

    def _infer_case_industry(self, project_name: str, content: str) -> str:
        merged = f"{project_name}\n{content}"
        if any(keyword in merged for keyword in ["国资", "政务", "气象"]):
            return "政企"
        if any(keyword in merged for keyword in ["教育", "产教"]):
            return "教育"
        if "钢铁" in merged:
            return "工业"
        return "综合"

    def _infer_case_keywords(self, project_name: str, content: str) -> str:
        merged = f"{project_name}\n{content}"
        keywords = []
        for keyword in ["信创", "国资云", "私有云", "高性能计算", "混合云", "云平台", "项目经理"]:
            if keyword in merged:
                keywords.append(keyword)
        return ",".join(keywords) or "项目业绩"
