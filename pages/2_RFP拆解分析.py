"""
Step 2: RFP 拆解与多轮核实验证
"""
import streamlit as st
import json
import time
from config import WORKFLOW_STEPS, get_llm
from utils.pdf_parser import extract_text_from_pdf
from utils.rfp_extractor import extract_rfp_requirements, cross_validate

st.set_page_config(page_title="RFP 拆解分析 - IT Bidding Copilot", page_icon="📋", layout="wide")

st.markdown("""
<style>
    .rfp-header {
        background: linear-gradient(135deg, rgba(255,107,107,0.06), rgba(108,99,255,0.08));
        border: 1px solid rgba(255,107,107,0.2);
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }
    .rfp-header h2 { margin: 0 0 6px; font-size: 1.5rem; }
    .rfp-header p { color: #9CA3AF; margin: 0; }
    .clause-card {
        background: #1A1D23;
        border-left: 4px solid;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    .clause-critical { border-color: #FF6B6B; }
    .clause-important { border-color: #FFD93D; }
    .clause-normal { border-color: #6C63FF; }
    .clause-tag {
        display: inline-block;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 600;
        margin-right: 6px;
    }
    .tag-veto { background: rgba(255,107,107,0.15); color: #FF6B6B; }
    .tag-threshold { background: rgba(255,217,61,0.15); color: #FFD93D; }
    .tag-scoring { background: rgba(108,99,255,0.15); color: #8B85FF; }
    .validation-box {
        background: rgba(0,212,170,0.06);
        border: 1px solid rgba(0,212,170,0.25);
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 16px;
    }
</style>
""", unsafe_allow_html=True)

st.session_state.current_step = 2

