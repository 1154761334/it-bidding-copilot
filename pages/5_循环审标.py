"""
Step 5: LangGraph 自动循环审标
"""
import streamlit as st
import time
import json
from config import MAX_REVIEW_ROUNDS, get_llm
from workflows.review_graph import run_review_workflow

st.set_page_config(page_title="循环审标 - IT Bidding Copilot", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .review-header {
        background: linear-gradient(135deg, rgba(255,107,107,0.06), rgba(255,217,61,0.06));
        border: 1px solid rgba(255,107,107,0.2);
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }
    .review-header h2 { margin: 0 0 6px; font-size: 1.5rem; }
    .review-header p { color: #9CA3AF; margin: 0; }
    .round-card {
        background: #1A1D23;
        border: 1px solid #2D3139;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 12px 0;
    }
    .round-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .finding-item {
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 8px;
        font-size: 0.88rem;
    }
    .finding-critical {
        background: rgba(255,107,107,0.08);
        border-left: 3px solid #FF6B6B;
    }
    .finding-warning {
        background: rgba(255,217,61,0.08);
        border-left: 3px solid #FFD93D;
    }
    .finding-info {
        background: rgba(108,99,255,0.08);
        border-left: 3px solid #6C63FF;
    }
    .verdict-pass {
        background: rgba(74,222,128,0.1);
        border: 2px solid #4ADE80;
        border-radius: 14px;
        padding: 24px;
        text-align: center;
        margin-top: 20px;
    }
    .verdict-fail {
        background: rgba(255,107,107,0.1);
        border: 2px solid #FF6B6B;
        border-radius: 14px;
        padding: 24px;
        text-align: center;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.session_state.current_step = 5

# ── 页眉 ──
st.markdown("""
<div class="review-header">
    <h2>🔍 LangGraph 自动循环审标</h2>
    <p>红脸评标组长严格对照废标条款和评分表进行找茬式审查，最多循环 3 轮</p>
</div>
""", unsafe_allow_html=True)

# ── 前置检查 ──
bid_sections = st.session_state.get("bid_sections", {})
rfp = st.session_state.get("rfp_data")

if not bid_sections:
    st.warning("⚠️ 请先完成前序步骤（协作编标 + 人机审阅）")
    st.stop()

st.divider()

# ── 执行审标 ──
if st.button("🔍 启动 LangGraph 循环审标", type="primary", use_container_width=True):
    # 汇总投标文件内容
    full_content = ""
    for s_key, section in bid_sections.items():
        full_content += f"\n\n# {section['title']}\n"
        for c_key, chapter in section["chapters"].items():
            full_content += f"\n## {chapter['title']}\n{chapter['content']}\n"

    with st.status("LangGraph 状态机正在运行...", expanded=True) as status:
        st.write("正在准备审查上下文...")
        llm = get_llm()
        
        veto_clauses = rfp.get("veto_clauses", []) if rfp else []
        scoring_criteria = json.dumps(rfp.get("scoring_criteria", []), ensure_ascii=False) if rfp else ""
        
        st.write("正在执行循环审标 (review → decide → revise)...")
        # 真实运行 LangGraph
        review_result = run_review_workflow(
            bid_content=full_content,
            veto_clauses=veto_clauses,
            scoring_criteria=scoring_criteria,
            llm=llm
        )
        
        st.session_state.final_review_result = review_result
        st.session_state.final_approved = review_result["is_approved"]
        
        # 将最终修改后的内容写回（可选，或者保留原样让用户看差异）
        # 这里我们更新 bid_sections 以反映最终修改结果（尽管是粗略的，因为 LangGraph 修改的是全文）
        # 为了演示，我们仅更新一个标记
        
        status.update(label=f"✅ 审标流程完成！共执行 {review_result['total_rounds']} 轮。", state="complete", expanded=False)

# ── 结果展示 ──
res = st.session_state.get("final_review_result")
if res:
    st.markdown(f"### 📊 审标执行结果（共 {res['total_rounds']} 轮）")
    
    for record in res["review_history"]:
        with st.expander(f"第 {record['round']} 轮审查报告", expanded=(record['round'] == res['total_rounds'])):
            st.markdown(record["review_text"])
            if record["is_approved"]:
                st.success("✅ 本轮判定：通过")
            else:
                st.error("🔴 本轮判定：不通过，已触发自动整改")

    if res["is_approved"]:
        st.markdown(f"""
        <div class="verdict-pass">
            <div style="font-size:3rem;">✅</div>
            <div style="font-size:1.3rem;font-weight:700;margin:10px 0;">最终审标通过</div>
            <div style="color:#9CA3AF;">
                投标文件已消除核心废标风险，可以进行最终导出。
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="verdict-fail">
            <div style="font-size:3rem;">❌</div>
            <div style="font-size:1.3rem;font-weight:700;margin:10px 0;">未能在最大轮次内完全通过</div>
            <div style="color:#9CA3AF;">
                仍存在潜在风险，请进入「人机交互大厅」手动调整或查看上方审查建议。
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    if st.button("📦 进入规范导出 →", type="primary", use_container_width=True):
        st.session_state.current_step = 6
        st.switch_page("pages/6_规范导出.py")
