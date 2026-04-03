"""
Step 6: 规范导出
"""
import streamlit as st
import time
import io
from datetime import datetime
from utils.docx_exporter import create_bid_document

st.set_page_config(page_title="规范导出 - IT Bidding Copilot", page_icon="📦", layout="wide")

st.markdown("""
<style>
    .export-header {
        background: linear-gradient(135deg, rgba(74,222,128,0.06), rgba(108,99,255,0.08));
        border: 1px solid rgba(74,222,128,0.2);
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }
    .export-header h2 { margin: 0 0 6px; font-size: 1.5rem; }
    .export-header p { color: #9CA3AF; margin: 0; }
    .doc-structure {
        background: #1A1D23;
        border: 1px solid #2D3139;
        border-radius: 12px;
        padding: 24px;
    }
    .doc-item {
        padding: 8px 12px;
        margin: 3px 0;
        border-radius: 6px;
        font-size: 0.88rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .doc-item:hover { background: rgba(108,99,255,0.06); }
    .doc-section { font-weight: 700; color: #FAFAFA; margin-top: 14px; }
    .doc-chapter { color: #9CA3AF; padding-left: 20px; }
    .export-success {
        background: rgba(74,222,128,0.08);
        border: 2px solid #4ADE80;
        border-radius: 14px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

st.session_state.current_step = 6

# ── 页眉 ──
st.markdown("""
<div class="export-header">
    <h2>📦 规范导出封标</h2>
    <p>预览最终文档结构，一键导出标准 Word 投标书</p>
</div>
""", unsafe_allow_html=True)

# ── 前置检查 ──
bid_sections = st.session_state.get("bid_sections", {})
final_approved = st.session_state.get("final_approved", False)

if not bid_sections:
    st.warning("⚠️ 请先完成前序步骤")
    st.stop()

if not final_approved:
    st.warning("⚠️ 投标文件尚未通过循环审标，请注意废标风险。建议返回 Step 5 完成审标。")

# ── Tab 布局 ──
tab_preview, tab_export, tab_checklist = st.tabs(["📄 文档预览", "📥 导出下载", "✅ 封标检查清单"])

with tab_preview:
    st.markdown("#### 📄 最终文档结构预览")
    rfp = st.session_state.get("rfp_data", {})
    project_name = rfp.get("project_name", "投标项目")
    profile = st.session_state.get("enterprise_profile", {})
    company_name = profile.get("name", "投标企业")

    st.markdown(f"""
    <div class="doc-structure">
        <div class="doc-item doc-section">📖 封面</div>
        <div class="doc-item doc-chapter">项目名称：{project_name}</div>
        <div class="doc-item doc-chapter">投标单位：{company_name}</div>
        <div class="doc-item doc-chapter">编制日期：{datetime.now().strftime('%Y年%m月%d日')}</div>
    </div>
    """, unsafe_allow_html=True)

    for sec_key, sec in bid_sections.items():
        st.markdown(f"""
        <div class="doc-structure" style="margin-top:12px;">
            <div class="doc-item doc-section">📂 {sec['title']}</div>
        </div>
        """, unsafe_allow_html=True)
        for ch_key, ch in sec.get("chapters", {}).items():
            with st.expander(f"  📝 {ch['title']}", expanded=False):
                st.markdown(ch["content"])

with tab_export:
    st.markdown("#### 📥 导出投标书")
    col1, col2 = st.columns(2)
    with col1:
        template_name = st.selectbox("选择导出风格", ["标准商务风格", "政企公文风格", "简约风格"])
    
    if st.button("📥 生成并导出 Word 文档", type="primary", use_container_width=True):
        with st.status("正在编排文档格式...", expanded=True) as status:
            st.write("正在准备封面...")
            time.sleep(0.5)
            st.write("正在填充响应章节...")
            
            try:
                # 调用核心导出工具
                buffer = create_bid_document(
                    project_name=project_name,
                    company_name=company_name,
                    sections=bid_sections
                )
                
                st.session_state.export_ready = True
                st.session_state.export_buffer = buffer
                status.update(label="✅ 导出成功！", state="complete", expanded=False)
            except Exception as e:
                st.error(f"导出失败: {e}")
                status.update(label="❌ 导出失败", state="error")
                
    if st.session_state.get("export_ready"):
        st.markdown("""
        <div class="export-success">
            <div style="font-size:3rem;">📄</div>
            <div style="font-size:1.3rem;font-weight:700;margin:10px 0;">投标书准备就绪！</div>
            <div style="color:#9CA3AF;">请点击下方按钮保存到本地</div>
        </div>
        """, unsafe_allow_html=True)
        
        filename = f"投标书_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
        st.download_button(
            label="📥 下载投标书 Word 文件",
            data=st.session_state.export_buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )

with tab_checklist:
    st.markdown("#### ✅ 封标前检查清单")
    checklist_items = ["投标文件是否已签章", "投标保证金是否已缴纳", "法人授权书是否齐全", "电子版是否备份", "附件清单核对无误"]
    for i, item in enumerate(checklist_items):
        st.checkbox(item, key=f"checklist_{i}")
