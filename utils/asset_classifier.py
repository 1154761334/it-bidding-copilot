import os
from typing import Literal, Dict, List
from utils.docling_wrapper import DoclingWrapper
from api.services.document_parse_service import DocumentParseService
import json

AssetType = Literal["CASE", "CERTIFICATE", "PERSONNEL", "GENERAL"]

class AssetClassifier:
    """
    智能资产全量分发器：
    集成了 MinerU (PDF) 和 Docling (其他) 的解析能力。
    """
    def __init__(self, model_name="gpt-4o"):
        self.model_name = model_name
        self.pdf_parser = DocumentParseService()
        self.docling_parser = DoclingWrapper()
    
    def classify(self, content_markdown: str, filename: str) -> AssetType:
        """
        根据内容特征进行分类。
        """
        content_lower = content_markdown.lower()
        fn_lower = filename.lower()
        
        if any(kw in content_lower or kw in fn_lower for kw in ["简历", "工程师", "职员", "从业经历", "社保"]):
            return "PERSONNEL"
        if any(kw in content_lower or kw in fn_lower for kw in ["证书", "等级", "认证", "有效期", "资质"]):
            return "CERTIFICATE"
        if any(kw in content_lower or kw in fn_lower for kw in ["合同", "中标", "项目案例", "金额", "工程内容"]):
            return "CASE"
            
        return "GENERAL"

    async def auto_ingest(self, file_path: str):
        """
        集成解析与智能分类的完整流水线。
        """
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".pdf":
            parse_result = self.pdf_parser.parse_pdf(file_path)
            # Read markdown
            with open(parse_result["markdown_file"], "r", encoding="utf-8") as f:
                md = f.read()
            # Read content list for chunks
            with open(parse_result["content_list_file"], "r", encoding="utf-8") as f:
                content_list = json.load(f)
            
            chunks = self._extract_chunks_from_mineru(content_list)
        else:
            parse_data = self.docling_parser.convert(file_path)
            md = parse_data["markdown"]
            chunks = self._chunk_markdown(md)
            parse_result = parse_data

        asset_type = self.classify(md, filename)
        
        return {
            "type": asset_type,
            "data": {"markdown": md, "raw": parse_result},
            "chunks": chunks,
            "filename": filename
        }

    def _extract_chunks_from_mineru(self, content_list: List[Dict]) -> List[Dict]:
        """
        Extract chunks from MinerU's content_list.json.
        """
        chunks = []
        for item in content_list:
            if item["type"] in ["text", "table"]:
                chunks.append({
                    "type": item["type"],
                    "content": item.get("text") or item.get("text_content") or ""
                })
        return chunks

    def _chunk_markdown(self, md: str) -> List[Dict]:
        """
        将 Markdown 拆分为语义块 (表格或段落)
        """
        import re
        chunks = []
        
        # 提取表格 (Markdown 表格通常以 | 开始)
        tables = re.findall(r"(\|.*\|(?:\n\|.*\|)+)", md)
        for t in tables:
            chunks.append({"type": "table", "content": t})
            
        # 提取普通段落 (按双换行拆分，过滤掉表格部分)
        rem_md = md
        for t in tables:
            rem_md = rem_md.replace(t, "\n[TABLE_PLACEHOLDER]\n")
            
        paragraphs = [p.strip() for p in rem_md.split("\n\n") if p.strip()]
        for p in paragraphs:
            if p != "[TABLE_PLACEHOLDER]":
                chunks.append({"type": "text", "content": p})
                
        return chunks
