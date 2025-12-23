"""
知识图谱可视化页面

"""

import streamlit as st


def render_graph_page():
    st.markdown("### 知识图谱可视化")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_input = st.text_input("输入疾病名称", value="高血压")
        if st.button("生成图谱", type="primary"):
             with st.spinner("从 Neo4j 读取数据中..."):
                nodes, links, categories, err = st.session_state.visualizer.get_disease_subgraph(search_input)
                if err:
                    st.error(err)
                else:
                    st.session_state.graph_data = (nodes, links, categories)
        
        if 'graph_data' in st.session_state:
            nodes, links, categories = st.session_state.graph_data
            st.session_state.visualizer.render_graph(nodes, links, categories, st.session_state.dark_mode)
    
    with col2:
        st.markdown("**图例说明**")
        legends = [
            ("🔴 疾病", "#E74C3C", "中心"),
            ("🔵 症状", "#3498DB", "左侧"),
            ("🟢 药品", "#2ECC71", "右侧"),
            ("🟠 食物", "#F39C12", "左下"),
            ("🟣 检查", "#9B59B6", "右下"),
            ("🩵 科室", "#1ABC9C", "顶部"),
        ]

        legend_bg = "var(--card-bg)" if st.session_state.dark_mode else "#F8F9FA"
        legend_text_color = "var(--text-main)" if st.session_state.dark_mode else "#333"
        legend_secondary_color = "var(--text-secondary)" if st.session_state.dark_mode else "#999"
        
        for icon_text, color, position in legends:
            st.markdown(
                f"""<div style='display:flex; align-items:center; margin-bottom:8px; padding:6px 10px; 
                               background:{legend_bg}; border-radius:6px; border-left:3px solid {color};'>
                    <span style='color:{legend_text_color}; font-weight:500;'>{icon_text}</span>
                    <span style='color:{legend_secondary_color}; font-size:0.8em; margin-left:auto;'>{position}</span>
                </div>""", 
                unsafe_allow_html=True
            )
        
        st.markdown("---")
        st.markdown("**操作提示**")
        st.caption("• 滚轮缩放图谱")
        st.caption("• 拖拽移动视图")
        st.caption("• 悬停查看详情")

