"""
症状组合诊断页面

勾选症状，进行症状-疾病的neo4j查询

"""
import streamlit as st

def render_diagnosis_page():
    st.markdown("### 症状组合诊断")
    st.markdown("请选择或输入症状，分析关联疾病。")

    if 'selected_symptoms' not in st.session_state:
        st.session_state.selected_symptoms = []

    def clear_all_callback():
        """处理清空所有症状的回调"""
        st.session_state.selected_symptoms = []
        # 通过清空 selected_symptoms 并让复选框在下一次渲染时读取该列表来更新选中状态。
        st.toast("🧹 已清空")

    with st.container():
        common_symptoms = st.session_state.diagnoser.get_common_symptoms()
        cols = st.columns(5)
        for i, sym in enumerate(common_symptoms[:20]): 
            with cols[i % 5]:
                is_selected = sym in st.session_state.selected_symptoms
                checkbox_key = f"check_{sym}"
                # 使用 selected_symptoms 控制复选框的初始选中状态，避免在小部件实例化后直接修改 session_state[key]
                checked = st.checkbox(sym, key=checkbox_key, value=(sym in st.session_state.selected_symptoms))
                if checked and not is_selected:
                    st.session_state.selected_symptoms.append(sym)
                    st.rerun()
                elif not checked and is_selected:
                    st.session_state.selected_symptoms.remove(sym)
                    st.rerun()

        # 提交后自动清空输入框
        with st.form(key="add_symptom_form", clear_on_submit=True, border=False):
            col_input, col_btn = st.columns([4, 1])
            with col_input:
                new_sym_val = st.text_input(
                    "添加其他症状", 
                    placeholder="例如：耳鸣", 
                    label_visibility="collapsed"
                )
            with col_btn:
                submitted = st.form_submit_button("➕ 添加", use_container_width=True)
        
        if submitted and new_sym_val and new_sym_val.strip():
            raw_input = new_sym_val.strip()
            final_sym = raw_input
            
            # 规范化输入的症状名称
            classifier = getattr(st.session_state.diagnoser, 'classifier', None)
            if classifier:
                expanded_text = classifier.expand_synonyms(raw_input)
                check_res = classifier.check_medical(expanded_text)
                matched_symptoms = [k for k, v in check_res.items() if 'symptom' in v]
                
                if matched_symptoms:
                    final_sym = max(matched_symptoms, key=len)
                    if final_sym != raw_input:
                        st.toast(f"💡 已将「{raw_input}」规范化为「{final_sym}」")
                else:
                    fuzzy_res = classifier.fuzzy_match(raw_input, classifier.symptom_wds)
                    if fuzzy_res:
                        best_match, score = max(fuzzy_res, key=lambda x: x[1])
                        if score >= 60:
                            final_sym = best_match
                            st.toast(f"💡 自动关联标准症状：{final_sym}")

            # 添加到症状列表
            if final_sym not in st.session_state.selected_symptoms:
                st.session_state.selected_symptoms.append(final_sym)
                st.success(f"✅ 已添加：{final_sym}")
                # 不要在小部件实例化后直接写入 st.session_state['check_<sym>']，
                # 通过 selected_symptoms 列表控制复选框初始值，随后重渲染页面以反映变化。
                st.rerun()
            else:
                st.warning(f"⚠️ 症状「{final_sym}」已存在")

        if st.session_state.selected_symptoms:
            st.divider()
            
            if st.session_state.dark_mode:
                tag_style = "background:#4A5F7A;padding:4px 12px;border-radius:16px;color:#FFFFFF;margin-right:5px;display:inline-block;margin-bottom:5px;"
            else:
                tag_style = "background:#EBF2F8;padding:4px 12px;border-radius:16px;color:#5B7AA6;margin-right:5px;display:inline-block;margin-bottom:5px;"
            
            tags_html = "".join([f"<span style='{tag_style}'>{s}</span>" for s in st.session_state.selected_symptoms])
            st.markdown(f"**已选症状：**<br>{tags_html}", unsafe_allow_html=True)
            st.markdown("") 
            
            col_action_main, col_action_clear = st.columns([5, 1])
            with col_action_main:
                run_diagnosis = st.button("🔍 开始诊断", type="primary", use_container_width=True)
            with col_action_clear:
                st.button("🗑️ 清空", use_container_width=True, on_click=clear_all_callback)

            # 诊断逻辑
            if run_diagnosis:
                with st.spinner("正在查询知识图谱..."):
                    results = st.session_state.diagnoser.diagnose(st.session_state.selected_symptoms)
                    if results:
                        st.markdown("### 诊断结果")
                        for idx, res in enumerate(results[:8], 1):
                            match_rate = res['match_rate']
                            color = "#2ecc71" if match_rate >= 80 else "#f39c12" if match_rate >= 50 else "#e74c3c"
                            matched_syms = ", ".join(res['matched_symptoms'][:5]) + ("..." if len(res['matched_symptoms']) > 5 else "")
                            
                            bg = "var(--card-bg)" if st.session_state.dark_mode else "#F8F9FA"
                            txt = "var(--text-main)" if st.session_state.dark_mode else "#2C3E50"
                            
                            st.markdown(f"""
                                <div style="background:{bg}; padding:15px; border-radius:8px; margin-bottom:12px; border-left:5px solid {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <strong style="color:{txt}; font-size:1.15em;">{idx}. {res['disease']}</strong>
                                        <span style="background:{color}; color:white; padding:2px 8px; border-radius:4px; font-size:0.85em;">匹配度 {match_rate}%</span>
                                    </div>
                                    <div style="margin-top:8px; font-size:0.95em; color:#666;">包含症状: {matched_syms}</div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.warning("🤔 未找到匹配的疾病，请尝试添加更多症状。")