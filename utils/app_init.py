"""
应用初始化

清除NLP模块缓存
初始化会话状态和核心组件

"""

import sys
import streamlit as st
from utils.logger import get_logger
from core.chatbot import MedicalChatBot
from core.diagnoser import SymptomDiagnoser
from core.analyzer import KnowledgeGraphAnalyzer
from core.visualizer import KnowledgeGraphVisualizer
from advanced.knowledge_reasoner import KnowledgeReasoner

logger = get_logger(__name__)

def _clear_nlp_cache():
    """
    清除NLP相关模块的缓存
    """
    modules_to_remove = []
    for module_name in sys.modules.keys():
        if 'nlp' in module_name or 'question_classifier' in module_name:
            modules_to_remove.append(module_name)
    
    for module_name in modules_to_remove:
        try:
            del sys.modules[module_name]
        except:
            pass


def init_session():
    """
    初始化会话状态变量
    包括：对话历史、收藏、页面状态、功能开关等
    """
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "智能问答"
    if 'selected_symptoms' not in st.session_state:
        st.session_state.selected_symptoms = []
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    if 'last_answer_metadata' not in st.session_state:
        st.session_state.last_answer_metadata = {}
    if 'answer_metadata' not in st.session_state:
        st.session_state.answer_metadata = [] 
    if 'llm_chat_history' not in st.session_state:
        st.session_state.llm_chat_history = []  
    if 'pending_llm_question' not in st.session_state:
        st.session_state.pending_llm_question = None  
    if 'llm_last_classify' not in st.session_state:
        st.session_state.llm_last_classify = None  


def initialize_components():
    """
    初始化所有核心组件
    包括：聊天机器人、症状诊断、图谱可视化、数据分析等
    """
    if 'bot' not in st.session_state:
        st.session_state.bot = MedicalChatBot()
        st.session_state.diagnoser = SymptomDiagnoser()
        st.session_state.visualizer = KnowledgeGraphVisualizer()
        st.session_state.analyzer = KnowledgeGraphAnalyzer()
        st.session_state.reasoner = KnowledgeReasoner()
        st.session_state.initialized = True

