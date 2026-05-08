"""
One-time ingestion script to import vault materials into the Evidence Store.
Parses the already-converted Markdown files, splits them into structured chunks,
extracts image references, classifies each chunk, and stores with embeddings.

Usage:
    cd backend
    source venv/bin/activate
    python -m src.ingest
"""
import os
import re
import sys
import json
from typing import Optional

# Ensure the parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.config import repo_path, settings
from src.database import engine, Base, SessionLocal
from src.models import EvidenceItem

# We'll try to use embeddings, but make it optional for the initial import
ENABLE_EMBEDDINGS = True
try:
    from src.evidence import get_embedding
except Exception as e:
    print(f"Warning: Could not load embedding function: {e}")
    ENABLE_EMBEDDINGS = False


# ---------------------------------------------------------------------------
# Section classification rules
# ---------------------------------------------------------------------------
SECTION_RULES = [
    # (pattern in heading path, category, sub_type)
    (r"法定代表人资格证明", "company_credential", "legal_representative"),
    (r"法定代表人授权", "company_credential", "authorization"),
    (r"偏离表", "bid_section", "deviation_table"),
    (r"证明材料.*私有云平台", "vendor_material", "tech_screenshot"),
    (r"证明材料.*云平台管理", "vendor_material", "tech_screenshot"),
    (r"证明材料.*服务器", "vendor_material", "tech_screenshot"),
    (r"证明材料.*交换机", "vendor_material", "tech_screenshot"),
    (r"证明材料.*防火墙", "vendor_material", "tech_screenshot"),
    (r"证明材料.*CDP|数据保护", "vendor_material", "tech_screenshot"),
    (r"营业执照", "company_credential", "license"),
    (r"承诺函", "company_credential", "commitment"),
    (r"商业信誉|财务会计", "company_credential", "financial_report"),
    (r"缴纳税收|社会保障", "company_credential", "tax_social"),
    (r"失信.*名单", "company_credential", "credit_check"),
    (r"非联合体", "company_credential", "commitment"),
    (r"廉政承诺", "company_credential", "commitment"),
    (r"业绩表", "project_case", "contract"),
    (r"其他资信", "company_credential", "other"),
    (r"ISO9001", "company_credential", "iso_cert"),
    (r"ISO14000", "company_credential", "iso_cert"),
    (r"ISO20000", "company_credential", "iso_cert"),
    (r"ISO27001", "company_credential", "iso_cert"),
    (r"厂商资质", "vendor_material", "product_cert"),
    (r"技术解决方案|技术方案|建设方案|部署方案", "bid_section", "tech_scheme"),
    (r"需求分析|项目背景|建设目标", "bid_section", "tech_scheme"),
    (r"采购需求响应", "bid_section", "tech_scheme"),
    (r"服务方案|售后服务", "bid_section", "service_plan"),
    (r"项目管理机构", "bid_section", "project_mgmt"),
    (r"项目负责人.*证书|PMP|软考", "personnel", "pm_cert"),
    (r"项目负责人.*业绩", "personnel", "pm_resume"),
    (r"项目负责人.*社保", "personnel", "social_security"),
    (r"项目团队.*资质", "personnel", "team_cert"),
    (r"项目团队.*社保", "personnel", "social_security"),
    (r"原厂实施团队", "personnel", "team_cert"),
    (r"服务承诺", "bid_section", "service_plan"),
    (r"优惠承诺", "bid_section", "service_plan"),
]

DEFAULT_CATEGORY = "bid_section"
DEFAULT_SUBTYPE = "general"


def classify_section(heading_path: str) -> tuple[str, str]:
    """Classify a section based on its heading path."""
    for pattern, category, sub_type in SECTION_RULES:
        if re.search(pattern, heading_path):
            return category, sub_type
    return DEFAULT_CATEGORY, DEFAULT_SUBTYPE


def extract_images(text: str) -> list[str]:
    """Extract image paths from Markdown/HTML img tags."""
    paths = []
    # Match <img src="media/imageN.ext" .../>
    for m in re.finditer(r'src="(media/[^"]+)"', text):
        paths.append(m.group(1))
    # Match ![...](media/...)
    for m in re.finditer(r'!\[.*?\]\((media/[^)]+)\)', text):
        paths.append(m.group(1))
    return list(dict.fromkeys(paths))  # deduplicate preserving order


