"""
智能问答页面

"""

import streamlit as st
import time
from utils.context import _build_context
from core.chatbot import MedicalChatBot


def render_chat_page():
    st.markdown("### 智能问答助手")
    # 显示历史消息
    for idx, msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)
            
            # 显示收藏按钮
            if msg["role"] == "assistant":
                cols = st.columns([10, 1])
                with cols[1]:
                    is_fav = any(f['a'] == msg["content"] for f in st.session_state.favorites)
                    if st.button("★" if is_fav else "☆", key=f"fav_btn_{idx}"):
                        if not is_fav:
                            # 获取上一条用户问题
                            prev_q = "历史问题"
                            if idx > 0 and st.session_state.chat_history[idx-1]["role"] == "user":
                                prev_q = st.session_state.chat_history[idx-1]["content"]
                            st.session_state.favorites.append({
                                "q": prev_q,
                                "a": msg["content"],
                                "time": time.strftime("%H:%M")
                            })
                            st.rerun()
    
    # 新输入的问题先显示问题，再生成答案
    if prompt := st.chat_input("请输入您的问题..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.rerun()
    
    # 检查是否有待处理的问题
    if st.session_state.chat_history:
        last_msg = st.session_state.chat_history[-1]
        # 如果最后一条是用户消息，说明需要生成答案
        if last_msg["role"] == "user":
            with st.chat_message("assistant"):
                with st.spinner("查询知识图谱中..."):
                    # 传入上下文进行多轮对话
                    context = _build_context()
                    answer_html, classify_result, process_info = st.session_state.bot.chat(
                        last_msg["content"], context=context
                    )
                    
                    # 检查是否有推理结果
                    reasoning_result = None
                    if process_info.get('method') == 'reasoning' and process_info.get('reasoning'):
                        reasoning_result = process_info.get('reasoning')
                    
                    # 保存答案元数据
                    st.session_state.last_answer_metadata = {
                        'classify': classify_result,
                        'reasoning': reasoning_result
                    }
                    
                    # 添加答案到历史
                    st.session_state.chat_history.append({"role": "assistant", "content": answer_html})
                    
                    # 保存分类结果用于下一轮上下文
                    if classify_result:
                        st.session_state.last_classify = classify_result
            st.rerun()

