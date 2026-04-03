"""
IT Bidding Copilot (IT 租赁与服务投标助手)
主入口 — Streamlit 多页面应用
"""
import streamlit as st
import json
from pathlib import Path
from config import WORKFLOW_STEPS, ENTERPRISE_DIR, DATA_DIR

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="IT Bidding Copilot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 自定义 CSS — 深色专业主题
# ============================================================
st.markdown("""
<style>
    /* 主色调 */
    :root {
        --primary: #6C63FF;
        --primary-light: #8B85FF;
        --accent: #00D4AA;
        --bg-dark: #0E1117;
        --bg-card: #1A1D23;
        --text-primary: #FAFAFA;
        --text-secondary: #9CA3AF;
        --border: #2D3139;
        --danger: #FF6B6B;
        --warning: #FFD93D;
        --success: #4ADE80;
    }

    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12141A 0%, #1A1D23 100%);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] .stMarkdown h1 {
        background: linear-gradient(135deg, #6C63FF, #00D4AA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    /* 步骤进度条 */
    .step-container {
        display: flex;
        align-items: center;
        padding: 10px 14px;
        margin: 4px 0;
        border-radius: 10px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    .step-container:hover { background: rgba(108, 99, 255, 0.08); }
    .step-active {
        background: rgba(108, 99, 255, 0.12) !important;
        border-color: var(--primary) !important;
    }
    .step-done {
        opacity: 0.7;
    }
    .step-icon {
        font-size: 1.3rem;
        margin-right: 10px;
        min-width: 28px;
        text-align: center;
    }
    .step-name {
        font-size: 0.88rem;
        font-weight: 500;
        color: var(--text-primary);
    }
    .step-badge {
        margin-left: auto;
        font-size: 0.65rem;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 600;
    }
    .badge-done { background: rgba(74,222,128,0.15); color: #4ADE80; }
    .badge-active { background: rgba(108,99,255,0.2); color: #8B85FF; }
    .badge-pending { background: rgba(156,163,175,0.1); color: #6B7280; }

    /* 主区域卡片 */
    .main-header {
        text-align: center;
        padding: 3rem 1rem 2rem;
    }
    .main-header h1 {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6C63FF 0%, #00D4AA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: var(--text-secondary);
        font-size: 1.05rem;
        max-width: 600px;
        margin: 0 auto;
    }

    /* 功能卡片 */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        padding: 1rem 0;
    }
    .feature-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 24px 20px;
        transition: all 0.25s ease;
        text-align: center;
    }
    .feature-card:hover {
        border-color: var(--primary);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(108,99,255,0.12);
    }
    .feature-card .card-icon { font-size: 2rem; margin-bottom: 10px; }
    .feature-card .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 6px;
    }
    .feature-card .card-desc {
        font-size: 0.82rem;
        color: var(--text-secondary);
        line-height: 1.5;
    }

    /* 全局按钮 */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 初始化 Session State
# ============================================================
DEFAULTS = {
    "current_step": 1,
    "enterprise_profile": None,
    "rfp_data": None,
    "rfp_confirmed": False,
    "bid_sections": {},
    "section_status": {},  # {section_key: "draft"|"confirmed"|"rejected"}
    "review_results": [],
    "review_round": 0,
    "final_approved": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def get_step_status(step_id: int) -> str:
    """返回步骤状态: done / active / pending"""
    current = st.session_state.current_step
    if step_id < current:
        return "done"
    elif step_id == current:
        return "active"
    return "pending"


def load_enterprise_list() -> list[dict]:
    """加载已保存的企业列表"""
    enterprises = []
    if ENTERPRISE_DIR.exists():
        for f in ENTERPRISE_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                enterprises.append(data)
            except Exception:
                pass
    return enterprises


# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.markdown("# 🎯 IT Bidding Copilot")
    st.caption("IT 租赁与服务投标助手 v1.0")
    st.divider()

    # 当前企业
    enterprises = load_enterprise_list()
    if enterprises:
        names = [e.get("name", "未命名") for e in enterprises]
        selected = st.selectbox(
            "🏢 当前企业",
            names,
            index=0,
            help="选择要为其投标的企业档案",
        )
        st.session_state.enterprise_profile = enterprises[names.index(selected)]
    else:
        st.info("📌 请先在「企业档案管理」中创建企业档案")

    st.divider()

    # 业务进度
    st.markdown("##### 📊 业务流程进度")
    for step in WORKFLOW_STEPS:
        status = get_step_status(step["id"])
        css_class = f"step-{status}"
        badge_class = f"badge-{status}"
        badge_text = {"done": "✓ 完成", "active": "● 进行中", "pending": "○ 待开始"}[status]

        st.markdown(f"""
        <div class="step-container {css_class}">
            <span class="step-icon">{step['icon']}</span>
            <span class="step-name">{step['name']}</span>
            <span class="step-badge {badge_class}">{badge_text}</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.caption("© 2026 IT Bidding Copilot")

# ============================================================
# 主页面 — 欢迎面板
# ============================================================
st.markdown("""
<div class="main-header">
    <h1>🎯 IT Bidding Copilot</h1>
    <p>基于多智能体协作的 IT 租赁与服务投标助手<br/>
    全流程覆盖：拆标 → 匹配素材 → 撰写 → 审标 → 封标</p>
</div>
""", unsafe_allow_html=True)

# 功能卡片
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="card-icon">🏢</div>
        <div class="card-title">企业档案管理</div>
        <div class="card-desc">一站式导入企业资质、财报与历史标书，智能生成投标维度企业简报</div>
    </div>
    <div class="feature-card">
        <div class="card-icon">📋</div>
        <div class="card-title">RFP 智能拆解</div>
        <div class="card-desc">自动提取商务门槛、废标条款与评分标准，二次交叉核实零遗漏</div>
    </div>
    <div class="feature-card">
        <div class="card-icon">✍️</div>
        <div class="card-title">AI 铁军编标</div>
        <div class="card-desc">四大 AI 专家协作，从商务响应到技术方案一气呵成</div>
    </div>
    <div class="feature-card">
        <div class="card-icon">🤝</div>
        <div class="card-title">人机交互审阅</div>
        <div class="card-desc">树状大纲 + 逐章审阅，市场人员灵活修改补充</div>
    </div>
    <div class="feature-card">
        <div class="card-icon">🔍</div>
        <div class="card-title">循环自动审标</div>
        <div class="card-desc">红脸评委严格找茬，最多三轮修改确保零废标风险</div>
    </div>
    <div class="feature-card">
        <div class="card-icon">📦</div>
        <div class="card-title">规范导出封标</div>
        <div class="card-desc">一键生成标准 Word 投标书，精准填入模板即可封装</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# 快速开始
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🚀 开始新的投标项目", use_container_width=True, type="primary"):
        st.switch_page("pages/1_企业档案管理.py")
with col2:
    if st.button("📂 继续未完成的项目", use_container_width=True):
        st.info("💡 请在左侧选择企业后，进入对应的业务步骤")
with col3:
    if st.button("📖 使用帮助", use_container_width=True):
        st.info("💡 从侧边栏点击各步骤页面，按顺序完成投标全流程")
