import random
import streamlit as st
from utils.ai_helper import search_ai_recommendations

def render_tour_guide_sidebar():
    selected_origin = st.selectbox(
        "📍 Nơi khởi hành (Điểm đi):",
        ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Bắc Ninh", "Khác"]
    )
    selected_duration_guide = st.selectbox(
        "⏱️ Thời gian chuyến đi:",
        ["3 ngày 2 đêm", "2 ngày 1 đêm", "1 ngày (Đi trong ngày)", "4 ngày 3 đêm", "5 ngày 4 đêm"]
    )
    selected_time_guide = st.selectbox(
        "📅 Thời điểm đi:",
        ["Tự động (Theo tháng 8 hiện tại)", "Tháng này (Thời tiết thật)", "Mùa Xuân", "Mùa Hè", "Mùa Thu", "Mùa Đông"]
    )
    selected_companion_guide = st.selectbox(
        "👥 Bạn đồng hành:",
        ["Hẹn hò cặp đôi", "Nhóm bạn trẻ / Phượt", "Gia đình / Trẻ nhỏ", "Đi một mình (Solo travel)"]
    )
    selected_budget_guide = st.select_slider(
        "💰 Ngân sách chuyến đi:",
        options=["Tiết kiệm", "Phổ thông / Tiêu chuẩn", "Sang chảnh / Resort"]
    )
    btn_filter_search = st.button("🧳 Lên Cẩm Nang Du Lịch", use_container_width=True, type="primary")
    return selected_origin, selected_duration_guide, selected_time_guide, selected_companion_guide, selected_budget_guide, btn_filter_search


