import anyio
import datetime
import json
import os
import shutil
import logging
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from api.models.assets_v2 import (
    AssetChunk,
    Company,
    CompanyAsset,
    EnterpriseCase,
    EnterpriseCertificate,
    EnterprisePersonnel,
    SourceDocument,
)
from utils.asset_manager import AssetManager
from utils.asset_classifier import AssetClassifier
from utils.business_asset_llm_extractor import BusinessAssetLLMExtractor
from utils.business_doc_asset_extractor import BusinessDocAssetExtractor
from utils.docling_wrapper import DoclingWrapper
from utils.hybrid_retriever import HybridRetriever


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md", ".png", ".jpg", ".jpeg"}
VAULT_CATEGORY_HINTS = {
    "certificate": "CERTIFICATE",
    "cert": "CERTIFICATE",
    "资质": "CERTIFICATE",
    "证书": "CERTIFICATE",
    "qualification": "CERTIFICATE",
    "case": "CASE",
    "案例": "CASE",
    "project": "CASE",
    "resume": "PERSONNEL",
    "personnel": "PERSONNEL",
    "人员": "PERSONNEL",
    "简历": "PERSONNEL",
}


class EnterpriseIngestService:
    def __init__(self, db: Session):
        self.db = db
        self.classifier = AssetClassifier()
        self.retriever = HybridRetriever(db)
        self.asset_manager = AssetManager(db)
        self.doc_parser = DoclingWrapper()
        self.business_doc_extractor = BusinessDocAssetExtractor()
        self.business_doc_llm_extractor: BusinessAssetLLMExtractor | None = None

    def ensure_company(self, company_id: int) -> Company:
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if company is None:
            raise ValueError("Company not found")
        return company

    async def ingest_upload_files(self, company_id: int, files: list[UploadFile], upload_dir: str) -> dict[str, Any]:
        self.ensure_company(company_id)
        os.makedirs(upload_dir, exist_ok=True)
        results = []

        for file in files:
            ext = os.path.splitext(file.filename or "")[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                results.append({"filename": file.filename, "status": "rejected", "reason": f"Unsupported extension: {ext}"})
                continue

            local_path = os.path.join(upload_dir, file.filename)
            with open(local_path, "wb") as f:
                f.write(await file.read())
            result = await self.ingest_local_file(company_id=company_id, local_path=local_path, display_name=file.filename)
            results.append(result)

        return {"status": "bulk processing finished", "results": results}

    async def ingest_vault_directory(self, company_id: int, vault_path: str, upload_dir: str) -> dict[str, Any]:
        self.ensure_company(company_id)
        vault_root = Path(vault_path).expanduser().resolve()
        if not vault_root.exists() or not vault_root.is_dir():
            raise ValueError("Vault path not found")

        vault_upload_dir = Path(upload_dir) / "obsidian_vault"
        vault_upload_dir.mkdir(parents=True, exist_ok=True)

        candidates = [
            path for path in sorted(vault_root.rglob("*"))
            if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
        ]
        results = []
        for file_path in candidates:
            relative_path = file_path.relative_to(vault_root)
            target_path = vault_upload_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if file_path.resolve() != target_path.resolve():
                shutil.copy2(file_path, target_path)
            inferred_type = self._infer_asset_type_from_path(file_path)
            result = await self.ingest_local_file(
                company_id=company_id,
                local_path=str(target_path),
                display_name=file_path.name,
                source_path=str(file_path),
                asset_type_hint=inferred_type,
            )
            result["vault_relative_path"] = str(relative_path)
            results.append(result)

        return {
            "status": "vault processing finished",
            "vault_path": str(vault_root),
            "files_total": len(candidates),
            "results": results,
        }

    async def ingest_local_file(
        self,
        *,
        company_id: int,
        local_path: str,
        display_name: str,
        source_path: str | None = None,
        asset_type_hint: str | None = None,
    ) -> dict[str, Any]:
        existing_doc = (
            self.db.query(SourceDocument)
            .filter(
                SourceDocument.company_id == company_id,
                SourceDocument.filename == display_name,
                SourceDocument.local_path == local_path,
            )
            .first()
        )
        if existing_doc is not None:
            return {
                "filename": display_name,
                "status": "skipped_existing",
                "asset_type": existing_doc.file_type,
                "chunks_count": len(existing_doc.chunks or []),
            }

        source_doc = SourceDocument(
            company_id=company_id,
            filename=display_name,
            file_type="AUTO",
            local_path=local_path,
            upload_date=datetime.date.today(),
        )
        self.db.add(source_doc)
        self.db.commit()
        self.db.refresh(source_doc)

        try:
            ingest_data = await self.classifier.auto_ingest(local_path)
            asset_type = asset_type_hint or ingest_data["type"]
            parse_data = ingest_data["data"]
            markdown_content = parse_data["markdown"]
            source_doc.file_type = asset_type

            asset = None
            if asset_type == "CASE":
                asset = EnterpriseCase(
                    company_id=company_id,
                    source_doc_id=source_doc.id,
                    project_name=f"提取自 {display_name}",
                    description=markdown_content[:2000],
                    compliance_keywords=self._build_compliance_keywords(source_path or local_path),
                    embedding=await anyio.to_thread.run_sync(self.retriever._get_embedding, markdown_content),
                )
            elif asset_type == "CERTIFICATE":
                asset = EnterpriseCertificate(
                    company_id=company_id,
                    source_doc_id=source_doc.id,
                    raw_name=display_name,
                    certification_scope=self._build_certification_scope(source_path or local_path),
                    embedding=await anyio.to_thread.run_sync(self.retriever._get_embedding, f"证书: {display_name}"),
                )
            elif asset_type == "PERSONNEL":
                asset = EnterprisePersonnel(
                    company_id=company_id,
                    name=Path(display_name).stem,
                    resume_text=markdown_content[:1000],
                    role=self._infer_personnel_role(markdown_content),
                    embedding=await anyio.to_thread.run_sync(self.retriever._get_embedding, markdown_content),
                )

            for chunk_data in ingest_data.get("chunks", []):
                self.db.add(
                    AssetChunk(
                        company_id=company_id,
                        source_doc_id=source_doc.id,
                        chunk_type=chunk_data["type"],
                        content=chunk_data["content"],
                        embedding=await anyio.to_thread.run_sync(self.retriever._get_embedding, chunk_data["content"]),
                    )
                )

            if asset is not None:
                self.db.add(asset)

            self.db.commit()
            return {
                "filename": display_name,
                "status": "ingested" if asset is not None else "source_only",
                "asset_type": asset_type,
                "chunks_count": len(ingest_data.get("chunks", [])),
            }
        except Exception as exc:
            self.db.rollback()
            return {"filename": display_name, "status": "partial_error", "reason": str(exc)}

    async def ingest_business_document(
        self,
        *,
        company_id: int,
        local_path: str,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        self.ensure_company(company_id)
        resolved_path = str(Path(local_path).expanduser().resolve())
        if not os.path.exists(resolved_path):
            raise ValueError("Business document not found")

        filename = display_name or os.path.basename(resolved_path)
        existing_doc = (
            self.db.query(SourceDocument)
            .filter(
                SourceDocument.company_id == company_id,
                SourceDocument.filename == filename,
                SourceDocument.local_path == resolved_path,
            )
            .first()
        )
        if existing_doc is not None:
            return self._build_existing_business_doc_summary(existing_doc)

        source_doc = SourceDocument(
            company_id=company_id,
            filename=filename,
            file_type="BUSINESS_DOC",
            local_path=resolved_path,
            upload_date=datetime.date.today(),
        )
        self.db.add(source_doc)
        self.db.flush()

        try:
            # Use improved classifier pipeline
            ingest_data = await self.classifier.auto_ingest(resolved_path)
            markdown_content = ingest_data["data"]["markdown"]
            
            # extracted = self.business_doc_extractor.extract(parse_result["markdown"], parse_result["images"])
            # Note: BusinessDocAssetExtractor needs update if we want to extract images properly from MinerU
            # For now, focus on markdown-based extraction
            extracted = self.business_doc_extractor.extract(markdown_content, [])
            llm_extractor = self._get_business_doc_llm_extractor()
            standardized = await llm_extractor.standardize(
                sections=extracted["sections"],
                fallback_assets={
                    "certificates": extracted["certificates"],
                    "cases": extracted["cases"],
                    "personnel": extracted["personnel"],
                    "authorizations": extracted["authorizations"],
                    "social_security": extracted["social_security"],
                },
            )
            structured_assets = {
                "sections": extracted["sections"],
                "images": extracted["images"],
                "certificates": standardized["assets"]["certificates"],
                "cases": standardized["assets"]["cases"],
                "personnel": standardized["assets"]["personnel"],
                "authorizations": standardized["assets"]["authorizations"],
                "social_security": standardized["assets"]["social_security"],
                "llm_trace": standardized["trace"],
            }
            structured_assets = self._sanitize_business_doc_assets(structured_assets)
            structured_assets = await self._persist_business_doc_assets(
                company_id=company_id,
                source_doc_id=source_doc.id,
                parse_result=ingest_data["data"],
                extracted=structured_assets,
            )
            self.db.commit()
            return {
                "filename": filename,
                "status": "ingested",
                "asset_type": "BUSINESS_DOC",
                "sections_total": len(extracted["sections"]),
                "chunks_count": structured_assets["chunks_count"],
                "images_registered": structured_assets["images_registered"],
                "certificates_created": structured_assets["certificates_created"],
                "cases_created": structured_assets["cases_created"],
                "personnel_created": structured_assets["personnel_created"],
                "text_assets_created": structured_assets["text_assets_created"],
                "llm_trace": structured_assets["llm_trace"],
            }
        except Exception as exc:
            self.db.rollback()
            return {"filename": filename, "status": "partial_error", "reason": str(exc)}

    def _infer_asset_type_from_path(self, file_path: Path) -> str | None:
        lowered_parts = " / ".join(part.lower() for part in file_path.parts)
        for key, asset_type in VAULT_CATEGORY_HINTS.items():
            if key in lowered_parts:
                return asset_type
        return None

    def _build_compliance_keywords(self, source_path: str) -> str:
        path = source_path.lower()
        tags = [key for key in VAULT_CATEGORY_HINTS if key in path]
        return ",".join(sorted(set(tags))) or "自动分类"

    def _build_certification_scope(self, source_path: str) -> str:
        scope = self._build_compliance_keywords(source_path)
        return f"来源于 Vault/文件夹标签: {scope}"

    def _infer_personnel_role(self, markdown: str) -> str | None:
        for keyword in ["项目经理", "架构师", "工程师", "售前", "运维"]:
            if keyword in markdown:
                return keyword
        return None

    async def _persist_business_doc_assets(
        self,
        *,
        company_id: int,
        source_doc_id: int,
        parse_result: dict[str, Any],
        extracted: dict[str, Any],
    ) -> dict[str, Any]:
        chunks_count = 0
        
        # 1. First, persist granular chunks from the raw parse result (Element-level storage)
        raw_parse = parse_result.get("raw", {})
        if isinstance(raw_parse, dict) and "content_list_file" in raw_parse:
            try:
                with open(raw_parse["content_list_file"], "r", encoding="utf-8") as f:
                    content_list = json.load(f)
                for item in content_list:
                    content = item.get("text") or item.get("text_content") or ""
                    if not content.strip():
                        continue
                    self.db.add(
                        AssetChunk(
                            company_id=company_id,
                            source_doc_id=source_doc_id,
                            chunk_type=item["type"],
                            content=content,
                            embedding=await anyio.to_thread.run_sync(self.retriever._get_embedding, content),
                        )
                    )
                    chunks_count += 1
            except Exception as e:
                logger.error(f"Error persisting MinerU elements: {e}")

        # 2. Then persist sections (Business-level retrieval units)
        for section in extracted["sections"]:
            section_text = "\n".join([section["title"], section["content"]]).strip()
            if not section_text:
                continue
            # If we already persisted this as a chunk, we might dedupe or keep for section-level retrieval
            self.db.add(
                AssetChunk(
                    company_id=company_id,
                    source_doc_id=source_doc_id,
                    chunk_type="section",
                    content=section_text[:4000],
                    embedding=await anyio.to_thread.run_sync(self.retriever._get_embedding, section_text),
                )
            )
            chunks_count += 1

        # Handle images
        images_registered = 0
        registered_image_map: dict[str, str] = {}
        
        # Determine image sources
        raw_parse = parse_result.get("raw", {})
        image_paths = []
        if isinstance(raw_parse, dict) and "image_dir" in raw_parse:
            # MinerU path
            img_dir = Path(raw_parse["image_dir"])
            if img_dir.exists():
                image_paths = [str(p) for p in img_dir.glob("*.png")]
        else:
            # Docling/Legacy path
            image_paths = parse_result.get("images", [])

        for image_path in image_paths:
            image_name = Path(image_path).name
            asset = self.asset_manager.register_asset(
                file_path=image_path,
                company_id=company_id,
                asset_name=f"资产图片-{image_name}",
                category="qualification",
                asset_tag="business_doc_image",
                metadata={
                    "source_doc_id": source_doc_id,
                    "original_filename": image_name,
                },
            )
            registered_image_map[image_path] = asset.local_path
            images_registered += 1

        certificates_created = 0
        for cert in extracted["certificates"]:
            if not self._should_persist_certificate(cert):
                continue
            self.db.add(
                EnterpriseCertificate(
                    company_id=company_id,
                    source_doc_id=source_doc_id,
                    cert_type=cert["cert_type"],
                    cert_level=(cert.get("cert_level") or None),
                    raw_name=cert["cert_name"][:255] or cert["title"][:255],
                    certification_scope=cert["scope"],
                    issue_date=self._parse_optional_iso_date(cert.get("issue_date")),
                    expiry_date=self._parse_optional_iso_date(cert.get("expiry_date")),
                    image_url=self._resolve_registered_image_path(cert.get("image_paths", []), registered_image_map),
                    embedding=await anyio.to_thread.run_sync(self.retriever._get_embedding, f"{cert['title']}\n{cert['evidence_text_preview']}"),
                )
            )
            certificates_created += 1

        cases_created = 0
        for case in extracted.get("cases", []):
            if not self._should_persist_case(case):
                continue
            self.db.add(
                EnterpriseCase(
                    company_id=company_id,
                    source_doc_id=source_doc_id,
                    project_name=case["project_name"][:255],
                    industry=(case.get("industry") or "综合")[:100],
                    description=case.get("description", "")[:2000],
                    compliance_keywords=case.get("compliance_keywords") or "项目业绩",
                    embedding=await anyio.to_thread.run_sync(self.retriever._get_embedding, f"{case['project_name']}\n{case.get('description', '')}"),
                )
            )
            cases_created += 1

        personnel_created = 0
        for person in extracted["personnel"]:
            if not self._should_persist_personnel(person):
                continue
            self.db.add(
                EnterprisePersonnel(
                    company_id=company_id,
                    name=(person["name"] or person["title"])[:100],
                    role=person["role"][:100],
                    level="待核验",
                    resume_text=person["content_preview"],
                    social_security_image_url=self._resolve_registered_image_path(
                        self._match_social_security_images(extracted.get("social_security", []), person["title"]),
                        registered_image_map,
                    ),
                    embedding=self.retriever._get_embedding(f"{person['title']}\n{person['content_preview']}"),
                )
            )
            personnel_created += 1

        text_assets_created = 0
        text_asset_specs = [
            ("authorization", "qualification", extracted["authorizations"]),
            ("social_security", "qualification", extracted["social_security"]),
        ]
        for asset_tag, category, items in text_asset_specs:
            for item in items:
                if not self._should_persist_text_asset(asset_tag, item):
                    continue
                self.db.add(
                    CompanyAsset(
                        id=self._build_company_asset_id(company_id, source_doc_id, asset_tag, item["title"]),
                        company_id=company_id,
                        asset_name=item["title"][:255],
                        asset_type="text",
                        category=category,
                        asset_tag=asset_tag,
                        local_path=None,
                        metadata_json=json.dumps(item, ensure_ascii=False),
                        upload_date=datetime.date.today(),
                    )
                )
                text_assets_created += 1

        return {
            "chunks_count": chunks_count,
            "images_registered": images_registered,
            "certificates_created": certificates_created,
            "cases_created": cases_created,
            "personnel_created": personnel_created,
            "text_assets_created": text_assets_created,
            "llm_trace": extracted.get("llm_trace", {}),
        }

    def _build_existing_business_doc_summary(self, source_doc: SourceDocument) -> dict[str, Any]:
        chunks_count = (
            self.db.query(AssetChunk)
            .filter(AssetChunk.source_doc_id == source_doc.id)
            .count()
        )
        certificates_created = (
            self.db.query(EnterpriseCertificate)
            .filter(EnterpriseCertificate.source_doc_id == source_doc.id)
            .count()
        )
        cases_created = (
            self.db.query(EnterpriseCase)
            .filter(EnterpriseCase.source_doc_id == source_doc.id)
            .count()
        )
        images_registered = (
            self.db.query(CompanyAsset)
            .filter(
                CompanyAsset.company_id == source_doc.company_id,
                CompanyAsset.asset_tag == "business_doc_image",
                CompanyAsset.metadata_json.contains(f'"source_doc_id": {source_doc.id}'),
            )
            .count()
        )
        text_assets_created = (
            self.db.query(CompanyAsset)
            .filter(
                CompanyAsset.company_id == source_doc.company_id,
                CompanyAsset.asset_type == "text",
                CompanyAsset.metadata_json.contains(source_doc.filename),
            )
            .count()
        )
        return {
            "filename": source_doc.filename,
            "status": "skipped_existing",
            "asset_type": source_doc.file_type,
            "chunks_count": chunks_count,
            "certificates_created": certificates_created,
            "cases_created": cases_created,
            "images_registered": images_registered,
            "text_assets_created": text_assets_created,
        }

    def _parse_optional_iso_date(self, value: str | None) -> datetime.date | None:
        if not value:
            return None
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            return None

    def _build_company_asset_id(self, company_id: int, source_doc_id: int, asset_tag: str, title: str) -> str:
        seed = f"{company_id}-{source_doc_id}-{asset_tag}-{title}"
        compact = "".join(ch for ch in seed if ch.isalnum()).lower()
        return compact[:50]

    def _resolve_registered_image_path(self, image_paths: list[str], registered_image_map: dict[str, str]) -> str | None:
        if not image_paths:
            return None
        for image_path in image_paths:
            if image_path in registered_image_map:
                return registered_image_map[image_path]
        return None

    def _get_business_doc_llm_extractor(self) -> BusinessAssetLLMExtractor:
        if self.business_doc_llm_extractor is None:
            self.business_doc_llm_extractor = BusinessAssetLLMExtractor()
        return self.business_doc_llm_extractor

    def _sanitize_business_doc_assets(self, extracted: dict[str, Any]) -> dict[str, Any]:
        extracted["certificates"] = self._dedupe_assets(
            [item for item in extracted.get("certificates", []) if self._should_persist_certificate(item)],
            lambda item: self._normalize_asset_signature(item.get("cert_name") or item.get("title") or ""),
        )
        extracted["cases"] = self._dedupe_assets(
            [item for item in extracted.get("cases", []) if self._should_persist_case(item)],
            lambda item: self._normalize_asset_signature(item.get("project_name") or item.get("title") or ""),
        )
        extracted["personnel"] = self._dedupe_assets(
            [
                item for item in extracted.get("personnel", [])
                if self._should_persist_personnel(item) and self._looks_like_person_name(item.get("name", ""))
            ],
            lambda item: self._normalize_asset_signature(f"{item.get('name', '')}|{item.get('role', '')}"),
        )
        extracted["authorizations"] = self._dedupe_assets(
            [item for item in extracted.get("authorizations", []) if self._should_persist_text_asset("authorization", item)],
            lambda item: self._normalize_asset_signature(item.get("title") or ""),
        )
        extracted["social_security"] = self._dedupe_assets(
            [item for item in extracted.get("social_security", []) if self._should_persist_text_asset("social_security", item)],
            lambda item: self._normalize_asset_signature(item.get("title") or ""),
        )
        return extracted

    def _dedupe_assets(self, items: list[dict[str, Any]], signature_builder) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in items:
            signature = signature_builder(item)
            if not signature or signature in seen:
                continue
            seen.add(signature)
            deduped.append(item)
        return deduped

    def _normalize_asset_signature(self, value: str) -> str:
        compact = "".join(ch for ch in (value or "") if ch.isalnum())
        return compact.lower()

    def _looks_like_person_name(self, value: str) -> bool:
        if not value:
            return False
        compact = "".join(ch for ch in value if not ch.isspace())
        if not (2 <= len(compact) <= 4):
            return False
        return compact.isalpha() and all("\u4e00" <= ch <= "\u9fff" for ch in compact)

    def _should_persist_certificate(self, cert: dict[str, Any]) -> bool:
        merged = f"{cert['title']}\n{cert['evidence_text_preview']}"
        allow_keywords = [
            "营业执照",
            "资质证书",
            "体系证书",
            "认证证书",
            "项目负责人证书",
            "人员资质证书",
            "互认证明",
            "证书",
        ]
        deny_keywords = [
            "偏离表",
            "方案设计",
            "建设目标",
            "逻辑架构",
            "相关证明材料",
            "私有云平台证明材料",
            "开放性",
            "计算虚拟化",
            "功能模块",
            "机房配置",
            "高级功能",
            "评审因素对应表",
            "业绩表",
        ]
        title = cert.get("title", "")
        cert_name = cert.get("cert_name", "")
        title_has_cert_signal = any(keyword in title for keyword in ["证书", "执照", "认证", "资质", "互认证明"])
        name_has_cert_signal = any(keyword in cert_name for keyword in ["证书", "执照", "认证", "资质", "互认证明"])
        return (
            any(keyword in merged for keyword in allow_keywords)
            and not any(keyword in merged for keyword in deny_keywords)
            and (title_has_cert_signal or name_has_cert_signal)
        )

    def _should_persist_personnel(self, person: dict[str, Any]) -> bool:
        merged = f"{person['title']}\n{person['content_preview']}"
        title = person.get("title", "")
        allow_keywords = ["项目负责人", "团队人员", "简历", "工程师", "社保", "人员资质证书", "实施团队", "授权代表"]
        deny_keywords = [
            "建设目标",
            "机房配置",
            "逻辑架构",
            "方案设计",
            "运维复杂度",
            "技术支持",
            "培训目的",
            "物理机页面",
            "云主机页面",
            "路由器页面",
            "虚拟IP页面",
            "三层网络页面",
            "产品功能场景",
            "资源编排",
            "消息中心",
            "知识库管理",
            "工单管理",
            "变更管理",
        ]
        return (
            any(keyword in merged for keyword in allow_keywords)
            and not any(keyword in merged for keyword in deny_keywords)
            and any(keyword in title for keyword in ["项目负责人", "团队人员", "简历", "人员", "实施团队", "社保", "资质证书"])
        )

    def _should_persist_case(self, case: dict[str, Any]) -> bool:
        merged = f"{case['title']}\n{case.get('project_name', '')}\n{case.get('description', '')}"
        allow_keywords = ["业绩", "案例", "项目合同", "验收材料", "项目负责人证明书", "云平台", "国资云", "混合云"]
        deny_keywords = ["当前项目", "本项目采购", "建设目标", "方案设计", "解决方案"]
        project_name = case.get("project_name", "").strip()
        return (
            len(project_name) >= 6
            and any(keyword in merged for keyword in allow_keywords)
            and not any(keyword in merged for keyword in deny_keywords)
        )

    def _should_persist_text_asset(self, asset_tag: str, item: dict[str, Any]) -> bool:
        merged = f"{item['title']}\n{item.get('content_preview', '')}"
        if asset_tag == "authorization":
            return any(keyword in merged for keyword in ["授权", "委托书", "法定代表人"]) and "混合云功能模块" not in merged
        if asset_tag == "social_security":
            return "社保" in merged and "授权" not in merged and "委托书" not in merged
        return True

    def _match_social_security_images(self, social_security_items: list[dict[str, Any]], person_title: str) -> list[str]:
        for item in social_security_items:
            if person_title.startswith("项目负责人") and "项目负责人" in item.get("title", ""):
                return item.get("image_paths", [])
            if any(keyword in person_title for keyword in ["团队人员", "实施团队"]) and any(
                keyword in item.get("title", "") for keyword in ["团队人员", "实施团队"]
            ):
                return item.get("image_paths", [])
        return []
