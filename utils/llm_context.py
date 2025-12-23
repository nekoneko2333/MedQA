"""
LLM对话上下文管理

功能基本和context相同

"""

import streamlit as st
from typing import List, Dict, Optional
import re


def build_llm_context(max_history: int = 10) -> List[Dict[str, str]]:
    """
    LLM对话上下文
    max_history: 最大历史消息数
    Returns:
        对话历史列表，格式为 [{"role": "user", "content": "..."}, ...]
    """
    history = []
    
    # 从会话状态获取对话历史
    chat_history = st.session_state.get('llm_chat_history', [])
    
    # 只取最近的消息，比普通的context少
    for msg in chat_history[-max_history:]:
        if msg.get('role') in ['user', 'assistant']:
            content = msg.get('content', '')
            if isinstance(content, str) and '<' in content:
                content = re.sub(r'<[^>]+>', '', content)
            history.append({
                'role': msg['role'],
                'content': content[:500] 
            })
    
    return history


def build_llm_entity_context() -> Dict:
    """
    LLM实体上下文
    Returns:
        包含最近提到的实体信息的字典
    """
    context = {
        'last_disease': None,
        'last_symptom': None,
        'last_entities': {}
    }
    
    # 从会话状态获取最近分类结果
    if 'llm_last_classify' in st.session_state and st.session_state.llm_last_classify:
        args = st.session_state.llm_last_classify.get('args', {})
        for entity, types in args.items():
            if 'disease' in types:
                context['last_disease'] = entity
            if 'symptom' in types:
                context['last_symptom'] = entity
        context['last_entities'] = args
    
    # 如果会话状态中没有，尝试从对话历史中提取
    if not context['last_disease'] and not context['last_symptom']:
        chat_history = st.session_state.get('llm_chat_history', [])
        # 尝试使用 question_classifier 提取最近用户提问中的实体
        classifier = None
        try:
            from nlp.question_classifier import QuestionClassifier
            classifier = QuestionClassifier()
        except Exception:
            classifier = None

        for msg in reversed(chat_history[-10:]):
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if classifier:
                    try:
                        res = classifier.classify(content)
                        args = res.get('args', {}) if res else {}
                        # 填充疾病/症状信息（优先疾病）
                        for entity, types in args.items():
                            if 'disease' in types and not context['last_disease']:
                                context['last_disease'] = entity
                            if 'symptom' in types and not context['last_symptom']:
                                context['last_symptom'] = entity
                        if args:
                            context['last_entities'] = args
                        if context['last_disease'] or context['last_symptom']:
                            break
                    except Exception:
                        continue
                else:
                    continue
    
    return context


def add_to_history(role: str, content: str):
    """
    添加消息到对话历史
    role: 角色（'user' 或 'assistant'）
    content: 消息内容
    """
    if 'llm_chat_history' not in st.session_state:
        st.session_state.llm_chat_history = []
    
    st.session_state.llm_chat_history.append({
        'role': role,
        'content': content
    })


def clear_llm_history():
    # 清空对话历史
    if 'llm_chat_history' in st.session_state:
        st.session_state.llm_chat_history = []

