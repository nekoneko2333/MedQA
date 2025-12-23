"""
LLM问答页面

基于RAG和LLM的问答，使用的是deepseek的API

"""

import streamlit as st
from advanced.llm_chatbot import LLMChatBot
from utils.llm_context import build_llm_context, build_llm_entity_context, add_to_history, clear_llm_history
from core.chatbot import MedicalChatBot


def render_llm_chat_page():
    st.markdown("### LLM智能问答")
    
    # 首次进入页面初始化LLM聊天机器人
    if 'llm_bot' not in st.session_state:
        # 从环境变量或配置获取API
        import os
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        # 使用连接的neo4j数据库
        graph = None
        try:
            if 'bot' in st.session_state and hasattr(st.session_state.bot, 'searcher'):
                if hasattr(st.session_state.bot.searcher, 'g'):
                    graph = st.session_state.bot.searcher.g
        except:
            pass
        
        st.session_state.llm_bot = LLMChatBot(api_key=api_key, graph=graph)
        
        # 初始化LLM对话历史
        if 'llm_chat_history' not in st.session_state:
            st.session_state.llm_chat_history = []
    
    # API配置
    if not st.session_state.llm_bot.llm_client.is_available() or st.session_state.get('show_api_config', False):
        with st.expander("⚙️ API配置", expanded=not st.session_state.llm_bot.llm_client.is_available()):
            api_key_input = st.text_input(
                "Deepseek API密钥",
                type="password",
                value=st.session_state.llm_bot.llm_client.api_key if st.session_state.llm_bot.llm_client.api_key else "",
                help="请输入您的Deepseek API密钥，或设置环境变量DEEPSEEK_API_KEY",
                key="deepseek_api_key_input"
            )
            
            # 配置API的发送网址
            with st.expander("URL配置", expanded=False):
                base_url_input = st.text_input(
                    "API基础URL",
                    value=st.session_state.llm_bot.llm_client.base_url,
                    help="默认: https://api.deepseek.com/v1",
                    key="deepseek_base_url_input"
                )
                model_input = st.text_input(
                    "模型名称",
                    value=st.session_state.llm_bot.llm_client.model,
                    help="默认: deepseek-chat",
                    key="deepseek_model_input"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存配置", key="save_api_key", type="primary"):
                    if api_key_input:
                        import os
                        os.environ["DEEPSEEK_API_KEY"] = api_key_input
                        if base_url_input:
                            os.environ["DEEPSEEK_API_BASE_URL"] = base_url_input
                        if model_input:
                            os.environ["DEEPSEEK_MODEL"] = model_input
                        
                        # 重新初始化客户端
                        from advanced.llm_client import DeepseekClient
                        new_client = DeepseekClient(
                            api_key=api_key_input,
                            base_url=base_url_input if base_url_input else None,
                            model=model_input if model_input else None
                        )
                        st.session_state.llm_bot.llm_client = new_client
                        st.session_state.show_api_config = False
                        st.success("✅ API配置已保存")
                        st.rerun()
                    else:
                        st.error("请输入有效的API密钥")
            with col2:
                if st.button("测试连接", key="test_api_connection"):
                    if api_key_input:
                        from advanced.llm_client import DeepseekClient
                        test_client = DeepseekClient(
                            api_key=api_key_input,
                            base_url=base_url_input if base_url_input else None,
                            model=model_input if model_input else None
                        )
                        test_response = test_client.chat(
                            messages=[{"role": "user", "content": "你好"}],
                            max_tokens=50
                        )
                        if 'error' in test_response:
                            st.error(f"❌ 连接失败: {test_response.get('error', '未知错误')}")
                            if 'error_detail' in test_response:
                                st.text_area("错误详情", test_response['error_detail'], height=100, key="error_detail")
                        else:
                            st.success("✅ 连接成功！")
                            st.text(f"测试回复: {test_response.get('answer', '')[:100]}")
    
    # 显示API状态
    if st.session_state.llm_bot.llm_client.is_available():
        st.info(f"✅ API已配置 | 模型: {st.session_state.llm_bot.llm_client.model} | URL: {st.session_state.llm_bot.llm_client.base_url}")
        if st.button("重新配置API", key="reconfig_api"):
            st.session_state.show_api_config = True
            st.rerun()
    
    # 显示对话历史
    for idx, msg in enumerate(st.session_state.get('llm_chat_history', [])):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)
    
    # 处理待发送的问题
    if st.session_state.get('pending_llm_question'):
        pending = st.session_state.pending_llm_question
        st.session_state.pending_llm_question = None
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                # 构建上下文
                conversation_history = build_llm_context(max_history=10)
                entity_context = build_llm_entity_context()  # 构建实体上下文用于追问
                
                # 调用LLM聊天机器人
                answer_html, classify_result, process_info = st.session_state.llm_bot.chat(
                    question=pending,
                    context=entity_context,  # 传入实体上下文
                    conversation_history=conversation_history
                )
                
                # 保存分类结果到会话状态
                if classify_result:
                    st.session_state.llm_last_classify = classify_result
                
                # 显示上下文解析提示
                if process_info.get('context_resolved'):
                    orig = process_info['context_resolved']['original']
                    resolved = process_info['context_resolved']['resolved']
                    if orig != resolved:
                        st.caption(f"🔗 已理解追问：「{orig}」→「{resolved}」")
                
                # 保存答案
                add_to_history("assistant", answer_html)
                
                # 显示答案
                st.markdown(answer_html, unsafe_allow_html=True)
                
                # 显示检索信息
                if process_info.get('retrieved_info'):
                    with st.expander("📚 检索到的知识图谱信息"):
                        st.text(process_info['retrieved_info'])
                
                # 显示处理信息
                if process_info.get('llm_used'):
                    st.caption("✅ 已使用LLM生成回答")
                else:
                    if 'error' in process_info:
                        st.error(f"❌ LLM调用失败: {process_info.get('error', '未知错误')}")
                    else:
                        st.caption("⚠️ 使用知识图谱信息回答（LLM不可用）")
        st.rerun() 
    
    # 处理新输入的问题
    if prompt := st.chat_input("请输入您的问题..."):
        add_to_history("user", prompt)
        st.session_state.pending_llm_question = prompt
        st.rerun()  
    
    # 清空对话按钮
    if st.session_state.get('llm_chat_history'):
        if st.button("清空对话历史", key="clear_llm_history"):
            clear_llm_history()
            st.rerun()

