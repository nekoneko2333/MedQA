"""
侧边栏
1、显示几个功能页面切换
2、切换深色模式
3、清空对话记录
"""

import streamlit as st


def render_sidebar():
    st.markdown("### MedQA")
    sidebar_text_color = "#64748B" if not st.session_state.dark_mode else "#94A3B8"
    st.markdown(f"<div style='color:{sidebar_text_color}; font-size:0.8rem; margin-bottom:20px;'>基于知识图谱的医疗问答助手</div>", unsafe_allow_html=True)
    
    nav = st.radio(
        "导航", 
        ["智能问答", "LLM问答", "症状诊断", "知识图谱", "数据分析", "我的收藏"],
        label_visibility="collapsed"
    )
    st.session_state.current_page = nav

    st.markdown("---")
    st.caption(f"当前对话: {len(st.session_state.chat_history)} 条")
    st.caption(f"已收藏: {len(st.session_state.favorites)} 条")
    
    # 切换深色模式
    dark_mode = st.toggle("深色模式", value=st.session_state.dark_mode,
                         help="切换明暗主题")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    
    st.markdown("---")
    
    if st.button("清空所有记录", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.favorites = []
        st.session_state.answer_metadata = []  # 清空元数据
        # 清空LLM相关记录
        st.session_state.llm_chat_history = []
        st.session_state.llm_last_classify = None
        st.rerun()

