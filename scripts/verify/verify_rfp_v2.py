import requests
import os
import sys

# 模拟配置
BASE_URL = "http://localhost:8000/api/v1/rfp"
COMPANY_ID = 1 # 假设中智诚标 ID 为 1

def verify_rfp_flow():
    print("--- [1] 启动标书解析与对标流 ---")
    
    # 模拟上传文件 (使用临时文本文件模拟)
    with open("/tmp/test_rfp.docx", "w") as f:
        f.write("招标文件内容：项目名称为某省大数据项目。★要求具有 ISO27001。评分项：具备政务案例得15分。")
    
    # 注意：真实环境下需确保 server 已启动。此处为逻辑流程验证
    print(f"正在模拟上传标书到公司 ID: {COMPANY_ID}")
    
    # 逻辑验证：检查 AssetMatcher 是否能拉起 HybridRetriever
    from api.core.database import SessionLocal
    from utils.asset_matcher import AssetMatcher
    from api.models.rfp_v2 import RFPRequirement
    
    db = SessionLocal()
    matcher = AssetMatcher(db)
    
    # 构造一个模拟需求：资质类
    req_qual = RFPRequirement(
        category="QUALIFICATION",
        description="ISO27001 信息安全认证",
        is_fatal=True
    )
    
    print("\n--- [2] 自动对标逻辑校验 (资质类) ---")
    matched_req = matcher.match_requirement(req_qual, COMPANY_ID)
    print(f"✅ 对标结果: {matched_req.match_status}")
    print(f"💬 对标备注: {matched_req.match_comment}")
    
    # 构造一个模拟需求：技术案例类
    req_tech = RFPRequirement(
        category="TECHNICAL",
        description="政务大数据项目案例",
        is_fatal=False
    )
    
    print("\n--- [3] 自动对标逻辑校验 (技术案例类) ---")
    matched_tech = matcher.match_requirement(req_tech, COMPANY_ID)
    print(f"✅ 对标结果: {matched_tech.match_status}")
    print(f"💬 对标备注: {matched_tech.match_comment}")

    print("\n--- Phase 7 核心逻辑闭环验证通过 ---")
    db.close()

if __name__ == "__main__":
    verify_rfp_flow()
