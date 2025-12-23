"""
CSS样式

深浅色css
自定义streamlit的组件，按钮侧边栏等

"""

def inject_css(dark_mode=False):
    # 深色模式开启
    if dark_mode:
        primary_color = "#6BA3E8"    
        hover_color = "#2C3E50"      
        bg_main = "#0E1117"          
        bg_sidebar = "#262730"       
        text_main = "#FFFFFF"        
        text_secondary = "#B0B0B0"  
        border_color = "#333333"    
        card_bg = "#262730"          
        input_bg = "#262730"         
        
        match_high = "#2ecc71"
        match_mid = "#f1c40f"
        match_low = "#e74c3c"
    
    # 默认为浅色配色
    else:
        primary_color = "#5B7AA6"
        hover_color = "#EBF2F8"
        bg_main = "#FFFFFF"
        bg_sidebar = "#F0F2F6"
        text_main = "#31333F"
        text_secondary = "#808495"
        border_color = "#DEE2E6"
        card_bg = "#FFFFFF"
        input_bg = "#FFFFFF"
        
        match_high = "#27ae60"
        match_mid = "#f39c12"
        match_low = "#c0392b"

    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');

    :root {{
        --primary-color: {primary_color};
        --hover-color: {hover_color};
        --text-main: {text_main};
        --bg-main: {bg_main};
        --bg-sidebar: {bg_sidebar};
        --text-secondary: {text_secondary};
        --border-color: {border_color};
        --card-bg: {card_bg};
        --input-bg: {input_bg};
    }}

    .stApp {{ 
        background-color: var(--bg-main) !important; 
        font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }}
    header[data-testid="stHeader"] {{ background-color: transparent !important; }}

    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, li, span, label, div {{
        color: var(--text-main);
    }}
    
    /* 全局圆角优化 */
    .main .block-container {{
        border-radius: 12px;
    }}

    /* 指标容器 */
    div[data-testid="metric-container"] {{
        background-color: var(--card-bg) !important;
        color: var(--text-main) !important;
        padding: 16px !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s ease !important;
    }}
    
    div[data-testid="metric-container"]:hover {{
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        transform: translateY(-1px);
    }}
    
    /* 指标数值 (大数字) */
    [data-testid="stMetricValue"] > div {{
        color: var(--text-main) !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }}
    
    /* 指标标签 (上面的小字) */
    [data-testid="stMetricLabel"] > div {{
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }}

    .streamlit-expanderHeader {{
        background-color: var(--card-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s ease !important;
    }}
    
    /* 鼠标悬停时的样式 */
    .streamlit-expanderHeader:hover {{
        background-color: var(--hover-color) !important;
        color: var(--primary-color) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }}
    
    /* 展开后的内容区域 */
    .streamlit-expanderContent {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        color: var(--text-main) !important;
        border-bottom-left-radius: 12px !important;
        border-bottom-right-radius: 12px !important;
        padding: 16px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
    }}
    
    [data-testid="stExpander"] {{
        background-color: transparent !important;
        color: var(--text-main) !important;
        margin-bottom: 12px !important;
    }}
    
    [data-testid="stExpander"] details {{
        background-color: transparent !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-color) !important;
        box-shadow: 2px 0 4px -2px rgba(0, 0, 0, 0.1) !important;
    }}
    
    .stRadio > div[role="radiogroup"] > label {{
        background-color: transparent !important;
        color: var(--text-secondary) !important;
        border: none !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
        border-radius: 12px !important;
        transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}
    
    /* 悬停状态 */
    .stRadio > div[role="radiogroup"] > label:hover {{
        background-color: var(--hover-color) !important;
        color: var(--primary-color) !important;
        transform: translateX(4px);
        box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.1) !important;
    }}
    
    /* 选中状态 */
    .stRadio > div[role="radiogroup"] > label[data-checked="true"] {{
        background-color: var(--primary-color) !important;
        color: white !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }}
    
    /* 侧边栏标题样式 */
    [data-testid="stSidebar"] h3 {{
        color: var(--text-main) !important;
        font-weight: 600 !important;
        margin-bottom: 8px !important;
    }}
    
    /* 隐藏原生 Radio 圆圈 */
    .stRadio div[role="radiogroup"] > label > div:first-child {{
        display: none !important;
    }}

    
    [data-testid="stBottom"] {{
        background-color: var(--bg-main) !important;
        background: var(--bg-main) !important;
        border-top: 1px solid var(--border-color) !important;
        padding-bottom: 20px !important;
        z-index: 99999;
        box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1), 0 -2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }}
    [data-testid="stBottom"] > div {{
        background-color: var(--bg-main) !important;
    }}
    [data-testid="stChatInputContainer"] {{
        background-color: var(--input-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 24px !important;
        color: var(--text-main) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s ease !important;
    }}
    [data-testid="stChatInputContainer"]:focus-within {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
        border-color: var(--primary-color) !important;
    }}
    [data-testid="stChatInputContainer"] textarea,
    [data-testid="stChatInputContainer"] input {{
        background-color: transparent !important;
        color: var(--text-main) !important;
        caret-color: var(--primary-color) !important;
        border-radius: 24px !important;
    }}
    [data-testid="stChatInputContainer"] textarea::placeholder {{
        color: var(--text-secondary) !important;
        opacity: 0.7 !important;
    }}
    [data-testid="stChatInputContainer"] button {{
        background-color: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        transition: all 0.2s ease !important;
    }}
    [data-testid="stChatInputContainer"] button:hover {{
        color: var(--primary-color) !important;
        transform: scale(1.1);
    }}

    /* 调整底部留白 */
    .main .block-container {{
        padding-bottom: 100px !important;
    }}
    
    
    /* 按钮 */
    button[kind="primary"] {{
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s ease !important;
    }}
    button[kind="primary"]:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
        transform: translateY(-1px);
    }}
    
    button[kind="secondary"] {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-main) !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s ease !important;
    }}
    button[kind="secondary"]:hover {{
        border-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
        background-color: var(--hover-color) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        transform: translateY(-1px);
    }}
    
    /* 普通按钮（推荐问题按钮等） */
    button:not([kind]):not([data-testid]) {{
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
    }}
    button:not([kind]):not([data-testid]):hover {{
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        transform: translateY(-1px);
    }}
    
    /* 链接 */
    a {{ 
        color: var(--primary-color) !important; 
        text-decoration: none; 
        transition: all 0.2s ease !important;
    }}
    a:hover {{ 
        text-decoration: underline; 
        color: var(--primary-color) !important;
    }}
    
    /* 质量评分标签 */
    .quality-score {{
        display: inline-flex; 
        align-items: center; 
        gap: 5px;
        padding: 6px 12px; 
        border-radius: 12px; 
        font-size: 0.85rem; 
        margin-bottom: 10px;
        font-weight: 500;
    }}
    .quality-high {{ background: rgba(16, 185, 129, 0.15); color: {match_high} !important; }}
    .quality-medium {{ background: rgba(245, 158, 11, 0.15); color: {match_mid} !important; }}
    .quality-low {{ background: rgba(239, 68, 68, 0.15); color: {match_low} !important; }}
    
    /* 聊天消息卡片 */
    [data-testid="stChatMessage"] {{
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
    }}
    
    /* 输入框和文本输入 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        border-radius: 10px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s ease !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--primary-color) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }}
    
    /* 复选框和单选按钮 */
    .stCheckbox > label,
    .stRadio > label {{
        border-radius: 8px !important;
        padding: 8px 12px !important;
        transition: all 0.2s ease !important;
    }}
    .stCheckbox > label:hover,
    .stRadio > label:hover {{
        background-color: var(--hover-color) !important;
    }}
    
    /* Tabs 标签页 */
    .stTabs [data-baseweb="tab-list"] {{
        border-radius: 12px 12px 0 0 !important;
        background-color: var(--bg-sidebar) !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0 0 !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: var(--hover-color) !important;
    }}
    
    /* 卡片和容器 */
    .element-container {{
        border-radius: 12px !important;
    }}
    
    /* 移动端适配 */
    @media (max-width: 768px) {{
        [data-testid="stSidebar"] {{ min-width: 200px !important; max-width: 200px !important; }}
    }}
</style>
"""