"""
Step 1: 企业档案管理与资产导入
"""
import streamlit as st
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from config import ENTERPRISE_DIR, WORKFLOW_STEPS, get_llm
from utils.pdf_parser import extract_text_from_pdf
from knowledge.vector_store import KnowledgeBase

st.set_page_config(page_title="企业档案管理 - IT Bidding Copilot", page_icon="🏢", layout="wide")

# ── 页面 CSS ──
st.markdown("""
<style>
    .profile-header {
        background: linear-gradient(135deg, rgba(108,99,255,0.08), rgba(0,212,170,0.06));
        border: 1px solid rgba(108,99,255,0.2);
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }
    .profile-header h2 {
        margin: 0 0 6px 0;
        font-size: 1.5rem;
    }
    .profile-header p { color: #9CA3AF; margin: 0; }
</style>
""", unsafe_allow_html=True)

st.session_state.current_step = 1

# ── 页眉 ──
st.markdown("""
<div class="profile-header">
    <h2>🏢 企业档案管理与资产导入</h2>
    <p>录入企业基础信息，导入资质证书、财报及历史优秀标书，构建企业知识库</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Tab 布局
# ============================================================
tab_new, tab_list, tab_briefing = st.tabs(["📝 新建企业档案", "📂 已有企业列表", "📊 企业简报"])

# ── Tab 1: 新建企业档案 ──
with tab_new:
    st.markdown("#### 基础信息录入")
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("企业全称 *", placeholder="例：中科云数据科技有限公司")
        credit_code = st.text_input("统一社会信用代码 *", placeholder="91110000XXXXXXXXX0")
        legal_person = st.text_input("法定代表人", placeholder="张三")
        established = st.date_input("成立日期")
    with col2:
        industry = st.selectbox("所属行业", [
            "信息技术服务", "云计算与大数据", "数据中心/IDC",
            "系统集成", "软件开发", "网络安全", "智慧城市", "其他",
        ])
        registered_capital = st.text_input("注册资本", placeholder="5000 万元")
        contact_person = st.text_input("投标联系人", placeholder="李四")
        contact_phone = st.text_input("联系电话", placeholder="138xxxx0000")

    st.markdown("#### 资质与材料上传")
    col_cert, col_doc = st.columns(2)
    with col_cert:
        st.markdown("##### 📜 资质证书")
        cert_files = st.file_uploader(
            "上传资质证书 PDF",
            type=["pdf"],
            accept_multiple_files=True,
            key="cert_upload",
        )

    with col_doc:
        st.markdown("##### 📄 财报与历史标书")
        doc_files = st.file_uploader(
            "上传财务报告、历史优秀标书等",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key="doc_upload",
        )

    capabilities = st.multiselect(
        "选择企业核心能力",
        ["机房建设与租赁", "云计算 IaaS/PaaS", "数据中心运维", "信息化集成", "网络安全", "大数据/AI"],
    )

    if st.button("💾 保存档案并构建知识库", type="primary", use_container_width=True):
        if not company_name or not credit_code:
            st.error("❌ 企业全称和信用代码为必填项")
        else:
            enterprise_id = str(uuid.uuid4())[:8]
            
            with st.status("正在处理企业档案...", expanded=True) as status:
                st.write("正在保存基础信息...")
                profile = {
                    "id": enterprise_id,
                    "name": company_name,
                    "credit_code": credit_code,
                    "legal_person": legal_person,
                    "established": str(established),
                    "industry": industry,
                    "registered_capital": registered_capital,
                    "contact_person": contact_person,
                    "contact_phone": contact_phone,
                    "capabilities": capabilities,
                    "certs": [f.name for f in (cert_files or [])],
                    "docs": [f.name for f in (doc_files or [])],
                    "created_at": datetime.now().isoformat(),
                    "briefing": ""
                }
                
                # 初始化知识库
                kb = KnowledgeBase(enterprise_id)
                all_texts = []
                all_metadatas = []
                
                # 处理资质证书
                if cert_files:
                    st.write(f"正在索引 {len(cert_files)} 份资质文件...")
                    for f in cert_files:
                        text = extract_text_from_pdf(f.read())
                        all_texts.append(text)
                        all_metadatas.append({"source": f.name, "type": "cert"})
                
                # 处理文档
                if doc_files:
                    st.write(f"正在索引 {len(doc_files)} 份参考文档...")
                    for f in doc_files:
                        if f.name.endswith(".pdf"):
                            text = extract_text_from_pdf(f.read())
                            all_texts.append(text)
                            all_metadatas.append({"source": f.name, "type": "doc"})
                
                if all_texts:
                    kb.add_documents(all_texts, metadatas=all_metadatas)
                
                # 保存 Profile
                save_path = ENTERPRISE_DIR / f"{enterprise_id}.json"
                save_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
                
                st.session_state.enterprise_profile = profile
                status.update(label="✅ 档案保存与知识库构建完成！", state="complete", expanded=False)
                st.success(f"✅ 企业「{company_name}」已保存！")

# ── Tab 2: 已有企业 ──
with tab_list:
    if ENTERPRISE_DIR.exists():
        for f in sorted(ENTERPRISE_DIR.glob("*.json")):
            ent = json.loads(f.read_text(encoding="utf-8"))
            with st.expander(f"🏢 {ent['name']} (ID: {ent['id']})"):
                st.write(ent)
                if st.button(f"选择该企业", key=f"sel_{ent['id']}"):
                    st.session_state.enterprise_profile = ent
                    st.success(f"已选择：{ent['name']}")

# ── Tab 3: 企业简报 ──
with tab_briefing:
    profile = st.session_state.get("enterprise_profile")
    if not profile:
        st.warning("请先选择企业")
    else:
        st.markdown(f"### 📊 {profile['name']} 情况简报")
        if st.button("🤖 智能生成/更新简报"):
            with st.spinner("AI 正在分析企业知识库..."):
                kb = KnowledgeBase(profile['id'])
                # 检索关键资质和能力
                context = kb.search("企业资质等级、核心技术、过往大型项目案例", k=10)
                context_str = "\n".join([c['content'] for c in context])
                
                llm = get_llm()
                prompt = f"请根据以下企业知识库片段，生成一份投标维度的企业简报，包含：1.核心资质清单 2.技术实力总结 3.重点业绩。内容要真实客观。\n\n知识库内容：\n{context_str}"
                response = llm.invoke(prompt)
                profile['briefing'] = response.content
                
                # 更新文件
                save_path = ENTERPRISE_DIR / f"{profile['id']}.json"
                save_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
                st.session_state.enterprise_profile = profile
                st.rerun()
        
        if profile.get('briefing'):
            st.markdown(profile['briefing'])
