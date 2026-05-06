from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


def test_document_preprocessor_writes_docx_source_note_with_asset_links(temp_vault, monkeypatch):
    from openclaw_pipeline.document_preprocessor import DocumentPreprocessor

    source_path = temp_vault / "50-Inbox" / "01-Raw" / "historical-bid" / "商务技术文件.docx"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(b"fake-docx")

    preprocessor = DocumentPreprocessor(temp_vault)

    monkeypatch.setattr(
        preprocessor,
        "_read_docx_metadata",
        lambda path: {
            "title": "私有云建设项目商务技术文件",
            "creator": "Test Author",
            "modified": "2023-12-08T01:26:33Z",
        },
    )

    def fake_run_pandoc(source_path, media_dir, markdown_path):
        media_file = media_dir / "media" / "image1.png"
        media_file.parent.mkdir(parents=True, exist_ok=True)
        media_file.write_bytes(b"png")
        markdown_path.write_text(
            "# 私有云建设项目商务技术文件\n\n正文段落。\n\n<img src=\"/tmp/fake/media/image1.png\" alt=\"示意图\" />\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(preprocessor, "_run_pandoc", fake_run_pandoc)

    result = preprocessor.preprocess_file(source_path)

    assert result.status == "completed"
    assert result.bid_doc_class == "historical_bid"
    assert result.allow_absorb is True
    assert result.normalized_path is not None

    normalized = result.normalized_path
    body = normalized.read_text(encoding="utf-8")
    assert "bid_doc_class: historical_bid" in body
    assert "allow_absorb: true" in body
    assert "50-Inbox/01-Raw/attachments/" in body
    assert "/tmp/fake/media" not in body

    sidecar = normalized.with_suffix(".preprocess.json")
    assert sidecar.exists()


def test_process_inbox_handles_nested_raw_markdown_and_archives_relative_path(temp_vault, monkeypatch):
    from openclaw_pipeline.auto_article_processor import AutoArticleProcessor, PipelineLogger, TransactionManager

    raw_file = temp_vault / "50-Inbox" / "01-Raw" / "current-tender" / "2026-04-07_tender.md"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text(
        """---
title: "招标文件"
source: local-file://50-Inbox/01-Raw/current-tender/招标文件.docx
author: unknown
date: 2026-04-07
type: source_note
tags: [source-note]
status: raw
source_type: docx
bid_doc_class: current_tender
allow_absorb: false
---

## Extracted Content

这是足够长的正文。""" + ("内容" * 200),
        encoding="utf-8",
    )

    logger = PipelineLogger(temp_vault / "60-Logs" / "pipeline.jsonl")
    txn = TransactionManager(temp_vault / "60-Logs" / "transactions")
    processor = AutoArticleProcessor(temp_vault, logger, txn)
    processor.article_processor = SimpleNamespace(
        generate_interpretation=lambda **kwargs: (
            "---\ntitle: Test\nsource: x\nauthor: y\ndate: 2026-04-07\ntype: article\ntags: []\nstatus: draft\n---\n\n# ok",
            {"tokens": 1},
            "tools",
        )
    )

    monkeypatch.setattr(
        processor,
        "_prepare_interpretation_source",
        lambda file_data: ("Substantive source material " * 80, {"origin": "body"}),
    )
    monkeypatch.setattr(
        "openclaw_pipeline.image_downloader.ImageDownloader.process_file",
        lambda self, file_path, backup=True: [],
    )

    results = processor.process_inbox(dry_run=False, batch_size=1)

    processed_file = temp_vault / "50-Inbox" / "03-Processed" / "2026-04" / "current-tender" / raw_file.name
    processing_file = temp_vault / "50-Inbox" / "02-Processing" / "current-tender" / raw_file.name

    assert results["completed"] == 1
    assert not raw_file.exists()
    assert not processing_file.exists()
    assert processed_file.exists()


def test_auto_evergreen_extractor_skips_files_with_allow_absorb_false(temp_vault):
    from openclaw_pipeline.auto_evergreen_extractor import AutoEvergreenExtractor, PipelineLogger

    deep_dive = temp_vault / "20-Areas" / "AI-Research" / "Topics" / "2026-04" / "2026-04-07_招标文件_深度解读.md"
    deep_dive.parent.mkdir(parents=True, exist_ok=True)
    deep_dive.write_text(
        """---
title: 招标文件深度解读
type: article
date: 2026-04-07
allow_absorb: false
bid_doc_class: current_tender
---

# 招标文件深度解读

正文内容
""",
        encoding="utf-8",
    )

    logger = PipelineLogger(temp_vault / "60-Logs" / "pipeline.jsonl")
    extractor = AutoEvergreenExtractor(temp_vault, logger)

    result = extractor.process_file(deep_dive, dry_run=False)

    assert result["status"] == "skipped"
    assert result["skip_reason"] == "allow_absorb_false"
    assert result["concepts_extracted"] == 0
