import random
import streamlit as st
from utils.ai_helper import search_ai_recommendations, get_current_hanoi_season

def render_itinerary_sidebar():
    selected_district = st.selectbox(
        "📍 Khu vực (Quận):",
        ["Tất cả Hà Nội", "Hoàn Kiếm & Phố Cổ", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Tây Hồ", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hoàng Mai", "Long Biên", "Hà Đông"]
    )
    selected_day_type = st.selectbox(
        "📅 Ngày đi chơi:",
        ["Tự động (Hôm nay)", "Ngày trong tuần (T2 - T6)", "Cuối tuần (T7 - CN / Phố đi bộ)"]
    )
    selected_duration = st.selectbox(
        "⏱️ Thời lượng chuyến đi:",
        ["Cả ngày (Sáng ➔ Tối)", "Buổi Sáng & Trưa (7h - 13h)", "Buổi Chiều & Tối (14h - 21h)", "Tối & Ăn Đêm (18h - 24h)"]
    )
    selected_season_input = st.selectbox(
        "🍂 Mùa trong năm:",
        ["Tự động (Theo mùa thật hiện tại)", "Mùa Thu Hà Nội (Đẹp nhất)", "Mùa Hè (Sôi động / Hồ Tây)", "Mùa Đông (Se lạnh / Đồ nướng lẩu)", "Mùa Xuân (Dạo phố / Chơi Tết)"]
    )
    selected_vibe_itinerary = st.selectbox(
        "🎨 Phong cách trải nghiệm:",
        ["Chill & Thư giãn", "Check-in & Sống ảo", "Ẩm thực & Food Tour", "Văn hóa & Lịch sử Phố Cổ", "Hẹn hò lãng mạn cặp đôi"]
    )
    btn_filter_search = st.button("🎲 Tạo Lịch Trình Ngẫu Nhiên", use_container_width=True, type="primary")
    return selected_district, selected_day_type, selected_duration, selected_season_input, selected_vibe_itinerary, btn_filter_search


def render_itinerary_main(selected_district, selected_day_type, selected_duration, selected_season_input, selected_vibe_itinerary, btn_filter_search, api_key, default_model):
    st.markdown('<div class="sub-title">Tự động thiết kế lịch trình đi chơi & ăn uống trọn gói ngẫu nhiên theo mùa và thời gian thực Hà Nội</div>', unsafe_allow_html=True)

    current_season_text = get_current_hanoi_season()
    st.info(f"🌿 **Thời tiết & Mùa hiện tại ở Hà Nội:** {current_season_text}")

    user_query = st.text_input(
        "Nhập mong muốn lịch trình tùy chọn (Tùy chọn):",
        placeholder="Ví dụ: lịch trình chill phố cổ ngày thu, tour ẩm thực tối thứ 7, hẹn hò ngắm hoàng hôn...",
        label_visibility="collapsed"
    )

    st.caption("💡 **Gợi ý chủ đề hot (Bấm để tạo ngay):**")
    tag_cols = st.columns(5)
    quick_itin_tags = [
        "🍂 Lịch trình Mùa Thu Phố Cổ",
        "🚲 Lịch trình Chiều Tối Hồ Tây",
        "🍜 Food Tour Bún Phở 1 Ngày",
        "📸 Check-in Sống Ảo Hà Nội",
        "🕯️ Hẹn Hò Lãng Mạn Tối CN"
    ]
    selected_tag = None
    for i, tag in enumerate(quick_itin_tags):
        with tag_cols[i]:
            if st.button(tag, key=f"itin_tag_{i}", use_container_width=True):
                selected_tag = tag.split(" ", 1)[1]

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        btn_search = st.button("🎲 Tạo Lịch Trình Ngẫu Nhiên", use_container_width=True, type="primary")
    with col_btn2:
        btn_random = st.button("✨ Đổi Chủ Đề Ngẫu Nhiên", use_container_width=True)

    if btn_random:
        random_itin_prompts = [
            "Một ngày mùa thu dạo chơi phố cổ Hà Nội và thưởng thức cafe trứng",
            "Lịch trình chiều tối chill Hồ Tây đạp xe và ngắm hoàng hôn",
            "Tour khám phá bảo tàng nghệ thuật và cafe vintage lãng mạn",
            "Hành trình săn đồ ăn đêm và trải nghiệm phố đi bộ",
            "Lịch trình hẹn hò cặp đôi ấm cúng ăn steak và ngắm thành phố"
        ]
        user_query = random.choice(random_itin_prompts)
        st.info(f"💡 AI đang lên lịch trình: **{user_query}**")
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
            spinner_msg = f"🤖 AI đang lên lịch trình tối ưu ngẫu nhiên cho bạn..."
                
            with st.spinner(spinner_msg):
                results = search_ai_recommendations("itinerary", user_query, selected_district, selected_day_type, selected_duration, selected_season_input, selected_vibe_itinerary, api_key, default_model)
                if results and isinstance(results, dict):
                    st.session_state.itinerary_result = results

    if st.session_state.itinerary_result:
        itin = st.session_state.itinerary_result
        st.markdown("---")
        st.subheader(f"🚩 {itin.get('itinerary_title', 'Lịch Trình Đi Chơi & Ăn Uống Hà Nội')}")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.info(f"🌿 **Vibe & Thời tiết:** {itin.get('season_vibe', 'Thời tiết lý tưởng')}")
        with col_m2:
            st.success(f"💰 **Ngân sách tổng dự kiến:** `{itin.get('estimated_budget', '200.000 - 500.000 VNĐ / người')}`")

        st.markdown("### 🗺️ Chi Tiết Hành Trình Từng Chặng:")
        
        timeline_list = itin.get("timeline", [])
        for step_idx, step in enumerate(timeline_list):
            with st.container(border=True):
                col_t, col_act = st.columns([1.2, 4])
                with col_t:
                    st.markdown(f"#### ⏰ `{step.get('time', '')}`")
                    st.caption(f"Chặng {step_idx+1}/{len(timeline_list)}")
                with col_act:
                    st.markdown(f"### {step_idx+1}. {step.get('activity_title', '')}")
                    st.markdown(f"📍 **Địa điểm:** {step.get('location', '')}")
                    st.markdown(f"📝 **Trải nghiệm:** {step.get('description', '')}")
                    if step.get('pro_tip'):
                        st.info(f"💡 **Mẹo local:** {step.get('pro_tip')}")
                    
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={step.get('location', '')}".replace(" ", "+")
                    st.link_button("🗺️ Mở vị trí Google Maps", maps_url)
