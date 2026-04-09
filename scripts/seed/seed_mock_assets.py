import datetime
import json
from sqlalchemy import text
from api.core.database import SessionLocal
from api.models.assets_v2 import Company, EnterpriseCase, EnterpriseCertificate, EnterprisePersonnel

def seed_assets():
    """
    灌入 V3 架构数据：
    1. 首个公司：中智诚标科技 (Main Company)
    2. 挂载多个案例、证书与人员
    """
    db = SessionLocal()
    print("正在清空旧数据并重新灌入 V3 测试资产...")
    
    try:
        # 清理旧数据 (级联清理)
        db.query(EnterpriseCase).delete()
        db.query(EnterpriseCertificate).delete()
        db.query(EnterprisePersonnel).delete()
        db.query(Company).delete()
        db.commit()
        
        # 1. 创建公司主体
        company_a = Company(
            company_name="中智诚标科技有限公司",
            description="专注于政务云与智慧城市建设的头部集成商。"
        )
        db.add(company_a)
        db.commit()
        db.refresh(company_a)
        
        # 2. 灌入案例 (Enterprise Cases)
        cases = [
            EnterpriseCase(
                company_id=company_a.id,
                project_name="北京市某局政务云二期建设项目",
                industry="政务云",
                contract_amount=15800000.0,
                sign_date=datetime.date(2023, 5, 20),
                description="涉及全栈国产化信创架构，包含高可用集群部署与数据安全迁移。",
                embedding=[0.1] * 1536
            ),
            EnterpriseCase(
                company_id=company_a.id,
                project_name="国家电网分布式储能监控平台",
                industry="能源",
                contract_amount=28000000.0,
                sign_date=datetime.date(2021, 8, 10),
                description="针对分布式能源的实时调度系统，支持高并发数据采集与 AI 预测。",
                embedding=[0.3] * 1536
            )
        ]
        
        # 3. 灌入资质证书 (Enterprise Certificates)
        certs = [
            EnterpriseCertificate(
                company_id=company_a.id,
                cert_type="信息安全管理体系认证",
                cert_level="ISO27001",
                raw_name="ISO/IEC 27001 信息安全管理体系",
                issue_date=datetime.date(2023, 1, 1),
                expiry_date=datetime.date(2026, 1, 1),
                image_url="/assets/images/certs/iso27001_v1.jpg",
                embedding=[0.5] * 1536
            )
        ]
        
        # 4. 灌入人员简历 (Enterprise Personnel)
        personnel = [
            EnterprisePersonnel(
                company_id=company_a.id,
                name="张建国",
                role="高级架构师",
                resume_text="15年 IT 建设经验，曾主导过多个省级政务云项目，精通国产化适配与分布式架构。",
                social_security_image_url="/assets/images/social/zhang_ss.jpg",
                embedding=[0.7] * 1536
            )
        ]
        
        db.add_all(cases)
        db.add_all(certs)
        db.add_all(personnel)
        db.commit()
        print(f"V3 数据铺设成功：公司 '{company_a.company_name}' 旗下已挂载案例、证书与人员。")
        
    except Exception as e:
        db.rollback()
        print(f"录入失败: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_assets()
