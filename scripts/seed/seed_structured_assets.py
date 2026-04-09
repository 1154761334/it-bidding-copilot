import sys
import os
from datetime import datetime, date
sys.path.append(os.getcwd())

from api.core.database import SessionLocal
from api.models.assets_v2 import Company, EnterpriseCertificate, EnterprisePersonnel, EnterpriseCase

def seed_structured_data():
    db = SessionLocal()
    
    # 1. 确保读取真实公司主数据（文字维度）
    company = db.query(Company).filter(Company.company_name == "测试演示公司").first()
    if not company:
        company = Company(
            company_name="测试演示公司", 
            description="一家拥有雄厚IT技术背景的企业，注册资金5000万，成立于2010年。"
        )
        db.add(company)
        db.commit()
        db.refresh(company)

    # 2. 存入真实的资质信息 (文字与日期 + 佐证材料图片绑定)
    print("--- 正在录入公司资质结构化信息 ---")
    iso_cert = db.query(EnterpriseCertificate).filter(EnterpriseCertificate.raw_name == "ISO 9001 质量管理体系认证").first()
    if not iso_cert:
        iso_cert = EnterpriseCertificate(
            company_id=company.id,
            cert_type="体系认证",
            cert_level="国际级",
            raw_name="ISO 9001 质量管理体系认证",
            certification_scope="计算机软件的安全开发与服务",
            issue_date=date(2023, 1, 1),
            expiry_date=date(2026, 1, 1),
            # 【这里是核心】：将文字属性与上一阶段我们生成的物理照片 UUID 绑定！
            image_url="data/assets/images/fcd57585-04a1-48ba-9023-1f4f53e497af.jpg" 
        )
        db.add(iso_cert)
        print("✅ 录入成功: ISO 9001 及关联照片引用")
        
    # 3. 存入核心人员信息 (文字 + 社保证明图片绑定)
    print("--- 正在录入核心人员结构化信息 ---")
    personnel = db.query(EnterprisePersonnel).filter(EnterprisePersonnel.name == "张三").first()
    if not personnel:
        personnel = EnterprisePersonnel(
            company_id=company.id,
            name="张三",
            role="高级项目经理",
            resume_text="拥有10年私有云建设经验，PMP认证，主导过多个省级政务云项目。",
            # 同样绑定到具体的物理资产上
            social_security_image_url="data/assets/images/personnel_ssn_mock_uuid.png"
        )
        db.add(personnel)
        print("✅ 录入成功: 项目经理 张三 及社保图片引用")

    db.commit()
    db.close()
    print("--- 结构化资产组装完毕 ---")

if __name__ == "__main__":
    seed_structured_data()
