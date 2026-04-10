import os
import re
import uuid
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session
from docxtpl import DocxTemplate, RichText

from api.models.assets_v2 import SourceDocument
from api.models.bid_draft_v2 import BidDraft
from api.models.rfp_v2 import RFPProject
from utils.word_engine import WordFragmentEngine

class BidExporter:
    """
    高保真 Word 导出引擎：基于 docxtpl 模板引擎，将草稿序列化为专业投标文件。
    """
    def __init__(self, db: Session):
        self.db = db
        self.template_path = "/root/it-bidding-copilot/templates/bidding_template.docx"

    def export_project_bid(self, project_id: int):
        """
        导出指定项目的全量标书，使用 docxtpl 模板引擎
        """
        project = self.db.query(RFPProject).filter(RFPProject.id == project_id).first()
        if not project:
            return None

        # 如果项目有原始 RFP，尝试作为母版 (这里目前简单处理，工业化方案建议统一使用标准模板)
        master_path = self._resolve_master_template(project) or self.template_path
        
        tpl = DocxTemplate(master_path)
        
        # 1. 获取所有并排序
        drafts = self.db.query(BidDraft).filter(
            BidDraft.project_id == project_id
        ).order_by(BidDraft.section_index).all()
        
        if not drafts:
            return None

        # 检查完整性
        incomplete_drafts = [
            draft.section_title
            for draft in drafts
            if draft.generation_status != "COMPLETED" or not (draft.content_markdown or "").strip()
        ]
        if incomplete_drafts:
            preview = "、".join(incomplete_drafts[:5])
            raise ValueError(f"导出中断：有 {len(incomplete_drafts)} 个章节尚未完成或内容为空: {preview}")

        # 2. 构造模板上下文
        processed_drafts = []
        for draft in drafts:
            # 创建 subdoc 处理 Markdown 渲染
            subdoc = tpl.new_subdoc()
            self._render_markdown_to_subdoc(subdoc, draft.content_markdown or "")
            
            processed_drafts.append({
                "section_title": draft.section_title,
                "winning_points": draft.winning_points,
                "rendered_content": subdoc,
                "source_fragments": (draft.source_fragments or [])[:8]
            })

        context = {
            "project_name": project.project_name,
            "subtitle": f"项目编号: {project_id} | 工业化投标方案",
            "drafts": processed_drafts
        }

        # 3. 渲染
        tpl.render(context)
        
        # 4. 如果是使用 Master Template (RFP)，且渲染后的文档可能不包含这些章节 (比如模板里没写 tags)
        # 我们追加一个“技术标内容”章节。
        # 工业化改进：如果模板中没有发现 {{ drafts }} 标签，则自动追加
        doc = tpl.docx
        doc.add_page_break()
        doc.add_heading(f"项目投标书：{project.project_name}", level=1)
        doc.add_heading("生成的标书正文 (自动追加)", level=2)
        
        for draft_data in processed_drafts:
             doc.add_heading(draft_data["section_title"], level=2)
             if draft_data["winning_points"]:
                  p = doc.add_paragraph()
                  p.add_run("核心优势：").bold = True
                  p.add_run(draft_data["winning_points"])
             
             # 我们无法直接将 subdoc (一个新的 Document) 简单的 merge 进 doc 的末尾而保持样式。
             # 简单方案：如果是 fallback 模式，直接在主文档重新渲染一次 Markdown
             draft_id = drafts[processed_drafts.index(draft_data)].id
             draft_obj = self.db.query(BidDraft).filter(BidDraft.id == draft_id).first()
             if draft_obj:
                  self._render_markdown_to_subdoc(doc, draft_obj.content_markdown or "")

        # 5. 追加证据片段 (Evidence Appendix)
        doc.add_page_break()
        doc.add_heading("章节证据附录", level=1)
        for draft in drafts:
            if draft.source_fragments:
                doc.add_heading(f"章节：{draft.section_title}", level=2)
                for frag in draft.source_fragments:
                    clean_frag = frag
                    img_matches = list(re.finditer(r"\[IMAGE:(.*?)\]", frag))
                    
                    for match in img_matches:
                        img_name = os.path.basename(match.group(1))
                        clean_frag = clean_frag.replace(match.group(0), f"(见附图：{img_name})")
                    
                    doc.add_paragraph(clean_frag)
                    
                    for match in img_matches:
                        img_name = os.path.basename(match.group(1))
                        cap = doc.add_paragraph(f"凭证凭证 - 图片证据：{img_name}", style='Caption')

        save_dir = "/root/it-bidding-copilot/exports"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"bid_{project_id}_{uuid.uuid4().hex[:8]}.docx")
        tpl.save(save_path)
        
        return save_path

    def _render_markdown_to_subdoc(self, doc, content: str):
        """
        将 Markdown 片段渲染到文档中，支持标题、列表、表格和基础行内样式。
        """
        # 1. 提取并标记表格
        table_matches = re.findall(r"(\|.*\|(?:\n\|.*\|)+)", content)
        remaining_text = content
        for table_str in table_matches:
            remaining_text = remaining_text.replace(table_str, f"\n[TABLE_MARKER_{hash(table_str)}]\n")
            
        lines = remaining_text.split('\n')
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # 处理表格标记
            if line_stripped.startswith('[TABLE_MARKER_'):
                try:
                    target_hash = int(line_stripped[14:-1])
                    for t_str in table_matches:
                        if hash(t_str) == target_hash:
                            rows = [r.strip().split('|')[1:-1] for r in t_str.split('\n') if '|' in r and '---' not in r]
                            if rows:
                                table = doc.add_table(rows=len(rows), cols=len(rows[0]))
                                table.style = 'Table Grid'
                                for r_idx, row_data in enumerate(rows):
                                    for c_idx, val in enumerate(row_data):
                                        self._add_formatted_text(table.cell(r_idx, c_idx).paragraphs[0], val.strip())
                except (ValueError, IndexError):
                    pass
                continue

            # 处理标题
            if line_stripped.startswith('### '):
                doc.add_heading(line_stripped[4:], level=3)
            elif line_stripped.startswith('## '):
                doc.add_heading(line_stripped[3:], level=2)
            elif line_stripped.startswith('# '):
                doc.add_heading(line_stripped[2:], level=1)
            # 处理列表
            elif line_stripped.startswith('- ') or line_stripped.startswith('* '):
                p = doc.add_paragraph(style='List Bullet')
                self._add_formatted_text(p, line_stripped[2:])
            elif re.match(r'^\d+\. ', line_stripped):
                p = doc.add_paragraph(style='List Number')
                self._add_formatted_text(p, re.sub(r'^\d+\. ', '', line_stripped))
            # 普通正文
            else:
                p = doc.add_paragraph()
                self._add_formatted_text(p, line)

    def _add_formatted_text(self, paragraph, text: str):
        """
        处理行内样式：**bold**, *italic*, 以及基础文本。
        """
        # 简单的正则替换逻辑
        parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                paragraph.add_run(part[2:-2]).bold = True
            elif part.startswith('*') and part.endswith('*'):
                paragraph.add_run(part[1:-1]).italic = True
            else:
                paragraph.add_run(part)

    def _resolve_master_template(self, project: RFPProject) -> str | None:
        if not project.rfp_source_id:
            return None
        source_doc = self.db.query(SourceDocument).filter(SourceDocument.id == project.rfp_source_id).first()
        if source_doc and source_doc.local_path and os.path.exists(source_doc.local_path):
            if Path(source_doc.local_path).suffix.lower() == ".docx":
                return source_doc.local_path
        return None