def extract_page_refs(text: str) -> Optional[str]:
    """Extract page references like P190-P196 from text."""
    matches = re.findall(r'P\d+(?:-P\d+)?', text)
    if matches:
        return ", ".join(matches[:3])
    return None


def extract_tags(title: str, text: str) -> list[str]:
    """Extract meaningful tags from the content."""
    tags = []
    keywords = [
        "ISO9001", "ISO14000", "ISO20000", "ISO27001",
        "营业执照", "社保", "PMP", "软考",
        "ZStack", "华为", "安恒", "信核",
        "CDP", "虚拟化", "防火墙", "交换机",
        "授权书", "资质", "案例", "合同",
    ]
    combined = title + " " + text[:2000]
    for kw in keywords:
        if kw in combined:
            tags.append(kw)
    return tags


# ---------------------------------------------------------------------------
# Markdown splitter
# ---------------------------------------------------------------------------
def split_markdown_by_headings(content: str, min_chunk_size: int = 100) -> list[dict]:
    """
    Split a Markdown document by headings into chunks.
    Handles: # headings, <span anchor>**bold headings**, and **N.N.N section** patterns.
    Each chunk includes: title, heading_path, content, level.
    """
    lines = content.split("\n")
    chunks = []
    current_headings = {}  # level -> heading text
    current_chunk_lines = []
    current_title = "Document Start"
    current_level = 0

    def save_current_chunk():
        nonlocal current_chunk_lines, current_title, current_level
        chunk_text = "\n".join(current_chunk_lines).strip()
        if chunk_text and len(chunk_text) >= min_chunk_size:
            heading_path = " > ".join(
                current_headings.get(i, "") for i in sorted(current_headings.keys())
                if i <= current_level and current_headings.get(i)
            )
            chunks.append({
                "title": current_title,
                "heading_path": heading_path or current_title,
                "content": chunk_text,
                "level": current_level,
            })

    def detect_heading(line: str) -> tuple[int, str] | None:
        stripped = line.strip()

        # Standard Markdown headings: # Title, ## Title, etc.
        md_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if md_match:
            return len(md_match.group(1)), md_match.group(2).strip()

        # HTML anchor + bold heading: <span ...>**一、法定代表人资格证明书**
        anchor_bold = re.match(
            r'^<span[^>]*>\s*</span>\s*\*\*(.+?)\*\*$', stripped
        )
        if anchor_bold:
            title = anchor_bold.group(1).strip()
            # Determine level from numbering
            if re.match(r'^[一二三四五六七八九十]+、', title):
                return 2, title
            elif re.match(r'^\d+\.\d+', title):
                return 3, title
            return 2, title

        # Standalone bold heading on its own line: **4.2相关证明材料**
        bold_match = re.match(r'^\*\*(\d+[\.\d]*\s*.+?)\*\*$', stripped)
        if bold_match:
            title = bold_match.group(1).strip()
            dots = title.count('.')
            return min(2 + dots, 4), title

        # Numbered section bold heading: **4.2.1私有云平台证明材料**
        section_match = re.match(r'^\*\*(\d+\.\d[\.\d]*[^*]+)\*\*$', stripped)
        if section_match:
            title = section_match.group(1).strip()
            dots = title.count('.')
            return min(2 + dots, 4), title

        return None

    for line in lines:
        result = detect_heading(line)

        if result:
            level, heading_text = result
            save_current_chunk()

            # Update heading hierarchy
            current_headings[level] = heading_text
            for k in list(current_headings.keys()):
                if k > level:
                    del current_headings[k]

            current_title = heading_text
            current_level = level
            current_chunk_lines = [line]
        else:
            current_chunk_lines.append(line)

    # Save last chunk
    save_current_chunk()

    return chunks


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------
VAULT_ROOT = str(repo_path(settings.VAULT_ROOT).resolve())
MEDIA_BASE = os.path.join(
    VAULT_ROOT,
    "raw/historical-bids/浙江省财务开发有限责任公司私有云建设项目-2023/商务技术文件-bundle/attachments"
)

