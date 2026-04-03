"""
Step 4: HITL 人机交互大厅
"""
import streamlit as st

st.set_page_config(page_title="人机交互大厅 - IT Bidding Copilot", page_icon="🤝", layout="wide")

st.markdown("""
<style>
    .hitl-header {
        background: linear-gradient(135deg, rgba(108,99,255,0.08), rgba(255,217,61,0.06));
        border: 1px solid rgba(108,99,255,0.2);
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }
    .hitl-header h2 { margin: 0 0 6px; font-size: 1.5rem; }
    .hitl-header p { color: #9CA3AF; margin: 0; }
    .outline-item {
        padding: 10px 14px;
        margin: 3px 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.15s;
        border: 1px solid transparent;
        font-size: 0.88rem;
    }
    .outline-item:hover { background: rgba(108,99,255,0.06); }
    .outline-active {
        background: rgba(108,99,255,0.1) !important;
        border-color: #6C63FF !important;
    }
    .status-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .dot-draft { background: #FFD93D; }
    .dot-confirmed { background: #4ADE80; }
    .dot-rejected { background: #FF6B6B; }
    .progress-bar-container {
        background: #1A1D23;
        border: 1px solid #2D3139;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

st.session_state.current_step = 4

# ── 页眉 ──
st.markdown("""
<div class="hitl-header">
    <h2>🤝 人机交互大厅</h2>
    <p>左侧树状大纲导航，右侧逐章审阅编辑。确认全部章节后进入循环审标</p>
</div>
""", unsafe_allow_html=True)

# ── 前置检查 ──
bid_sections = st.session_state.get("bid_sections", {})
if not bid_sections:
    st.warning("⚠️ 请先完成 Step 3 → 协作编标")
    st.stop()

section_status = st.session_state.get("section_status", {})

# ── 统计进度 ──
all_chapters = []
for sec_key, sec in bid_sections.items():
    for ch_key, ch in sec["chapters"].items():
        all_chapters.append((sec_key, ch_key, sec["title"], ch))

total = len(all_chapters)
confirmed = sum(1 for _, k, _, _ in all_chapters if section_status.get(k) == "confirmed")
rejected = sum(1 for _, k, _, _ in all_chapters if section_status.get(k) == "rejected")
drafts = total - confirmed - rejected

st.markdown(f"""
<div class="progress-bar-container">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <span style="font-weight:700;font-size:1.1rem;">📊 审阅进度</span>
            <span style="color:#9CA3AF;margin-left:12px;">{confirmed}/{total} 章节已确认</span>
        </div>
        <div>
            <span style="color:#4ADE80;">✅ {confirmed}</span> &nbsp;
            <span style="color:#FFD93D;">📝 {drafts}</span> &nbsp;
            <span style="color:#FF6B6B;">🔙 {rejected}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 双栏布局: 左侧大纲 + 右侧编辑
# ============================================================
col_outline, col_editor = st.columns([1, 3])

# 当前选中章节
if "selected_chapter" not in st.session_state:
    st.session_state.selected_chapter = all_chapters[0][1] if all_chapters else None

with col_outline:
    st.markdown("##### 📂 文档大纲")

    for sec_key, sec in bid_sections.items():
        st.markdown(f"**{sec['title']}**")
        for ch_key, ch in sec["chapters"].items():
            status = section_status.get(ch_key, "draft")
            dot_class = f"dot-{status}"
            status_label = {"draft": "待审", "confirmed": "已确认", "rejected": "已打回"}[status]

            if st.button(
                f"{'🟡' if status == 'draft' else '🟢' if status == 'confirmed' else '🔴'} {ch['title']} ({status_label})",
                key=f"nav_{ch_key}",
                use_container_width=True,
            ):
                st.session_state.selected_chapter = ch_key

        st.markdown("---")

with col_editor:
    selected = st.session_state.selected_chapter

    # 查找当前章节
    current_chapter = None
    current_section_title = ""
    for sec_key, sec in bid_sections.items():
        if selected in sec["chapters"]:
            current_chapter = sec["chapters"][selected]
            current_section_title = sec["title"]
            break

    if current_chapter:
        status = section_status.get(selected, "draft")
        status_emoji = {"draft": "📝", "confirmed": "✅", "rejected": "🔙"}[status]
        status_text = {"draft": "待审阅", "confirmed": "已确认", "rejected": "已打回，待修改"}[status]

        st.markdown(f"### {status_emoji} {current_section_title} / {current_chapter['title']}")
        st.caption(f"状态：{status_text}")

        # 编辑区域
        edited_content = st.text_area(
            "章节内容（可直接编辑修改）",
            value=current_chapter["content"],
            height=400,
            key=f"edit_{selected}",
        )

        # 补充说明
        supplement = st.text_area(
            "💬 补充说明或修改意见（可选）",
            placeholder="在此输入对该章节的补充要求或修改建议...",
            height=80,
            key=f"supplement_{selected}",
        )

        st.divider()

        # 操作按钮
        col_confirm, col_reject, col_save = st.columns(3)
        with col_confirm:
            if st.button("✅ 确认该章节", type="primary", use_container_width=True, key=f"confirm_{selected}"):
                bid_sections[current_section_title.replace("商务响应", "commercial").replace("技术与服务响应方案", "technical")
                    if False else list(bid_sections.keys())[
                        [sec["title"] for sec in bid_sections.values()].index(current_section_title)
                    ]]["chapters"][selected]["content"] = edited_content
                st.session_state.section_status[selected] = "confirmed"
                st.success(f"✅ 「{current_chapter['title']}」已确认")
                st.rerun()

        with col_reject:
            if st.button("🔙 打回重写", use_container_width=True, key=f"reject_{selected}"):
                st.session_state.section_status[selected] = "rejected"
                st.warning(f"🔙 「{current_chapter['title']}」已打回")
                st.rerun()

        with col_save:
            if st.button("💾 保存修改", use_container_width=True, key=f"save_{selected}"):
                for sec_key, sec in bid_sections.items():
                    if selected in sec["chapters"]:
                        sec["chapters"][selected]["content"] = edited_content
                        break
                st.success("💾 已保存修改")

    # 全部确认检查
    st.divider()
    all_confirmed = all(
        section_status.get(ch_key) == "confirmed"
        for _, ch_key, _, _ in all_chapters
    )

    if all_confirmed:
        st.success("🎉 全部章节已确认！可以进入循环审标。")
        if st.button("🔍 进入循环审标 →", type="primary", use_container_width=True):
            st.session_state.current_step = 5
            st.switch_page("pages/5_循环审标.py")
    else:
        st.info(f"📌 还有 {total - confirmed} 个章节待确认，请逐一审阅后才能进入审标环节。")
