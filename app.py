"""
app主入口，其他渲染的函数等已经拆分到views文件夹

主要页面有：
1. 智能问答：基于知识图谱检索的医疗问答，支持多轮对话、知识推理
2、LLM问答:用RAG检索并且发送给llm，返回更有逻辑通人性的回答
2. 症状诊断：根据症状组合进行疾病诊断
3. 知识图谱：可视化疾病相关的知识图谱
4. 数据分析：知识图谱统计分析和关联分析
5. 我的收藏：收藏和管理问答记录
"""

import streamlit as st
import time
from ui.styles import inject_css
from ui.utils import show_loading_screen
from utils.app_init import _clear_nlp_cache, init_session, initialize_components
from utils.logger import setup_logging, get_logger
from views.sidebar import render_sidebar
from views.chat_page import render_chat_page
from views.llm_chat_page import render_llm_chat_page
from views.diagnosis_page import render_diagnosis_page
from views.graph_page import render_graph_page
from views.analysis_page import render_analysis_page
from views.favorites_page import render_favorites_page

# 在应用启动时初始化日志系统
setup_logging()
logger = get_logger(__name__)

# 在应用启动时清除缓存
_clear_nlp_cache()

# 加载页
st.set_page_config(
    page_title="MedQA 智能医疗问答",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    init_session()
    
    # 暗色模式的注入CSS
    st.markdown(inject_css(st.session_state.dark_mode), unsafe_allow_html=True)
    
    # 首次加载显示加载页面
    if not st.session_state.initialized and 'bot' not in st.session_state:
        show_loading_screen()
        initialize_components()
        time.sleep(0.5) 
        st.rerun()
        return
    
    # 初始化组件
    if 'bot' not in st.session_state:
        initialize_components()

    # 侧边栏
    with st.sidebar:
        render_sidebar()

    # 页面内容渲染
    current_page = st.session_state.current_page
    
    if current_page == "智能问答":
        render_chat_page()
    elif current_page == "LLM问答":
        render_llm_chat_page()
    elif current_page == "症状诊断":
        render_diagnosis_page()
    elif current_page == "知识图谱":
        render_graph_page()
    elif current_page == "数据分析":
        render_analysis_page()
    elif current_page == "我的收藏":
        render_favorites_page()


if __name__ == "__main__":
    main()