# ── 页眉 ──
st.markdown("""
<div class="rfp-header">
    <h2>📋 RFP 拆解与多轮核实验证</h2>
    <p>上传招标文件，系统自动提取商务资质要求、技术参数、废标条款和评分标准，并进行二次交叉核实</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Tab 布局
# ============================================================
tab_upload, tab_result, tab_validate = st.tabs(["📤 上传招标文件", "📊 提取结果", "✅ 交叉核实"])

# ── Tab 1: 上传 ──
with tab_upload:
    st.markdown("#### 上传《采购文件 / 招标文件》")
    rfp_file = st.file_uploader(
        "支持 PDF 格式的招标文件",
        type=["pdf"],
        key="rfp_upload",
        help="系统将自动解析此文件并提取关键投标要素",
    )

    if rfp_file:
        st.success(f"✅ 已上传：{rfp_file.name} ({rfp_file.size / 1024:.1f} KB)")

        if st.button("🔍 开始智能拆解", type="primary", use_container_width=True):
            with st.status("正在进行智能拆解...", expanded=True) as status:
                st.write("正在解析 PDF 文档...")
                file_bytes = rfp_file.read()
                rfp_text = extract_text_from_pdf(file_bytes)
                st.session_state.rfp_text_raw = rfp_text
                
                st.write("正在启动 AI 铁军进行需求拆解...")
                llm = get_llm()
                
                try:
                    # 调用真实提取逻辑
                    rfp_data = extract_rfp_requirements(rfp_text, llm=llm)
                    if not rfp_data:
                        raise ValueError("无法从文档中提取有效 RFP 信息")
                    st.session_state.rfp_data = rfp_data
                    st.session_state.rfp_confirmed = False
                    status.update(label="✅ RFP 拆解完成！", state="complete", expanded=False)
                    st.success("✅ RFP 拆解完成！请切换到「提取结果」标签查看详情。")
                except Exception as e:
                    st.error(f"拆解失败: {e}")
                    status.update(label="❌ 拆解失败", state="error")

# ── Tab 2: 提取结果 ──
with tab_result:
    rfp = st.session_state.get("rfp_data")
    if not rfp:
        st.warning("⚠️ 请先在「上传招标文件」标签中上传并解析文件")
    else:
        # 项目概况
        st.markdown(f"### 📌 {rfp.get('project_name', '未命名项目')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("预算金额", rfp.get("budget", "见原文"))
        c2.metric("服务期限", rfp.get("service_period", "见原文"))
        c3.metric("投标截止", rfp.get("bid_deadline", "见原文"))

        st.divider()

        # 废标条款 (最重要)
        st.markdown("#### 🚨 废标条款 (一票否决项)")
        veto_clauses = rfp.get("veto_clauses", [])
        if not veto_clauses:
            st.info("未识别到明确的废标条款")
        for clause in veto_clauses:
            st.markdown(f"""
            <div class="clause-card clause-critical">
                <span class="clause-tag tag-veto">⛔ 废标</span>
                {clause}
            </div>""", unsafe_allow_html=True)

        st.divider()

        # 商务资质要求
        st.markdown("#### 📜 商务资质要求")
        comm_reqs = rfp.get("commercial_requirements", [])
        for req in comm_reqs:
            mandatory = req.get("mandatory", True)
            level = "clause-critical" if mandatory else "clause-normal"
            tag = "tag-threshold" if mandatory else "tag-scoring"
            label = "必须" if mandatory else "加分"
            st.markdown(f"""
            <div class="clause-card {level}">
                <span class="clause-tag {tag}">{label}</span>
                【{req.get('type', '门槛')}】{req.get('item', '')}
            </div>""", unsafe_allow_html=True)

        st.divider()

        # 技术参数
        st.markdown("#### 🔧 技术/服务参数要求")
        tech_reqs = rfp.get("technical_requirements", [])
        for req in tech_reqs:
            st.markdown(f"""
            <div class="clause-card clause-important">
                <span class="clause-tag tag-threshold">📐 {req.get('category', '参数')}</span>
                {req.get('item', '')}
            </div>""", unsafe_allow_html=True)

        st.divider()

        # 评分标准
        st.markdown("#### 📊 评分标准表")
        scoring = rfp.get("scoring_criteria", [])
        for section in scoring:
            with st.expander(f"📂 {section.get('category', '评分项')}（权重 {section.get('weight', 0)}%）", expanded=True):
                for item in section.get("items", []):
                    col_name, col_score = st.columns([4, 1])
                    col_name.markdown(f"• {item.get('name', '评分维度')}")
                    col_score.markdown(f"**{item.get('score', 0)} 分**")

# ── Tab 3: 交叉核实 ──
with tab_validate:
    rfp = st.session_state.get("rfp_data")
    if not rfp:
        st.warning("⚠️ 请先完成 RFP 拆解")
    else:
        st.markdown("#### ✅ 二次交叉核实（Cross-Validation）")
        st.caption("由 AI 二审 Agent 逐条将提取结果与原文进行比对，确保核心门槛要求零遗漏、零误读")

        if st.button("🔄 启动交叉核实", type="primary", use_container_width=True):
            with st.spinner("AI 审计专家正在与原文逐条比对核实..."):
                llm = get_llm()
                validation_result = cross_validate(
                    rfp, 
                    st.session_state.get("rfp_text_raw", ""), 
                    llm=llm
                )
 
            st.markdown(f"""
            <div class="validation-box">
                <h4>✅ 交叉核实报告</h4>
                <p><b>核实状态：</b>{validation_result.get('status', 'Completed')}</p>
                <div style="background: #252A33; padding: 15px; border-radius: 8px; margin: 10px 0; font-family: monospace; white-space: pre-wrap;">
{validation_result.get('report', '未生成报告')}
                </div>
                <p><b>结论：</b>核实完成，请根据上方报告确认是否进入编标阶段。</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        st.markdown("#### 📝 人工确认")
        st.info("请仔细阅读上方提取结果和核实报告，确认无误后点击下方按钮。")

        col_confirm, col_back = st.columns([3, 1])
        with col_confirm:
            if st.button("✅ 确认 RFP 拆解结果，进入编标", type="primary", use_container_width=True):
                st.session_state.rfp_confirmed = True
                st.session_state.current_step = 3
                st.success("✅ RFP 拆解结果已确认！请进入「协作编标」步骤。")
        with col_back:
            if st.button("🔙 返回修改", use_container_width=True):
                st.session_state.rfp_confirmed = False
                st.info("请在「提取结果」标签中查看并手动修改")
