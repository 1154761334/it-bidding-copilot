from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import ZipFile
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import yaml

from .runtime import VaultLayout


DOCX_EXTENSIONS = {".docx"}
PDF_EXTENSIONS = {".pdf"}
TEXT_EXTENSIONS = {".txt", ".text"}
MARKDOWN_EXTENSIONS = {".md", ".markdown"}
SUPPORTED_EXTENSIONS = DOCX_EXTENSIONS | PDF_EXTENSIONS | TEXT_EXTENSIONS
SKIP_TOP_LEVEL_DIRS = {"attachments"}


@dataclass
class PreprocessResult:
    source_path: Path
    normalized_path: Path | None
    status: str
    source_type: str
    bid_doc_class: str
    allow_absorb: bool
    attachments: list[str]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "normalized_path": str(self.normalized_path) if self.normalized_path else None,
            "status": self.status,
            "source_type": self.source_type,
            "bid_doc_class": self.bid_doc_class,
            "allow_absorb": self.allow_absorb,
            "attachments": self.attachments,
            "error": self.error,
        }


class DocumentPreprocessor:
    """Normalize local documents into raw markdown notes OVP can ingest."""

    def __init__(self, vault_dir: Path, logger: Any | None = None):
        self.layout = VaultLayout.from_vault(vault_dir)
        self.vault_dir = self.layout.vault_dir
        self.raw_dir = self.layout.raw_dir
        self.attachments_dir = self.raw_dir / "attachments"
        self.logger = logger

    def preprocess_inbox(self, dry_run: bool = False) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)

        for source_path in self._iter_supported_files():
            result = self.preprocess_file(source_path, dry_run=dry_run)
            results.append(result.to_dict())

        return results

    def preprocess_file(self, source_path: Path, dry_run: bool = False) -> PreprocessResult:
        source_path = source_path.resolve()
        source_type = source_path.suffix.lower().lstrip(".")
        bid_doc_class = self.classify_document(source_path)
        allow_absorb = bid_doc_class != "current_tender"
        normalized_path = self._normalized_markdown_path(source_path)

        if source_path.suffix.lower() in MARKDOWN_EXTENSIONS:
            return PreprocessResult(
                source_path=source_path,
                normalized_path=source_path,
                status="already_markdown",
                source_type=source_type,
                bid_doc_class=bid_doc_class,
                allow_absorb=allow_absorb,
                attachments=[],
            )

        if dry_run:
            return PreprocessResult(
                source_path=source_path,
                normalized_path=normalized_path,
                status="dry_run",
                source_type=source_type,
                bid_doc_class=bid_doc_class,
                allow_absorb=allow_absorb,
                attachments=[],
            )

        try:
            if source_path.suffix.lower() in DOCX_EXTENSIONS:
                result = self._preprocess_docx(source_path, normalized_path, bid_doc_class, allow_absorb)
            elif source_path.suffix.lower() in PDF_EXTENSIONS:
                result = self._preprocess_pdf(source_path, normalized_path, bid_doc_class, allow_absorb)
            elif source_path.suffix.lower() in TEXT_EXTENSIONS:
                result = self._preprocess_text(source_path, normalized_path, bid_doc_class, allow_absorb)
            else:
                result = PreprocessResult(
                    source_path=source_path,
                    normalized_path=None,
                    status="unsupported",
                    source_type=source_type,
                    bid_doc_class=bid_doc_class,
                    allow_absorb=allow_absorb,
                    attachments=[],
                    error=f"unsupported_extension:{source_path.suffix.lower()}",
                )
        except Exception as exc:
            result = PreprocessResult(
                source_path=source_path,
                normalized_path=None,
                status="error",
                source_type=source_type,
                bid_doc_class=bid_doc_class,
                allow_absorb=allow_absorb,
                attachments=[],
                error=str(exc),
            )

        if self.logger:
            self.logger.log("document_preprocessed", result.to_dict())

        return result

    def _iter_supported_files(self) -> list[Path]:
        files: list[Path] = []
        for path in sorted(self.raw_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            relative = path.relative_to(self.raw_dir)
            if any(part.startswith(".") for part in relative.parts):
                continue
            if relative.parts and relative.parts[0] in SKIP_TOP_LEVEL_DIRS:
                continue
            files.append(path)
        return files

    def classify_document(self, source_path: Path) -> str:
        try:
            relative = source_path.relative_to(self.raw_dir)
            parts = [part.lower() for part in relative.parts]
        except ValueError:
            parts = [part.lower() for part in source_path.parts]

        if any(part in {"current-tender", "current-tenders", "tender"} for part in parts):
            return "current_tender"
        if any(part in {"historical-bid", "historical-bids", "historical", "history"} for part in parts):
            return "historical_bid"
        return "generic_source"

    def _normalized_markdown_path(self, source_path: Path) -> Path:
        relative = source_path.relative_to(self.raw_dir)
        stem = source_path.stem
        digest = sha1(str(relative).encode("utf-8")).hexdigest()[:8]
        prefix = self._source_date(source_path).strftime("%Y-%m-%d")
        return source_path.with_name(f"{prefix}_{stem}_{digest}.md")

    def _source_date(self, source_path: Path) -> datetime:
        if source_path.suffix.lower() in DOCX_EXTENSIONS:
            metadata = self._read_docx_metadata(source_path)
            for key in ("modified", "created"):
                value = metadata.get(key)
                if value:
                    parsed = self._parse_datetime(value)
                    if parsed is not None:
                        return parsed
        return datetime.fromtimestamp(source_path.stat().st_mtime)

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        normalized = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    def _preprocess_docx(
        self,
        source_path: Path,
        normalized_path: Path,
        bid_doc_class: str,
        allow_absorb: bool,
    ) -> PreprocessResult:
        metadata = self._read_docx_metadata(source_path)
        asset_dir = self._asset_dir_for(normalized_path)

        with TemporaryDirectory(prefix="ovp-docx-") as temp_dir:
            temp_root = Path(temp_dir)
            temp_media_dir = temp_root / "media"
            temp_markdown_path = temp_root / "source.md"
            self._run_pandoc(source_path, temp_media_dir, temp_markdown_path)
            body = temp_markdown_path.read_text(encoding="utf-8")
            attachments = self._copy_extracted_media(temp_media_dir, asset_dir)

        body = self._rewrite_local_asset_links(body, normalized_path, asset_dir)
        title = self._choose_title(source_path, body=body, explicit_title=metadata.get("title"))
        markdown = self._build_source_markdown(
            title=title,
            source_path=source_path,
            body=body,
            source_type="docx",
            bid_doc_class=bid_doc_class,
            allow_absorb=allow_absorb,
            metadata=metadata,
            attachments=attachments,
        )
        normalized_path.write_text(markdown, encoding="utf-8")
        self._write_sidecar(normalized_path, source_path, "docx", bid_doc_class, allow_absorb, attachments, metadata)
        return PreprocessResult(
            source_path=source_path,
            normalized_path=normalized_path,
            status="completed",
            source_type="docx",
            bid_doc_class=bid_doc_class,
            allow_absorb=allow_absorb,
            attachments=attachments,
        )

    def _preprocess_pdf(
        self,
        source_path: Path,
        normalized_path: Path,
        bid_doc_class: str,
        allow_absorb: bool,
    ) -> PreprocessResult:
        text = self._extract_pdf_text(source_path)
        if not text.strip():
            raise RuntimeError("pdf_text_extraction_failed")
        markdown = self._build_source_markdown(
            title=self._choose_title(source_path, body=text),
            source_path=source_path,
            body=text,
            source_type="pdf",
            bid_doc_class=bid_doc_class,
            allow_absorb=allow_absorb,
            metadata={},
            attachments=[],
        )
        normalized_path.write_text(markdown, encoding="utf-8")
        self._write_sidecar(normalized_path, source_path, "pdf", bid_doc_class, allow_absorb, [], {})
        return PreprocessResult(
            source_path=source_path,
            normalized_path=normalized_path,
            status="completed",
            source_type="pdf",
            bid_doc_class=bid_doc_class,
            allow_absorb=allow_absorb,
            attachments=[],
        )

    def _preprocess_text(
        self,
        source_path: Path,
        normalized_path: Path,
        bid_doc_class: str,
        allow_absorb: bool,
    ) -> PreprocessResult:
        text = source_path.read_text(encoding="utf-8")
        markdown = self._build_source_markdown(
            title=self._choose_title(source_path, body=text),
            source_path=source_path,
            body=text,
            source_type="text",
            bid_doc_class=bid_doc_class,
            allow_absorb=allow_absorb,
            metadata={},
            attachments=[],
        )
        normalized_path.write_text(markdown, encoding="utf-8")
        self._write_sidecar(normalized_path, source_path, "text", bid_doc_class, allow_absorb, [], {})
        return PreprocessResult(
            source_path=source_path,
            normalized_path=normalized_path,
            status="completed",
            source_type="text",
            bid_doc_class=bid_doc_class,
            allow_absorb=allow_absorb,
            attachments=[],
        )

    def _run_pandoc(self, source_path: Path, media_dir: Path, markdown_path: Path) -> None:
        media_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    "pandoc",
                    str(source_path),
                    "-t",
                    "gfm",
                    "--wrap=none",
                    f"--extract-media={media_dir}",
                    "-o",
                    str(markdown_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("pandoc_not_installed") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"pandoc_failed: {exc.stderr.strip() or exc.stdout.strip()}") from exc

    def _extract_pdf_text(self, source_path: Path) -> str:
        try:
            result = subprocess.run(
                ["pdftotext", str(source_path), "-"],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("pdftotext_not_installed") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"pdftotext_failed: {exc.stderr.strip() or exc.stdout.strip()}") from exc
        return result.stdout

    def _asset_dir_for(self, normalized_path: Path) -> Path:
        return self.attachments_dir / normalized_path.stem

    def _copy_extracted_media(self, temp_media_dir: Path, asset_dir: Path) -> list[str]:
        attachments: list[str] = []
        if not temp_media_dir.exists():
            return attachments
        if asset_dir.exists():
            shutil.rmtree(asset_dir)
        for path in sorted(temp_media_dir.rglob("*")):
            if path.is_dir():
                continue
            destination = asset_dir / path.relative_to(temp_media_dir)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            attachments.append(self._vault_relative(destination))
        return attachments

    def _rewrite_local_asset_links(self, markdown: str, normalized_path: Path, asset_dir: Path) -> str:
        if not asset_dir.exists():
            return markdown
        asset_root = self._vault_relative(asset_dir)

        def rewrite_target(raw_target: str) -> str:
            normalized = raw_target.strip().replace("\\", "/")
            if normalized.startswith(("http://", "https://", "data:", "/asset?", "50-Inbox/")):
                return normalized
            if normalized.startswith("media/"):
                return f"{asset_root}/{normalized}"
            if "/media/" in normalized:
                suffix = normalized.split("/media/", 1)[1]
                if suffix.startswith("media/"):
                    return f"{asset_root}/{suffix}"
                return f"{asset_root}/media/{suffix}"
            return normalized

        def replace_match(match: re.Match[str]) -> str:
            label = match.group(1)
            raw_target = match.group(2)
            rewritten = rewrite_target(raw_target)
            if rewritten == raw_target.strip():
                return match.group(0)
            return f"![{label}]({rewritten})"

        def replace_html_img(match: re.Match[str]) -> str:
            before = match.group(1) or ""
            raw_target = match.group(2)
            after = match.group(3) or ""
            rewritten = rewrite_target(raw_target)
            if rewritten == raw_target.strip():
                return match.group(0)
            attrs = f"{before} {after}"
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', attrs, flags=re.IGNORECASE)
            alt_text = alt_match.group(1) if alt_match else ""
            return f"![{alt_text}]({rewritten})"

        rewritten = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_match, markdown)
        rewritten = re.sub(r"<img\b([^>]*?)src=[\"']([^\"']+)[\"']([^>]*)>", replace_html_img, rewritten, flags=re.IGNORECASE)
        return rewritten

    def _build_source_markdown(
        self,
        *,
        title: str,
        source_path: Path,
        body: str,
        source_type: str,
        bid_doc_class: str,
        allow_absorb: bool,
        metadata: dict[str, Any],
        attachments: list[str],
    ) -> str:
        source_date = self._source_date(source_path).date().isoformat()
        frontmatter = {
            "title": title,
            "source": f"local-file://{self._vault_relative(source_path)}",
            "author": metadata.get("creator", "unknown"),
            "date": source_date,
            "type": "source_note",
            "tags": ["source-note", source_type, bid_doc_class],
            "status": "raw",
            "source_type": source_type,
            "bid_doc_class": bid_doc_class,
            "allow_absorb": allow_absorb,
            "original_path": self._vault_relative(source_path),
            "original_filename": source_path.name,
            "attachments_root": self._vault_relative(self._asset_dir_for(self._normalized_markdown_path(source_path))),
            "attachment_count": len(attachments),
            "preprocess_status": "completed",
        }

        lines = [
            "---",
            yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip(),
            "---",
            "",
            f"# {title}",
            "",
            "## Source Metadata",
            "",
            f"- source_type: `{source_type}`",
            f"- bid_doc_class: `{bid_doc_class}`",
            f"- allow_absorb: `{str(allow_absorb).lower()}`",
            f"- original_path: `{self._vault_relative(source_path)}`",
            f"- attachment_count: `{len(attachments)}`",
            "",
            "## Extracted Content",
            "",
            body.strip(),
        ]
        if attachments:
            attachment_preview = attachments[:20]
            lines.extend(
                [
                    "",
                    "## Extracted Attachments",
                    "",
                    f"- total_attachments: {len(attachments)}",
                ]
            )
            for attachment in attachment_preview:
                lines.append(f"- {attachment}")
            if len(attachments) > len(attachment_preview):
                lines.append(f"- ... and {len(attachments) - len(attachment_preview)} more")

        lines.append("")
        return "\n".join(lines)

    def _write_sidecar(
        self,
        normalized_path: Path,
        source_path: Path,
        source_type: str,
        bid_doc_class: str,
        allow_absorb: bool,
        attachments: list[str],
        metadata: dict[str, Any],
    ) -> None:
        sidecar_path = normalized_path.with_suffix(".preprocess.json")
        payload = {
            "source_path": self._vault_relative(source_path),
            "normalized_path": self._vault_relative(normalized_path),
            "source_type": source_type,
            "bid_doc_class": bid_doc_class,
            "allow_absorb": allow_absorb,
            "attachments": attachments,
            "metadata": metadata,
            "generated_at": datetime.now().isoformat(),
        }
        sidecar_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_docx_metadata(self, source_path: Path) -> dict[str, str]:
        metadata: dict[str, str] = {}
        namespace = {
            "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
        }
        with ZipFile(source_path) as archive:
            if "docProps/core.xml" not in archive.namelist():
                return metadata
            root = ET.fromstring(archive.read("docProps/core.xml"))
            title = root.findtext("dc:title", default="", namespaces=namespace)
            creator = root.findtext("dc:creator", default="", namespaces=namespace)
            created = root.findtext("dcterms:created", default="", namespaces=namespace)
            modified = root.findtext("dcterms:modified", default="", namespaces=namespace)
            if title:
                metadata["title"] = title.strip()
            if creator:
                metadata["creator"] = creator.strip()
            if created:
                metadata["created"] = created.strip()
            if modified:
                metadata["modified"] = modified.strip()
        return metadata

    @staticmethod
    def _sanitize_title_fragment(text: str) -> str:
        cleaned = re.sub(r"<[^>]+>", "", text)
        cleaned = re.sub(r"[*_`#>\[\]\(\)]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" :：-_")
        return cleaned.strip()

    @classmethod
    def _infer_title_from_body(cls, body: str) -> str:
        lines = [cls._sanitize_title_fragment(line) for line in body.splitlines()]
        lines = [line for line in lines if line]

        for line in lines[:40]:
            match = re.search(r"项目名称[:：]\s*(.+)", line)
            if match:
                candidate = cls._sanitize_title_fragment(match.group(1))
                if candidate:
                    return candidate

        for index, line in enumerate(lines[:20]):
            if line == "招标文件":
                prefix: list[str] = []
                lookback = lines[max(0, index - 2):index]
                for candidate in lookback:
                    if candidate not in {"正本", "副本"}:
                        prefix.append(candidate)
                candidate_title = "".join(prefix + [line]).strip()
                if candidate_title:
                    return candidate_title

        for line in lines[:40]:
            if line in {"正本", "副本", "投标文件", "商务技术部分"}:
                continue
            if len(line) >= 4:
                return line
        return ""

    def _choose_title(self, source_path: Path, body: str = "", explicit_title: str | None = None) -> str:
        inferred = self._infer_title_from_body(body)
        if inferred:
            return inferred
        title = (explicit_title or "").strip()
        if title and title not in {"正本", "副本"}:
            return title
        return source_path.stem

    def _vault_relative(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.vault_dir.resolve()))
