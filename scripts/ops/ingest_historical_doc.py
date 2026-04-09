import os
import sys
import uuid
import json
from pathlib import Path
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT

sys.path.append(os.getcwd())
from api.core.database import SessionLocal
from utils.asset_manager import AssetManager

def ingest_docx_images(docx_path: str, company_id: int):
    print(f"--- 启动历史资产自动化提取: {docx_path} ---")
    db = SessionLocal()
    manager = AssetManager(db)
    
    doc_name = Path(docx_path).stem
    temp_dir = Path("/tmp/extracted_assets")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        doc = Document(docx_path)
        image_count = 0
        
        # 遍历文档关系寻找图片
        for rel in doc.part.rels.values():
            if rel.reltype == RT.IMAGE:
                image_count += 1
                image_part = rel.target_part
                
                # 获取图片原始名称后缀
                ext = os.path.splitext(image_part.partname)[1]
                temp_file = temp_dir / f"temp_img_{image_count}{ext}"
                
                # 写入临时文件
                with open(temp_file, "wb") as f:
                    f.write(image_part.blob)
                
                # 注册到资产库
                asset_name = f"历史资产-{doc_name}-图{image_count}"
                asset = manager.register_asset(
                    file_path=str(temp_file),
                    company_id=company_id,
                    asset_name=asset_name,
                    category="historical",
                    asset_tag=f"hist_{doc_name}_{image_count}",
                    metadata={
                        "source": docx_path,
                        "extraction_rank": image_count,
                        "original_partname": image_part.partname
                    }
                )
                print(f"成功入库: {asset.asset_name} -> {asset.id}")
                
        print(f"\n--- 提取完成！共计入库 {image_count} 个多模态资产 ---")
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
    finally:
        db.close()
        # 清理临时文件
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 script.py <docx_path> <company_id>")
    else:
        ingest_docx_images(sys.argv[1], int(sys.argv[2]))
