"""
数据分析页面

- 图谱概览统计
- 疾病关联分析
- 数据覆盖率分析

"""

import streamlit as st
from streamlit_echarts import st_echarts


def render_analysis_page():

    st.markdown("### 数据统计与分析")
    
    analyzer = st.session_state.analyzer
    
    # Tab 分区
    tab1, tab2, tab3 = st.tabs(["概览","覆盖率","疾病关联查询"])
    
    with tab1:
        st.markdown("#### 知识图谱数据统计")
        
        # 获取统计数据
        stats = analyzer.get_overview_stats()
        if stats and 'error' not in stats:
            # 节点统计 - 6列
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                st.metric("疾病", f"{stats['disease_count']:,}")
            with col2:
                st.metric("症状", f"{stats['symptom_count']:,}")
            with col3:
                st.metric("药品", f"{stats['drug_count']:,}")
            with col4:
                st.metric("食物", f"{stats['food_count']:,}")
            with col5:
                st.metric("检查", f"{stats['check_count']:,}")
            with col6:
                st.metric("科室", f"{stats['department_count']:,}")
            
            st.markdown("---")
            
            # 左右两张图
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("##### 节点类型占比")
                pie_data = [
                    {"name": "疾病", "value": stats['disease_count']},
                    {"name": "症状", "value": stats['symptom_count']},
                    {"name": "药品", "value": stats['drug_count']},
                    {"name": "食物", "value": stats['food_count']},
                    {"name": "检查", "value": stats['check_count']},
                    {"name": "科室", "value": stats['department_count']},
                ]
                legend_text_color = "#E0E0E0" if st.session_state.dark_mode else "#555"
                pie_option = {
                    "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                    "legend": {
                        "bottom": 0, 
                        "textStyle": {
                            "fontSize": 11,
                            "color": legend_text_color
                        }
                    },
                    "series": [{
                        "type": "pie",
                        "radius": ["40%", "70%"],
                        "avoidLabelOverlap": True,
                        "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
                        "label": {"show": False},
                        "emphasis": {"label": {"show": True, "fontSize": 14, "fontWeight": "bold"}},
                        "data": pie_data,
                        "color": ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C"]
                    }]
                }
                st_echarts(options=pie_option, height="300px")
            
            with col_chart2:
                st.markdown("##### 关系类型分布")
                bar_data = [
                    {"name": "疾病-症状", "value": stats['rel_symptom']},
                    {"name": "疾病-药品", "value": stats['rel_drug']},
                    {"name": "疾病-食物", "value": stats['rel_food']},
                    {"name": "疾病-检查", "value": stats['rel_check']},
                ]
                axis_label_color = "#E0E0E0" if st.session_state.dark_mode else "#555"
                bar_option = {
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {
                        "type": "category", 
                        "data": [d["name"] for d in bar_data], 
                        "axisLabel": {
                            "fontSize": 11,
                            "color": axis_label_color
                        }
                    },
                    "yAxis": {
                        "type": "value",
                        "axisLabel": {
                            "color": axis_label_color
                        }
                    },
                    "series": [{
                        "type": "bar",
                        "data": [d["value"] for d in bar_data],
                        "itemStyle": {"borderRadius": [5, 5, 0, 0]},
                        "color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1, 
                                 "colorStops": [{"offset": 0, "color": "#5B7AA6"}, {"offset": 1, "color": "#8FA4C4"}]}
                    }]
                }
                st_echarts(options=bar_option, height="300px")
            
            # 关联度最高的疾病排行展示
            st.markdown("---")
            st.markdown("##### 关联度最高的疾病 TOP 10")
            top_diseases = analyzer.get_top_diseases(10)
            if top_diseases:
                for i, d in enumerate(top_diseases, 1):
                    progress = d['relation_count'] / top_diseases[0]['relation_count']
                    st.markdown(
                        f"""<div style="display:flex; align-items:center; margin-bottom:8px;">
                            <span style="width:30px; font-weight:bold; color:#5B7AA6;">{i}.</span>
                            <span style="width:150px; font-weight:500;">{d['name']}</span>
                            <div style="flex:1; background:#EEE; border-radius:10px; height:20px; margin:0 10px;">
                                <div style="width:{progress*100}%; background:linear-gradient(90deg, #5B7AA6, #8FA4C4); height:100%; border-radius:10px;"></div>
                            </div>
                            <span style="width:60px; text-align:right; color:#666;">{d['relation_count']} 条</span>
                        </div>""",
                        unsafe_allow_html=True
                    )
            
            # 疾病科室分布统计
            st.markdown("---")
            st.markdown("##### 疾病科室分布 TOP 10")
            dept_dist = analyzer.get_department_distribution()
            if dept_dist and len(dept_dist) > 0:
                for i, d in enumerate(dept_dist[:10], 1): 
                    progress = d['disease_count'] / dept_dist[0]['disease_count'] if dept_dist[0]['disease_count'] > 0 else 0
                    st.markdown(
                        f"""<div style="display:flex; align-items:center; margin-bottom:8px;">
                            <span style="width:30px; font-weight:bold; color:#5B7AA6;">{i}.</span>
                            <span style="width:150px; font-weight:500;">{d['department']}</span>
                            <div style="flex:1; background:#EEE; border-radius:10px; height:20px; margin:0 10px;">
                                <div style="width:{progress*100}%; background:linear-gradient(90deg, #5B7AA6, #8FA4C4); height:100%; border-radius:10px;"></div>
                            </div>
                            <span style="width:60px; text-align:right; color:#666;">{d['disease_count']} 种</span>
                        </div>""",
                        unsafe_allow_html=True
                    )
            else:
                st.info("暂无科室分布数据")
        else:
            st.error("无法获取统计数据，请检查数据库连接")
    
    with tab3:
        st.markdown("#### 疾病关联分析")
        st.caption("输入疾病名称，分析与其症状相似的疾病、共用药品等关联关系")
        
        disease_input = st.text_input("输入疾病名称", value="糖尿病", key="analysis_disease")
        
        if st.button("开始分析", type="primary", key="analyze_btn"):
            with st.spinner("分析中..."):
                col_sim, col_drug = st.columns(2)
                
                with col_sim:
                    st.markdown("##### 症状相似的疾病")
                    similar = analyzer.find_similar_diseases(disease_input)
                    if similar:
                        for item in similar:
                            symptoms_text = ", ".join(item['symptoms'][:3])
                            analysis_bg = "var(--card-bg)" if st.session_state.dark_mode else "#F8F9FA"
                            analysis_text = "var(--text-main)" if st.session_state.dark_mode else "#2C3E50"
                            analysis_secondary = "var(--text-secondary)" if st.session_state.dark_mode else "#666"
                            
                            st.markdown(
                                f"""<div style="background:{analysis_bg}; padding:12px; border-radius:8px; margin-bottom:8px; border-left:3px solid #3498DB;">
                                    <strong style="color:{analysis_text};">{item['disease']}</strong>
                                    <div style="color:{analysis_secondary}; font-size:0.9em; margin-top:4px;">
                                        共同症状 ({item['common_symptoms']}个): {symptoms_text}...
                                    </div>
                                </div>""",
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("未找到相似疾病")
                
                with col_drug:
                    st.markdown("##### 共用药品的疾病")
                    common_drugs = analyzer.find_common_drugs(disease_input)
                    if common_drugs:
                        for item in common_drugs:
                            drugs_text = ", ".join(item['drugs'][:3])
                            analysis_bg = "var(--card-bg)" if st.session_state.dark_mode else "#F8F9FA"
                            analysis_text = "var(--text-main)" if st.session_state.dark_mode else "#2C3E50"
                            analysis_secondary = "var(--text-secondary)" if st.session_state.dark_mode else "#666"
                            
                            st.markdown(
                                f"""<div style="background:{analysis_bg}; padding:12px; border-radius:8px; margin-bottom:8px; border-left:3px solid #2ECC71;">
                                    <strong style="color:{analysis_text};">{item['disease']}</strong>
                                    <div style="color:{analysis_secondary}; font-size:0.9em; margin-top:4px;">
                                        共用药品 ({item['common_drugs']}种): {drugs_text}
                                    </div>
                                </div>""",
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("未找到共用药品的疾病")
    
    with tab2:
        st.markdown("#### 知识图谱数据覆盖率")
        st.caption("可视化各类属性在疾病数据中的完整程度")
        
        coverage = analyzer.get_coverage_stats()
        if coverage and 'error' not in coverage:
            st.markdown(f"**共计 {coverage['total']:,} 种疾病**")
            st.markdown("---")
            
            coverage_items = [
                ("症状信息", coverage['symptom'], "#3498DB"),
                ("药品信息", coverage['drug'], "#2ECC71"),
                ("饮食信息", coverage['food'], "#F39C12"),
                ("检查项目", coverage['check'], "#9B59B6"),
                ("所属科室", coverage['department'], "#1ABC9C"),
            ]
            
            for label, data, color in coverage_items:
                rate = data['rate']
                count = data['count']
                
                # 根据覆盖率显示不同状态
                if rate >= 80:
                    status = "✅ 优秀"
                    status_color = "#2ECC71"
                elif rate >= 50:
                    status = "⚠️ 一般"
                    status_color = "#F39C12"
                else:
                    status = "❌ 待完善"
                    status_color = "#E74C3C"
                
                st.markdown(
                    f"""<div style="margin-bottom:20px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span style="font-weight:500;">{label}</span>
                            <span style="color:{status_color}; font-weight:500;">{status} ({rate}%)</span>
                        </div>
                        <div style="background:#EEE; border-radius:10px; height:24px; overflow:hidden;">
                            <div style="width:{rate}%; background:{color}; height:100%; border-radius:10px; 
                                        display:flex; align-items:center; justify-content:flex-end; padding-right:10px;">
                                <span style="color:white; font-size:0.85em; font-weight:500;">{count:,}/{coverage['total']:,}</span>
                            </div>
                        </div>
                    </div>""",
                    unsafe_allow_html=True
                )
        else:
            st.error("无法获取覆盖率数据")

