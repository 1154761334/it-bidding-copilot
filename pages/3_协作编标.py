"""
Step 3: CrewAI 团队协作编标
"""
import streamlit as st
import time
import json
from config import get_llm
from workflows.crew_tasks import BiddingCrew

st.set_page_config(page_title="协作编标 - IT Bidding Copilot", page_icon="✍️", layout="wide")

st.markdown("""
<style>
    .crew-header {
        background: linear-gradient(135deg, rgba(0,212,170,0.06), rgba(108,99,255,0.08));
        border: 1px solid rgba(0,212,170,0.2);
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }
    .crew-header h2 { margin: 0 0 6px; font-size: 1.5rem; }
    .crew-header p { color: #9CA3AF; margin: 0; }
    .agent-card {
        background: #1A1D23;
        border: 1px solid #2D3139;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
        transition: all 0.2s;
    }
    .agent-card:hover { border-color: #6C63FF; }
    .agent-avatar { font-size: 2rem; margin-bottom: 8px; }
    .agent-name { font-weight: 700; font-size: 1rem; color: #FAFAFA; }
    .agent-role { font-size: 0.82rem; color: #9CA3AF; margin-top: 4px; }
    .agent-status {
        margin-top: 10px;
        font-size: 0.78rem;
        padding: 4px 10px;
        border-radius: 9999px;
        display: inline-block;
        font-weight: 600;
    }
    .status-idle { background: rgba(156,163,175,0.1); color: #6B7280; }
    .status-working { background: rgba(108,99,255,0.15); color: #8B85FF; }
    .status-done { background: rgba(74,222,128,0.15); color: #4ADE80; }
    .log-box {
        background: #0D1117;
        border: 1px solid #2D3139;
        border-radius: 10px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        max-height: 400px;
        overflow-y: auto;
        color: #9CA3AF;
    }
    .log-agent { color: #8B85FF; font-weight: 600; }
    .log-task { color: #00D4AA; }
    .log-output { color: #FAFAFA; }
</style>
""", unsafe_allow_html=True)

st.session_state.current_step = 3

# ── 页眉 ──
st.markdown("""
<div class="crew-header">
    <h2>✍️ CrewAI 团队协作编标</h2>
    <p>四大 AI 专家联合编制商务响应与技术方案，结合企业知识库与 RFP 定制化输出</p>
</div>
""", unsafe_allow_html=True)

# ── 前置检查 ──
rfp = st.session_state.get("rfp_data")
profile = st.session_state.get("enterprise_profile")
rfp_confirmed = st.session_state.get("rfp_confirmed", False)

if not rfp:
    st.warning("⚠️ 请先完成 Step 2 → RFP 拆解分析")
    st.stop()
if not rfp_confirmed:
    st.warning("⚠️ 请先在 Step 2 中确认 RFP 拆解结果")
    st.stop()

# ── Agent 团队展示 ──
st.markdown("#### 🤖 投标铁军阵容")
agents_info = [
    {"avatar": "🧠", "name": "需求统筹与拆标专家", "role": "Bid Analyst",
     "desc": "15 年 IT 综合项目售前咨询经验，对合同条款和评标规则极其敏感"},
    {"avatar": "📋", "name": "商务合规管家", "role": "Commercial Specialist",
     "desc": "严谨的法务与商务专家，严格依据事实匹配资质，绝不捏造"},
    {"avatar": "🏗️", "name": "首席技术主笔", "role": "Technical Architect",
     "desc": "精通 IT 架构、云服务与数据治理，行文干练反感套话"},
    {"avatar": "👁️", "name": "红脸评标组长", "role": "Chief Reviewer",
     "desc": "极其苛刻的独立评委，专职找茬确保零废标风险"},
]

cols = st.columns(4)
for i, agent in enumerate(agents_info):
    with cols[i]:
        status_key = f"agent_{i}_status"
        status = st.session_state.get(status_key, "idle")
        status_class = f"status-{status}"
        status_text = {"idle": "⏳ 待命", "working": "🔄 工作中", "done": "✅ 完成"}[status]
        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-avatar">{agent['avatar']}</div>
            <div class="agent-name">{agent['name']}</div>
            <div class="agent-role">{agent['role']}</div>
            <div style="font-size:0.78rem;color:#6B7280;margin-top:8px;">{agent['desc']}</div>
            <div class="agent-status {status_class}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── RFP 摘要 ──
with st.expander("📌 RFP 要求摘要", expanded=False):
    st.markdown(f"**项目：** {rfp.get('project_name', '未命名项目')}")
    st.markdown(f"**预算：** {rfp.get('budget')}  |  **服务期限：** {rfp.get('service_period')}")
    st.markdown(f"**废标条款：** {len(rfp.get('veto_clauses', []))} 项  |  "
                f"**商务要求：** {len(rfp.get('commercial_requirements', []))} 项  |  "
                f"**技术参数：** {len(rfp.get('technical_requirements', []))} 项")

