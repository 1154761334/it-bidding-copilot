import datetime
from sqlalchemy.orm import Session
from api.core.logger import get_logger
from api.models.assets_v2 import SourceDocument
from utils.docling_wrapper import DoclingWrapper

logger = get_logger("document_parse_service")

class DocumentParseService:
    """
    Unified entry point for all document parsing tasks.
    Maintains parsing state in the database and standardizes output elements.
    """
    def __init__(self, db: Session):
        self.db = db
        self.docling_parser = DoclingWrapper()

    async def parse(self, source_doc_id: int, mode: str = "auto") -> dict:
        """
        Parses a document, updates its status, and returns standardized elements.
        """
        source_doc = self.db.query(SourceDocument).filter(SourceDocument.id == source_doc_id).first()
        if not source_doc:
            raise ValueError(f"SourceDocument {source_doc_id} not found")

        source_doc.parse_status = "PARSING"
        self.db.commit()

        try:
            logger.info("Parsing document: %s (id: %s) using mode: %s", source_doc.filename, source_doc.id, mode)
            
            # Currently only docling_wrapper is implemented as the primary backend
            # In Phase B, we can add logic to route to MinerU, OCR, etc.
            import asyncio
            parse_result = await asyncio.to_thread(self.docling_parser.convert, source_doc.local_path)
            
            # Standardize output
            md = parse_result.get("markdown", "")
            
            # Basic section splitting by headers
            sections = []
            current_section = {"title": "Root", "content": []}
            for line in md.splitlines():
                if line.startswith("#"):
                    if current_section["content"] or current_section["title"] != "Root":
                        sections.append({
                            "title": current_section["title"],
                            "content": "\n".join(current_section["content"]).strip()
                        })
                    current_section = {"title": line.lstrip("#").strip(), "content": []}
                else:
                    current_section["content"].append(line)
            if current_section["content"] or current_section["title"] != "Root":
                sections.append({
                    "title": current_section["title"],
                    "content": "\n".join(current_section["content"]).strip()
                })

            standard_output = {
                "parser": "DoclingWrapper",
                "backend": "hybrid",
                "quality_report": {
                    "has_tables": "|" in md,
                    "image_count": len(parse_result.get("images", [])),
                    "markdown_length": len(md),
                    "section_count": len(sections)
                },
                "document_meta": {
                    "filename": source_doc.filename,
                    "file_type": source_doc.file_type,
                    "local_path": source_doc.local_path
                },
                "sections": sections,
                "tables": [], # Table extraction can be added in Phase B with MinerU
                "images": parse_result.get("images", []),
                # Keep both keys during the transition. Several downstream callers still
                # read parse_result["markdown"] directly.
                "markdown": md,
                "raw_markdown": md,
                "trace": {
                    "started_at": datetime.datetime.now().isoformat(),
                    "coordinates": parse_result.get("coordinates", [])
                }
            }

            source_doc.parse_status = "COMPLETED"
            source_doc.parsed_at = datetime.date.today()
            source_doc.parse_error = None
            self.db.commit()

            return standard_output

        except Exception as e:
            logger.exception("Failed to parse document: %s", source_doc_id)
            source_doc.parse_status = "FAILED"
            source_doc.parse_error = str(e)
            self.db.commit()
            raise
