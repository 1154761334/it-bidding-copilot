import sys
import os
from datetime import date
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from api.core.database import SessionLocal
from api.models.assets_v2 import Company, EnterpriseCertificate, EnterprisePersonnel

def seed_business_entities():
    db = SessionLocal()
    try:
        # 1. 精准定位或创建目标公司
        target_name = "极客商务科技有限公司"
        company = db.query(Company).filter(Company.company_name == target_name).first()
        
        if not company:
            # 如果名字没重复，尝试拿 ID 1 的改名，或者新建
            company = db.query(Company).get(1)
            if company:
                company.company_name = target_name
            else:
                company = Company(company_name=target_name)
                db.add(company)
        
        # 2. 强制同步所有核心商业属性
        company.unified_social_credit_code = "91330100MA2H7A123X"
        company.registered_capital = "1000万元人民币"
        company.address = "浙江省杭州市西湖区超级大厦 88 层"
        company.legal_representative = "马老板"
        db.flush()

        # 3. 清理该公司的老旧资产/人员，重新灌入
        db.query(EnterpriseCertificate).filter(EnterpriseCertificate.company_id == company.id).delete()
        db.query(EnterprisePersonnel).filter(EnterprisePersonnel.company_id == company.id).delete()

        # 灌入资质 (带业务分类)
        certs = [
            ("体系认证", "ISO 9001 质量管理体系认证", "一级", date(2026, 1, 1)),
            ("体系认证", "ISO 27001 信息安全管理体系认证", "高级", date(2025, 12, 1)),
            ("行业资质", "信息系统建设和服务能力证书 (CS4)", "四级", date(2027, 8, 15)),
            ("软件能力", "CMMI 5级 软件成熟度集成模型认证", "5级", date(2028, 5, 20))
        ]
        for cat, name, level, expiry in certs:
            db.add(EnterpriseCertificate(
                company_id=company.id, cert_type=cat, raw_name=name, cert_level=level, expiry_date=expiry
            ))

        # 灌入人员 (带专家职级)
        staff = [
            ("张三", "技术总监", "专家级", 15),
            ("李四", "项目经理", "高级工程师", 8),
            ("王五", "安全专家", "中级工程师", 5)
        ]
        for name, role, level, years in staff:
            db.add(EnterprisePersonnel(
                company_id=company.id, name=name, role=role, level=level, years_of_experience=years
            ))

        db.commit()
        print(f"✅ 业务实体库 ({target_name}) 数据极速同步完成！")
    except Exception as e:
        db.rollback()
        print(f"❌ 同步失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_business_entities()