def render_tour_guide_main(selected_origin, selected_duration_guide, selected_time_guide, selected_companion_guide, selected_budget_guide, btn_filter_search, api_key, default_model):
    st.markdown('<div class="sub-title">Cẩm nang du lịch trọn gói: Gợi ý Đặt xe, Top Homestay ok nhất, Outfit & Lịch trình chi tiết tiện đường</div>', unsafe_allow_html=True)

    col_loc1, col_loc2 = st.columns(2)
    with col_loc1:
        origin_input = st.text_input("📍 Điểm khởi hành (Nơi đi):", value=selected_origin)
    with col_loc2:
        dest_input = st.text_input("🎯 Điểm du lịch muốn đến (Nơi đến):", value="Sapa")

    st.caption("💡 **Gợi ý điểm đến du lịch nổi tiếng (Bấm để chọn nhanh):**")
    tag_cols = st.columns(5)
    quick_dest_tags = [
        "🏔️ Sapa",
        "🌾 Hà Giang",
        "🌊 Đà Nẵng - Hội An",
        "🌲 Đà Lạt",
        "🚣 Ninh Bình"
    ]
    selected_dest_tag = None
    for i, tag in enumerate(quick_dest_tags):
        with tag_cols[i]:
            if st.button(tag, key=f"dest_tag_{i}", use_container_width=True):
                selected_dest_tag = tag.split(" ", 1)[1]

    if selected_dest_tag:
        dest_input = selected_dest_tag
        st.info(f"💡 Đã chọn điểm đến: **{dest_input}**")

    user_query = st.text_input(
        "Nhập mong muốn chuyến đi tùy chọn (Tùy chọn):",
        placeholder="Ví dụ: săn mây Sapa, nghỉ dưỡng biển Đà Nẵng, chụp ảnh cổ phục Hội An...",
        label_visibility="collapsed"
    )

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        btn_search = st.button("🧳 Lên Cẩm Nang Du Lịch Full", use_container_width=True, type="primary")
    with col_btn2:
        btn_random = st.button("🎲 Gợi Ý Chuyến Đi Bất Kỳ", use_container_width=True)

    if btn_random:
        random_destinations = [
            ("Hà Nội", "Sapa", "Săn mây Fansipan và check-in cafe bản Cát Cát"),
            ("Hà Nội", "Hà Giang", "Phượt mạo hiểm đèo Mã Pí Lèng và ngắm dòng sông Nho Quế"),
            ("Hà Nội", "Đà Nẵng", "Nghỉ dưỡng biển Mỹ Khê và khám phá phố cổ Hội An đêm"),
            ("TP. Hồ Chí Minh", "Đà Lạt", "Chill cafe sương mờ và chụp ảnh phong cách Vintage"),
            ("Hà Nội", "Ninh Bình", "Chèo thuyền Tràng An và leo núi Múa ngắm toàn cảnh")
        ]
        chosen = random.choice(random_destinations)
        origin_input, dest_input, user_query = chosen
        st.info(f"💡 AI gợi ý chuyến đi: **{origin_input} ➔ {dest_input}** ({user_query})")
        btn_search = True

    should_search = btn_search or btn_filter_search

    if should_search:
        if not api_key:
            st.error("⚠️ Hệ thống đang bảo trì kết nối AI. Vui lòng thử lại sau!")
        else:
            spinner_msg = f"🤖 AI đang tổng hợp Cẩm Nang Du Lịch ({origin_input} ➔ {dest_input}), gợi ý Đặt xe, Homestay & Lịch trình tiện đường..."
                
            with st.spinner(spinner_msg):
                results = search_ai_recommendations(
                    "tour_guide",
                    user_query,
                    origin_input,
                    dest_input,
                    selected_duration_guide,
                    selected_time_guide,
                    f"{selected_companion_guide} - Ngân sách: {selected_budget_guide}",
                    api_key,
                    default_model
                )
                if results and isinstance(results, dict):
                    st.session_state.tour_guide_result = results

    if st.session_state.tour_guide_result:
        guide = st.session_state.tour_guide_result
        st.markdown("---")
        st.subheader(f"🧳 {guide.get('trip_title', 'Cẩm Nang Du Lịch Trọn Gói')}")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.info(f"🌤️ **Thời tiết & Khuyên dùng:** {guide.get('weather_vibe', 'Thời tiết thuận lợi')}")
        with col_g2:
            st.success(f"💰 **Chi phí dự kiến tổng cộng:** `{guide.get('estimated_total_cost', '2.000.000 - 4.000.000 VNĐ / người')}`")

        # Khung Phương tiện di chuyển & Outfit
        col_trans, col_outfit = st.columns(2)
        
        with col_trans:
            with st.container(border=True):
                st.markdown("### 🛞 Phương Tiện Di Chuyển & Gợi Ý Đặt Xe")
                trans = guide.get("transportation", {})
                st.markdown(f"🚌 **Phương tiện khuyên dùng:** `{trans.get('vehicle_type', 'Xe giường nằm / Máy bay')}`")
                st.markdown(f"🚍 **Hãng xe / Đơn vị uy tín:** `{trans.get('recommended_bus_lines', 'Các nhà xe chất lượng cao')}`")
                st.markdown(f"⏱️ **Thời gian di chuyển:** `{trans.get('travel_time', 'Đang cập nhật')}`")
                st.markdown(f"🎟️ **Giá vé ước tính:** `{trans.get('ticket_price', 'Đang cập nhật')}`")
                st.info(f"💡 **Mẹo đặt vé & xuất phát:** {trans.get('booking_tips', 'Nên đặt vé trước 3-5 ngày qua Vexere hoặc hotline nhà xe')}")

        with col_outfit:
            with st.container(border=True):
                st.markdown("### 👗 Outfit & Phối Màu Trang Phục")
                outfit = guide.get("outfit_guide", {})
                st.markdown(f"💃 **Phong cách:** `{outfit.get('style_name', 'Vintage / Năng động')}`")
                
                colors = outfit.get("recommended_colors", [])
                color_badges_html = " ".join([f'<span class="color-badge">🎨 {c}</span>' for c in colors])
                st.markdown(f"🎨 **Tone màu cực ăn ảnh:** {color_badges_html}", unsafe_allow_html=True)
                
                st.markdown(f"🧥 **Gợi ý đồ mặc:** {outfit.get('clothing_suggestions', '')}")
                st.markdown(f"🧢 **Phụ kiện cần mang:** `{outfit.get('accessories', '')}`")
                st.success(f"📸 **Mẹo chụp ảnh đẹp:** {outfit.get('photo_tips', '')}")

        # Homestay & Khách sạn gợi ý ok nhất
        st.markdown("### 🏡 Top Homestay & Khách Sạn Uy Tín / View Đẹp Nhất:")
        hs_list = guide.get("homestay_recommendations", [])
        if hs_list:
            hs_cols = st.columns(min(len(hs_list), 3))
            for h_idx, hs in enumerate(hs_list):
                with hs_cols[h_idx % len(hs_cols)]:
                    with st.container(border=True):
                        st.markdown(f"#### 🏨 {hs.get('name', 'Homestay')}")
                        st.caption(f"📍 {hs.get('address', '')}")
                        st.markdown(f"💰 **Giá phòng:** `{hs.get('price_per_night', 'Đang cập nhật')}`")
                        st.markdown(f"✨ **Điểm nổi bật:** {hs.get('highlight', '')}")
                        st.caption(f"💬 *Review:* {hs.get('review_summary', '')}")
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={hs.get('name', '')}+{hs.get('address', '')}".replace(" ", "+")
                        st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)

        # Lịch trình chi tiết từng ngày tiện đường di chuyển
        st.markdown("### 🗓️ Lịch Trình Chi Tiết Từng Ngày (Tối Ưu Tiện Đường):")
        day_list = guide.get("day_by_day_itinerary", [])
        for day_idx, day_item in enumerate(day_list):
            with st.expander(f"📌 **{day_item.get('day_title', f'Ngày {day_idx+1}')}**", expanded=True):
                activities = day_item.get("activities", [])
                for act_idx, act in enumerate(activities):
                    col_at, col_ad = st.columns([1.2, 4])
                    with col_at:
                        st.markdown(f"⏰ `{act.get('time', '')}`")
                    with col_ad:
                        st.markdown(f"### {act_idx+1}. {act.get('title', '')}")
                        st.caption(f"📍 **Địa điểm:** {act.get('location', '')}")
                        st.write(f"📝 **Trải nghiệm:** {act.get('description', '')}")
                        
                        if act.get('route_note'):
                            st.caption(f"🚏 **Đường đi tiện lợi:** {act.get('route_note')}")
                        if act.get('pro_tip'):
                            st.info(f"💡 **Mẹo local:** {act.get('pro_tip')}")
                            
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={act.get('title', '')}+{act.get('location', '')}".replace(" ", "+")
                        st.link_button("🗺️ Mở vị trí Google Maps", maps_url)
                        st.markdown("---")

        # Quán ăn & Đặc sản khuyên thử
        st.markdown("### 🍲 Quán Ăn Đặc Sản Nhất Định Phải Thử:")
        food_list = guide.get("food_recommendations", [])
        if food_list:
            food_cols = st.columns(min(len(food_list), 3))
            for f_idx, food in enumerate(food_list):
                with food_cols[f_idx % len(food_cols)]:
                    with st.container(border=True):
                        st.markdown(f"#### 🍽️ {food.get('name', 'Quán ăn')}")
                        st.caption(f"📍 {food.get('address', '')}")
                        st.markdown(f"😋 **Món ngon:** `{food.get('dishes', '')}`")
                        st.markdown(f"💰 `{food.get('price_range', '')}`")
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={food.get('name', '')}+{food.get('address', '')}".replace(" ", "+")
                        st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)
