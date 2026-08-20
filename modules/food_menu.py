import random
import streamlit as st
from utils.ai_helper import search_ai_recommendations

def render_food_sidebar():
    selected_district = st.selectbox(
        "📍 Khu vực (Quận):",
        ["Tất cả Hà Nội", "Hoàn Kiếm & Phố Cổ", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Tây Hồ", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hoàng Mai", "Long Biên", "Hà Đông"]
    )
    selected_meal = st.selectbox(
        "⏰ Bữa ăn trong ngày:",
        ["Mọi bữa ăn", "Bữa sáng (6h - 10h)", "Bữa trưa (10h - 14h)", "Bữa xế / Ăn vặt (14h - 18h)", "Bữa tối (18h - 22h)", "Ăn đêm (Sau 22h)"]
    )
    selected_category = st.selectbox(
        "🍜 Thể loại món ăn:",
        ["Tất cả loại món", "Bún / Phở / Miến", "Lẩu / Nướng", "Ốc / Ăn vặt", "Steak / Món Âu", "Cơm / Món Việt", "Trà chanh / Cafe / Tráng miệng"]
    )
    selected_vibe = st.selectbox(
        "✨ Dịp / Phong cách:",
        ["Mọi phong cách", "Local truyền thống / Bình dân", "Hẹn hò lãng mạn / Riêng tư", "Tụ tập bạn bè / Nhậu", "Ăn đêm / Mở muộn", "Sang trọng / Fine Dining"]
    )
    selected_budget = st.select_slider(
        "💰 Mức ngân sách / người:",
        options=["Mọi mức giá", "Sinh viên (< 50k)", "Bình dân (50k - 150k)", "Khá (150k - 300k)", "Sang chảnh (> 300k)"]
    )
    btn_filter_search = st.button("✨ Khám Phá Theo Bộ Lọc", use_container_width=True, type="primary")
    return selected_district, selected_meal, selected_category, selected_vibe, selected_budget, btn_filter_search


def render_food_main(selected_district, selected_meal, selected_category, selected_vibe, selected_budget, btn_filter_search, api_key, default_model):
    st.markdown('<div class="sub-title">Khám phá các quán ăn ngon chuẩn vị theo bữa ăn, khu vực & ngân sách</div>', unsafe_allow_html=True)

    user_query = st.text_input(
        "Nhập món ăn hoặc từ khóa muốn tìm (Tùy chọn):",
        placeholder="Ví dụ: bún chả que tre nướng, phở bò sốt vang phố cổ, steak hẹn hò ấm cúng...",
        label_visibility="collapsed"
    )

    st.caption("💡 **Gợi ý món hot (Bấm để xem ngay):**")
    tag_cols = st.columns(5)
    quick_tags = [
        "🍜 Phở bò sốt vang phố cổ",
        "🧆 Bún chả que tre nướng",
        "🐚 Ốc luộc lá chanh đêm",
        "🍱 Bún đậu mắm tôm ngon",
        "🥩 Steak hẹn hò ấm cúng"
    ]
    selected_tag = None
    for i, tag in enumerate(quick_tags):
        with tag_cols[i]:
            if st.button(tag, key=f"food_tag_{i}", use_container_width=True):
                selected_tag = tag.split(" ", 1)[1]

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        btn_search = st.button("🔍 Khám Phá Quán Ăn", use_container_width=True, type="primary")
    with col_btn2:
        btn_random = st.button("🎲 Gợi Ý Bất Kỳ", use_container_width=True)

    if btn_random:
        random_prompts = [
            "Quán phở bò sốt vang nóng hổi chuẩn vị phố cổ",
            "Quán ốc luộc lá chanh nước chấm đậm đà đông khách",
            "Quán nướng vỉa hè sốt me/bơ tỏi ngon rẻ tụ tập bạn bè",
            "Bánh mì chảo đẫm pate trứng lòng đào cho bữa xế",
            "Nhà hàng pasta steak phong cách vintage ấm cúng để hẹn hò"
        ]
        user_query = random.choice(random_prompts)
        st.info(f"💡 AI đang gợi ý món: **{user_query}**")
        btn_search = True

    if selected_tag:
        user_query = selected_tag
        st.info(f"💡 Bạn đã chọn: **{user_query}**")
        btn_search = True

    should_search = btn_search or btn_filter_search

    if should_search:
        if not api_key:
            st.error("⚠️ Hệ thống đang bảo trì kết nối AI. Vui lòng thử lại sau!")
        else:
            filter_summary = f"Quận: {selected_district} | Bữa: {selected_meal} | Thể loại: {selected_category} | Giá: {selected_budget}"
            spinner_msg = f"🤖 AI đang tìm kiếm quán ăn phù hợp ({filter_summary})..."
                
            with st.spinner(spinner_msg):
                results = search_ai_recommendations("food", user_query, selected_district, selected_category, selected_meal, selected_vibe, selected_budget, api_key, default_model)
                if results:
                    st.session_state.food_results = results

    if st.session_state.food_results:
        st.markdown("---")
        st.subheader(f"✨ Gợi ý {len(st.session_state.food_results)} quán ăn phù hợp nhất:")
        
        for idx, item in enumerate(st.session_state.food_results):
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1.2])
                
                with col_info:
                    st.markdown(f"### {idx+1}. {item.get('name', 'Quán ăn')} `⭐ {item.get('score', '4.5/5.0')}`")
                    st.markdown(f"📍 **Địa chỉ:** {item.get('address', 'Đang cập nhật')} *(Quận {item.get('district', '')})*")
                    st.markdown(f"💰 **Khoảng giá:** `{item.get('price_range', 'Đang cập nhật')}`")
                    st.markdown(f"🍽️ **Món nên gọi:** `{item.get('signature_dishes', '')}`")
                    st.markdown(f"💬 **Review tổng hợp:** {item.get('review_summary', '')}")
                    
                    col_p, col_c = st.columns(2)
                    with col_p:
                        st.success(f"👍 **Điểm cộng:** {item.get('pros', 'Đồ ăn tươi ngon')}")
                    with col_c:
                        st.warning(f"⚠️ **Lưu ý:** {item.get('cons', 'Không có')}")

                with col_action:
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={item.get('name', '')}+{item.get('address', '')}".replace(" ", "+")
                    st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)
                    
                    is_saved = any(f.get('name') == item.get('name') for f in st.session_state.favorites)
                    if not is_saved:
                        if st.button("⭐ Lưu quán", key=f"save_food_{idx}", use_container_width=True):
                            st.session_state.favorites.append(item)
                            st.rerun()
                    else:
                        st.caption("✅ Đã lưu vào danh sách")