FILES_TO_INGEST = [
    {
        "path": os.path.join(VAULT_ROOT, "10-Knowledge/Evergreen/商务技术文件.md"),
        "source_doc": "商务技术文件.docx",
        "doc_type": "bid_response",
    },
    {
        "path": os.path.join(VAULT_ROOT, "10-Knowledge/Evergreen/招标文件案例.md"),
        "source_doc": "招标文件案例.docx",
        "doc_type": "tender",
    },
]


def ingest_file(db: Session, file_info: dict, dry_run: bool = False):
    """Ingest a single Markdown file into the evidence store."""
    filepath = file_info["path"]
    source_doc = file_info["source_doc"]

    print(f"\n{'='*60}")
    print(f"📄 Ingesting: {source_doc}")
    print(f"   Path: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"   Size: {len(content)} chars, {content.count(chr(10))} lines")

    # Split into chunks
    chunks = split_markdown_by_headings(content, min_chunk_size=80)
    print(f"   Chunks: {len(chunks)}")

    items_created = 0
    for i, chunk in enumerate(chunks):
        category, sub_type = classify_section(chunk["heading_path"])
        images = extract_images(chunk["content"])
        page_ref = extract_page_refs(chunk["content"])
        tags = extract_tags(chunk["title"], chunk["content"])

        # Build image paths relative to vault
        image_full_paths = [os.path.join(MEDIA_BASE, img) for img in images]

        # Create summary (first 100 chars of content, cleaned)
        clean_text = re.sub(r'<[^>]+>', '', chunk["content"])
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        summary = clean_text[:150]

        if dry_run:
            print(f"  [{i+1:3d}] {category}/{sub_type}: {chunk['title'][:50]} | {len(images)} imgs | tags={tags[:3]}")
            continue

        # Generate embedding
        embedding = None
        if ENABLE_EMBEDDINGS:
            try:
                embed_text = f"{chunk['title']}\n{clean_text[:4000]}"
                embedding = get_embedding(embed_text)
            except Exception as e:
                print(f"  Warning: Embedding failed for chunk {i}: {e}")

        item = EvidenceItem(
            category=category,
            sub_type=sub_type,
            title=chunk["title"],
            text_content=chunk["content"],
            summary=summary,
            file_path=filepath,
            image_paths=image_full_paths if images else [],
            source_doc=source_doc,
            source_page=page_ref,
            source_section=chunk["heading_path"],
            embedding=embedding,
            tags=tags,
        )
        db.add(item)
        items_created += 1

        if items_created % 10 == 0:
            print(f"  ... {items_created} items created")
            db.flush()

    if not dry_run:
        db.commit()

    print(f"  ✅ Done: {items_created} evidence items created from {source_doc}")
    return items_created


def main():
    print("=" * 60)
    print("  Evidence Store Ingestion Pipeline")
    print("=" * 60)

    # Check for --dry-run flag
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("  Mode: DRY RUN (no database writes)")
    else:
        print("  Mode: LIVE (writing to database)")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Clear existing evidence (for re-runs)
        if not dry_run:
            count = db.query(EvidenceItem).count()
            if count > 0:
                print(f"\n⚠️  Clearing {count} existing evidence items...")
                db.query(EvidenceItem).delete()
                db.commit()

        total = 0
        for file_info in FILES_TO_INGEST:
            if os.path.exists(file_info["path"]):
                total += ingest_file(db, file_info, dry_run=dry_run)
            else:
                print(f"  ⚠️  File not found: {file_info['path']}")

        print(f"\n{'='*60}")
        print(f"  ✅ Ingestion complete: {total} total evidence items")
        print(f"{'='*60}")

        # Print summary stats
        if not dry_run:
            for cat in ["company_credential", "vendor_material", "project_case", "personnel", "bid_section"]:
                count = db.query(EvidenceItem).filter(EvidenceItem.category == cat).count()
                if count:
                    print(f"  {cat}: {count} items")

    finally:
        db.close()


if __name__ == "__main__":
    main()