# ── 编标执行 ──
st.markdown("#### 🚀 启动编标")
col_start, col_config = st.columns([3, 1])
with col_config:
    writing_style = st.selectbox("行文风格", ["专业严谨", "技术详实", "简洁高效"])
with col_start:
    pass

def parse_md_chapters(text: str, prefix: str) -> dict:
    """简单解析 Markdown 章节"""
    import re
    # 尝试匹配 "1. 标题", "2. 标题" 等
    chapters = {}
    lines = text.split('\n')
    current_ch = None
    current_content = []
    ch_count = 0
    
    for line in lines:
        match = re.match(r'^(\d+)\.\s*(.*)', line)
        if match:
            if current_ch:
                chapters[current_ch] = {"title": current_title, "content": '\n'.join(current_content).strip(), "status": "draft"}
            ch_count += 1
            current_ch = f"{prefix}_{ch_count}"
            current_title = match.group(2)
            current_content = []
        else:
            current_content.append(line)
            
    if current_ch:
        chapters[current_ch] = {"title": current_title, "content": '\n'.join(current_content).strip(), "status": "draft"}
    elif text.strip():
        # 如果没有识别到章节，则作为一个整体
        chapters[f"{prefix}_all"] = {"title": "完整响应内容", "content": text.strip(), "status": "draft"}
        
    return chapters

if st.button("🚀 开始 AI 协作编标", type="primary", use_container_width=True):
    log_container = st.empty()
    progress_bar = st.progress(0)
    logs = []
    
    def log_msg(agent_name, msg, color="#8B85FF"):
        logs.append(f'<span style="color:{color}">[{agent_name}]</span> <span class="log-task">{msg}</span>')
        log_container.markdown(f'<div class="log-box">{"<br/>".join(logs)}</div>', unsafe_allow_html=True)

    with st.status("AI 铁军正在协同作战...", expanded=True) as status:
        log_msg("SYSTEM", "指令已下达，AI 专家团队正在就绪...", color="#00D4AA")
        time.sleep(1)
        
        st.session_state["agent_1_status"] = "working"
        st.session_state["agent_2_status"] = "working"
        
        llm = get_llm()
        crew = BiddingCrew(llm=llm, verbose=True)
        
        # 准备数据
        rfp_requirements = json.dumps(rfp, ensure_ascii=False, indent=2)
        enterprise_info = "企业档案：\n" + (profile.get('briefing', '') if profile else "无企业背景信息")
        
        # 真实 RAG 检索
        log_msg("SYSTEM", f"正在为 {profile['name']} 检索历史投标素材...", color="#00D4AA")
        kb = KnowledgeBase(profile['id'])
        # 针对 RFP 要求进行语义检索
        query = f"项目：{rfp.get('project_name')} 关键要求：SLA, 基础设施参数, 安全合规, 运维方案"
        search_results = kb.search(query, k=8)
        knowledge_context = "### 知识库参考素材 ###\n"
        for i, res in enumerate(search_results):
            knowledge_context += f"素材{i+1} (来源:{res['metadata'].get('source')}):\n{res['content']}\n\n"
        
        try:
            log_msg("Commercial", "正在编写商务响应与资质匹配表...")
            # 真实运行 Crew
            result = crew.run_bid_writing(
                rfp_requirements=rfp_requirements,
                enterprise_info=enterprise_info,
                knowledge_context=knowledge_context
            )
            
            st.session_state["agent_1_status"] = "done"
            log_msg("Commercial", "商务响应编写完成。")
            
            log_msg("Technical", "正在编写技术与服务响应方案全章节...")
            st.session_state["agent_2_status"] = "done"
            log_msg("Technical", "技术方案编写完成。")
            
            # 自动解析结果
            comm_output = result["tasks"].get("commercial", "")
            tech_output = result["tasks"].get("technical", "")
            
            bid_sections = {
                "commercial": {
                    "title": "商务响应",
                    "chapters": parse_md_chapters(comm_output, "comm")
                },
                "technical": {
                    "title": "技术与服务响应方案",
                    "chapters": parse_md_chapters(tech_output, "tech")
                }
            }
            
            st.session_state.bid_sections = bid_sections
            # 初始化状态
            if "section_status" not in st.session_state:
                st.session_state.section_status = {}
            for s_key, section in bid_sections.items():
                for c_key in section["chapters"]:
                    st.session_state.section_status[c_key] = "draft"
            
            status.update(label="✅ 编标任务全部完成！", state="complete", expanded=False)
            st.success("✅ 编标初稿生成完成！请进入下一步「人机交互大厅」进行审阅和修改。")
            
        except Exception as e:
            st.error(f"编标过程出错: {e}")
            status.update(label="❌ 编标失败", state="error")
