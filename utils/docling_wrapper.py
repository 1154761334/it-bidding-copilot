import os
import re
from pathlib import Path
from typing import List, Dict, Any

from docling.document_converter import DocumentConverter
from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from api.models.ontology import SourceCoordinate

class DoclingWrapper:
    """
    RFP 多模态解析器：
    基于 IBM Docling 实现对 PDF/Docx 的深度理解，支持：
    1. 表格精准还原
    2. 图片自动分离与存储
    3. 语义块坐标锁定
    """
    def __init__(self, output_dir: str = "/root/it-bidding-copilot/assets/extracted_images"):
        self.converter = DocumentConverter()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert(self, file_path: str) -> Dict[str, Any]:
        """
        执行多模态转换：
        返回 Markdown 文本、提取的图片列表以及坐标映射
        """
        suffix = Path(file_path).suffix.lower()
        if suffix == ".docx":
            return self._convert_docx(file_path)
        if suffix in {".txt", ".md"}:
            return self._convert_plaintext(file_path)

        print(f"正在启动 Docling 引擎解析: {file_path}")
        result = self.converter.convert(file_path)
        
        # 1. 导出层级 Markdown
        markdown_content = result.document.export_to_markdown()
        
        # 2. 图像原生提取逻辑 (Native Image Extraction)
        images = []
        doc_filename = os.path.basename(file_path)
        
        # 遍历 Docling 解析出的图片对象
        for i, picture in enumerate(result.document.pictures):
            # 获取图片在文档中的位置锚点 (用于后续回溯)
            # anchor = picture.prov[0]
            
            img_rel_path = f"{doc_filename}_native_{i}.png"
            full_img_path = self.output_dir / img_rel_path
            
            # 这里的逻辑是：如果是 Word，直接从 Ooxml 导出原始二进制流
            # 如果是 PDF，从 PDF 资源对象中导出
            # Docling 的 picture.image 对象通常是 PIL Image
            try:
                if hasattr(picture, 'image') and picture.image:
                    picture.image.save(full_img_path)
                    images.append(str(full_img_path))
                    print(f"✅ 成功原生提取图片: {img_rel_path}")
            except Exception as e:
                print(f"⚠️ 图片提取失败: {str(e)}")
        
        # 3. 构造虚拟坐标映射 (对接前端 Tracer)
        coordinates = [
            SourceCoordinate(page=1, bbox=[10, 10, 100, 50], text="解析坐标占位")
        ]
        
        return {
            "markdown": markdown_content,
            "images": images,
            "coordinates": coordinates
        }

    def _convert_docx(self, file_path: str) -> Dict[str, Any]:
        doc = Document(file_path)
        markdown_blocks: list[str] = []
        image_map = self._extract_docx_images(doc, file_path)
        images = list(image_map.values())

        for block in self._iter_block_items(doc):
            if isinstance(block, Paragraph):
                paragraph_blocks = self._render_paragraph_blocks(block, image_map)
                markdown_blocks.extend(paragraph_blocks)
            elif isinstance(block, Table):
                table_blocks = self._render_table_blocks(block)
                markdown_blocks.extend(table_blocks)

        return {
            "markdown": "\n\n".join(markdown_blocks),
            "images": images,
            "coordinates": [SourceCoordinate(page=1, bbox=[10, 10, 100, 50], text="DOCX 内容占位")],
        }

    def _convert_plaintext(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {
            "markdown": content,
            "images": [],
            "coordinates": [SourceCoordinate(page=1, bbox=[10, 10, 100, 50], text="文本内容占位")],
        }

    def _infer_heading_level(self, text: str) -> int | None:
        normalized = text.strip()
        if not normalized:
            return None

        if re.match(r"^第[一二三四五六七八九十百]+章", normalized):
            return 1
        if re.match(r"^[一二三四五六七八九十]+、", normalized):
            return 2
        number_match = re.match(r"^(\d+(?:\.\d+)+)", normalized)
        if number_match:
            dot_count = number_match.group(1).count(".")
            return min(dot_count + 2, 6)
        if re.match(r"^\d+[）\)]", normalized):
            return 4
        return None

    def _extract_docx_images(self, doc: Document, file_path: str) -> dict[str, str]:
        images: dict[str, str] = {}
        doc_filename = Path(file_path).stem
        seen_targets: set[str] = set()

        for rel_id, rel in doc.part.rels.items():
            if "image" not in rel.reltype:
                continue
            target_part = rel.target_part
            partname = str(target_part.partname)
            if partname in seen_targets:
                continue
            seen_targets.add(partname)
            suffix = Path(partname).suffix or ".bin"
            img_path = self.output_dir / f"{doc_filename}_{Path(partname).stem}{suffix}"
            with open(img_path, "wb") as f:
                f.write(target_part.blob)
            images[rel_id] = str(img_path)

        return images

    def _iter_block_items(self, parent: DocxDocument):
        parent_elm = parent.element.body
        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    def _render_paragraph_blocks(self, paragraph: Paragraph, image_map: dict[str, str]) -> list[str]:
        blocks: list[str] = []
        text = paragraph.text.strip()
        if text:
            style_name = (paragraph.style.name or "").lower()
            if "heading" in style_name:
                level_text = "".join(ch for ch in paragraph.style.name if ch.isdigit())
                level = int(level_text) if level_text else 1
                blocks.append(f"{'#' * max(1, min(level, 6))} {text}")
            else:
                inferred_level = self._infer_heading_level(text)
                if inferred_level is not None:
                    blocks.append(f"{'#' * inferred_level} {text}")
                else:
                    blocks.append(text)

        for image_path in self._extract_paragraph_image_paths(paragraph, image_map):
            blocks.append(f"[IMAGE:{image_path}]")
        return blocks

    def _render_table_blocks(self, table: Table) -> list[str]:
        rows = []
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            if any(cells):
                rows.append(cells)
        if not rows:
            return []
        header = rows[0]
        divider = ["---"] * len(header)
        blocks = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(divider) + " |",
        ]
        for row in rows[1:]:
            normalized = row + [""] * (len(header) - len(row))
            blocks.append("| " + " | ".join(normalized[: len(header)]) + " |")
        return blocks

    def _extract_paragraph_image_paths(self, paragraph: Paragraph, image_map: dict[str, str]) -> list[str]:
        paths: list[str] = []
        seen: set[str] = set()
        for drawing in paragraph._element.xpath(".//w:drawing"):
            blips = drawing.xpath(".//a:blip")
            for blip in blips:
                rel_id = blip.get(qn("r:embed"))
                if not rel_id:
                    continue
                image_path = image_map.get(rel_id)
                if image_path and image_path not in seen:
                    seen.add(image_path)
                    paths.append(image_path)
        return paths

if __name__ == "__main__":
    # 简单的 PoC 测试用例逻辑
    pass
