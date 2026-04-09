import os
import shutil
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session
from api.models.assets_v2 import CompanyAsset
from api.core.config import get_settings
settings = get_settings()

class AssetManager:
    """
    企业资产管理器：
    负责将本地图片/文档进行 UUID 重命名、物理归档，并同步至数据库映射。
    """
    def __init__(self, db: Session):
        self.db = db

    def register_asset(self, 
                       file_path: str, 
                       company_id: int, 
                       asset_name: str, 
                       category: str, 
                       asset_tag: str = None,
                       metadata: dict = None) -> CompanyAsset:
        """
        将外部文件注册进入 IT Bidding Copilot 资产库。
        
        :param file_path: 原始文件路径
        :param company_id: 所属企业 ID
        :param asset_name: 资产友好名称 (如：浙江分公司营业执照)
        :param category: 资产分类 (如：qualification, case)
        :param asset_tag: 业务检索标签 (如：business_license)
        :param metadata: 扩展元数据字典 (如：{"expiry_date": "2026-01-01"})
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        # 1. 生成全局唯一标识
        asset_id = str(uuid.uuid4())
        ext = os.path.splitext(file_path)[1].lower()
        new_filename = f"{asset_id}{ext}"
        
        # 2. 判别文件类型并确定存至哪个物理子目录
        is_image = ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf'] # PDF 也可以作为佐证图
        target_dir = settings.ASSET_IMAGES_DIR if is_image else settings.ASSET_DOCS_DIR
        target_path = target_dir / new_filename
        
        # 3. 执行物理拷贝 (保留原始文件，存入受控区域)
        shutil.copy2(file_path, target_path)
        
        # 4. 数据库持久化记录
        new_asset = CompanyAsset(
            id=asset_id,
            company_id=company_id,
            asset_name=asset_name,
            asset_type="image" if is_image else "document",
            category=category,
            asset_tag=asset_tag,
            local_path=str(target_path),
            metadata_json=json.dumps(metadata) if metadata else None,
            upload_date=datetime.now().date()
        )
        
        try:
            self.db.add(new_asset)
            self.db.commit()
            self.db.refresh(new_asset)
            return new_asset
        except Exception as e:
            self.db.rollback()
            # 物理文件回滚
            if target_path.exists():
                os.remove(target_path)
            raise e

    def get_asset_by_tag(self, company_id: int, asset_tag: str) -> CompanyAsset:
        """根据业务标签快速获取最新资产记录"""
        return self.db.query(CompanyAsset).filter(
            CompanyAsset.company_id == company_id,
            CompanyAsset.asset_tag == asset_tag
        ).order_by(CompanyAsset.upload_date.desc()).first()
