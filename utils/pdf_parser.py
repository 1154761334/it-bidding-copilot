"""
PDF 文档解析工具
使用 pdfplumber 提取 PDF 文本与表格，预留 RAGFlow API 接口
"""
import io
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """从 PDF 文件字节提取全文文本"""
    if pdfplumber is None:
        return _mock_extract(file_bytes)

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_tables_from_pdf(file_bytes: bytes) -> list[list[list[str]]]:
    """从 PDF 提取全部表格，返回三层嵌套列表 [table][row][cell]"""
    if pdfplumber is None:
        return []

    tables = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables


def extract_text_via_ragflow(file_bytes: bytes, api_url: str, api_key: str) -> Optional[str]:
    """预留 RAGFlow API 解析接口（未实现）"""
    # TODO: 实现 RAGFlow API 调用
    raise NotImplementedError("RAGFlow API 接口尚未接入，请使用本地 pdfplumber 解析")


def _mock_extract(file_bytes: bytes) -> str:
    """本地 Mock 文本提取（当 pdfplumber 不可用时）"""
    return (
        "【Mock 提取结果】\n\n"
        f"文件大小：{len(file_bytes)} 字节\n\n"
        "本内容为模拟提取，请安装 pdfplumber 以启用真实 PDF 解析。\n"
        "pip install pdfplumber"
    )
