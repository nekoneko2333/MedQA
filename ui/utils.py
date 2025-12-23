"""
UI工具函数

- 将长文本转换为结构化的HTML
- 显示应用加载动画
- 渲染答案

"""

import streamlit as st
import re


def format_long_text(text):
    """
    将长文本转换为漂亮的 HTML
    """
    if not text:
        return ""
    
    html_output = '<div class="med-card-text">'
    
    lines = text.split('\n')
    buffer = ""
    
    # 正则表达式模式
    # 一级标题：一、二、...
    pattern_h1 = re.compile(r'^\s*(一、|二、|三、|四、|五、|六、)(.*)')
    # 二级标题：1、 1. 
    pattern_h2 = re.compile(r'^\s*(\d+[、\.])(.*)')
    # 列表项：(1) ①
    pattern_list = re.compile(r'^\s*(\(\d+\)|①|②|③)(.*)')
    
    # 如果是一整段没有换行的长文本，先尝试根据句号或序号强制分行
    if len(lines) < 3 and len(text) > 100:
        # 在序号前强制加换行
        text = re.sub(r'(一、|二、|三、|\d+[、\.]|\(\d+\))', r'\n\1', text)
        lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 匹配一级标题
        m1 = pattern_h1.match(line)
        if m1:
            html_output += f'<div class="med-section-title">{m1.group(1)}{m1.group(2)}</div>'
            continue
            
        # 匹配二级标题 
        m2 = pattern_h2.match(line)
        if m2:
            html_output += f'<div style="margin-top:10px; font-weight:bold; color:var(--text-main, #34495E);">{m2.group(1)} {m2.group(2)}</div>'
            continue
            
        # 匹配列表项
        ml = pattern_list.match(line)
        if ml:
            # 提取内容，如果有冒号，冒号前加粗
            content = ml.group(2)
            if "：" in content:
                parts = content.split("：", 1)
                content = f'<span class="med-highlight">{parts[0]}：</span>{parts[1]}'
            elif ":" in content:
                parts = content.split(":", 1)
                content = f'<span class="med-highlight">{parts[0]}：</span>{parts[1]}'
            
            html_output += f'<div class="med-list-item" style="padding-left:10px;">• {content}</div>'
            continue
            
        # 普通文本，如果包含中文冒号，尝试处理成键值对样式
        if "：" in line and len(line) < 50:
             parts = line.split("：", 1)
             html_output += f'<div class="med-list-item"><span class="med-highlight">{parts[0]}：</span>{parts[1]}</div>'
        else:
             html_output += f'<div class="med-list-item" style="margin-bottom:5px; color:var(--text-secondary, #555);">{line}</div>'

    html_output += '</div>'
    return html_output


def show_loading_screen():
    """
    加载页面包含应用Logo、标题和加载动画
    """
    st.markdown("""
    <style>
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 60vh;
        }
        .loading-logo {
            font-size: 4rem;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
        }
        .loading-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: #5B7AA6;
            margin-bottom: 10px;
        }
        .loading-subtitle {
            font-size: 1rem;
            color: #888;
            margin-bottom: 30px;
        }
        .loading-bar {
            width: 200px;
            height: 4px;
            background: #EEE;
            border-radius: 2px;
            overflow: hidden;
        }
        .loading-bar-inner {
            width: 40%;
            height: 100%;
            background: linear-gradient(90deg, #5B7AA6, #8FA4C4);
            border-radius: 2px;
            animation: loading 1.5s infinite ease-in-out;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        @keyframes loading {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(350%); }
        }
    </style>
    <div class="loading-container">
        <div class="loading-logo">🧬</div>
        <div class="loading-title">MedQA</div>
        <div class="loading-subtitle">正在加载知识图谱...</div>
        <div class="loading-bar">
            <div class="loading-bar-inner"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)



def render_answer_with_metadata(answer_html: str, question: str, classify_result, process_info, 
                                reasoning_result=None):
    # 渲染答案内容
    st.markdown(answer_html, unsafe_allow_html=True)

