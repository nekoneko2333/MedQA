"""
上下文管理

功能：
- 构建多轮对话的上下文信息
- 提取历史对话中的实体信息
- 维护最近提到的疾病和症状

"""

import streamlit as st

def _build_context():
    """
    从最近的对话历史中提取最近5轮的对话历史、最近提到的实体、最后提到的疾病和症状
    Returns:
        context: 包含历史对话和实体信息的字典
    """
    context = {
        'history': [],
        'last_entities': {},
        'last_disease': None,
        'last_symptom': None,
    }
    
    # 从最近的对话中提取上下文
    history = st.session_state.chat_history[-10:]  
    for msg in history:
        if msg['role'] == 'user':
            context['history'].append({'role': 'user', 'content': msg['content']})
        else:
            content = msg.get('content', '')
            if isinstance(content, str) and '<' in content:
                import re
                content = re.sub(r'<[^>]+>', '', content)
            context['history'].append({'role': 'assistant', 'content': content[:500]}) 
    
    # 提取最近提到的实体
    if 'last_classify' in st.session_state and st.session_state.last_classify:
        args = st.session_state.last_classify.get('args', {})
        for entity, types in args.items():
            if 'disease' in types:
                context['last_disease'] = entity
            if 'symptom' in types:
                context['last_symptom'] = entity
        context['last_entities'] = args
    
    return context

