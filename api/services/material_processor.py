from sqlalchemy.orm import Session
from api.models.bid_draft_v2 import ProjectMaterial
from utils.docling_wrapper import DoclingWrapper
import os

class MaterialProcessor:
    """
    项目物料处理器：负责将用户上传的 pdf/docx 转换为 Agent 可理解的 Markdown。
    """
    def __init__(self, db: Session):
        self.db = db
        self.docling = DoclingWrapper()

    def process_material(self, material_id: int):
        """
        解析物料内容并更新数据库
        """
        material = self.db.query(ProjectMaterial).filter(ProjectMaterial.id == material_id).first()
        if not material or not os.path.exists(material.local_path):
            return False
            
        print(f"--- Processing Project Material: {material.filename} ---")
        
        try:
            parse_result = self.docling.convert(material.local_path)
            md_content = parse_result.get("markdown", "")
            
            # 更新模型
            material.parsed_content = md_content
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error processing material: {e}")
            return False
