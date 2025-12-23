"""
我的收藏页面

可以收藏或删除聊天的回复

"""

import streamlit as st


def render_favorites_page():
    st.markdown("### 对话收藏夹")
    if not st.session_state.favorites:
        st.info("暂无收藏，请在对话界面点击星标收藏回答。")
    else:
        for i, item in enumerate(st.session_state.favorites):
            with st.expander(f"收藏记录 {i+1} - {item['time']}"):
                st.markdown(item['a'], unsafe_allow_html=True)
                if st.button("删除", key=f"del_fav_{i}"):
                    st.session_state.favorites.pop(i)
                    st.rerun()

