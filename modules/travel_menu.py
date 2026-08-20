import random
import streamlit as st
from utils.ai_helper import search_ai_recommendations

def render_travel_sidebar():
    selected_district = st.selectbox(
        "📍 Khu vực (Quận):",
        ["Tất cả Hà Nội", "Hoàn Kiếm & Phố Cổ", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Tây Hồ", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hoàng Mai", "Long Biên", "Hà Đông"]
    )
    selected_activity_type = st.selectbox(
        "🎭 Loại hình đi chơi / Giải trí:",
        ["Tất cả loại hình", "Cafe view đẹp / Check-in", "Công viên / Không gian xanh", "Bảo tàng / Di tích lịch sử", "Khu vui chơi / Game Center", "Phố bộ hành / Chợ đêm", "Hồ Tây / Hẹn hò lãng mạn", "Bar / Pub / Chill đêm"]
    )
    selected_companion = st.selectbox(
        "👥 Đối tượng đi cùng:",
        ["Mọi đối tượng", "Đi một mình / Yên tĩnh", "Hẹn hò cặp đôi", "Nhóm bạn đông người", "Gia đình có trẻ nhỏ"]
    )
    selected_cost = st.select_slider(
        "💰 Mức chi phí dự kiến:",
        options=["Mọi mức giá", "Miễn phí (0đ)", "Tiết kiệm (< 50k)", "Vừa phải (50k - 200k)", "Cao cấp (> 200k)"]
    )
    btn_filter_search = st.button("✨ Khám Phá Theo Bộ Lọc", use_container_width=True, type="primary")
    return selected_district, selected_activity_type, selected_companion, selected_cost, btn_filter_search


def render_travel_main(selected_district, selected_activity_type, selected_companion, selected_cost, btn_filter_search, api_key, default_model):
    st.markdown('<div class="sub-title">Khám phá địa điểm đi chơi, cafe view đẹp, khu giải trí & check-in hot nhất Hà Nội</div>', unsafe_allow_html=True)

    user_query = st.text_input(
        "Nhập địa điểm hoặc từ khóa trải nghiệm muốn tìm (Tùy chọn):",
        placeholder="Ví dụ: cafe chill Hồ Tây, bảo tàng nghệ thuật check-in, phố đi bộ đêm...",
        label_visibility="collapsed"
    )

    st.caption("💡 **Gợi ý điểm đến hot (Bấm để xem ngay):**")
    tag_cols = st.columns(5)
    quick_travel_tags = [
        "☕ Cafe chill ngắm Hồ Tây",
        "🏛️ Bốt Hàng Đậu & Phố Cổ",
        "🚲 Đạp xe Hồ Tây hoàng hôn",
        "🎨 Bảo tàng Mỹ thuật check-in",
        "🌌 Phố đi bộ Hồ Gươm đêm"
    ]
    selected_tag = None
    for i, tag in enumerate(quick_travel_tags):
        with tag_cols[i]:
            if st.button(tag, key=f"travel_tag_{i}", use_container_width=True):
                selected_tag = tag.split(" ", 1)[1]

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        btn_search = st.button("🔍 Khám Phá Địa Điểm", use_container_width=True, type="primary")
    with col_btn2:
        btn_random = st.button("🎲 Gợi Ý Bất Kỳ", use_container_width=True)

    if btn_random:
        random_travel_prompts = [
            "Quán cafe rooftop view ngắm trọn Hồ Tây hoàng hôn",
            "Bảo tàng Mỹ thuật Việt Nam kiến trúc Pháp cổ check-in đẹp",
            "Cung thiếu nhi Hà Nội mới phong cách hiện đại độc lạ",
            "Tổ hợp giải trí Complex 01 Tây Sơn không gian nghệ thuật",
            "Phố sách Hà Nội yên tĩnh đọc sách và chụp ảnh"
        ]
        user_query = random.choice(random_travel_prompts)
        st.info(f"💡 AI đang gợi ý điểm đến: **{user_query}**")
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
            filter_summary = f"Quận: {selected_district} | Loại hình: {selected_activity_type} | Chi phí: {selected_cost}"
            spinner_msg = f"🤖 AI đang tìm kiếm địa điểm đi chơi phù hợp ({filter_summary})..."
                
            with st.spinner(spinner_msg):
                results = search_ai_recommendations("travel", user_query, selected_district, selected_activity_type, selected_companion, None, selected_cost, api_key, default_model)
                if results:
                    st.session_state.travel_results = results

    if st.session_state.travel_results:
        st.markdown("---")
        st.subheader(f"✨ Gợi ý {len(st.session_state.travel_results)} địa điểm đi chơi phù hợp nhất:")
        
        for idx, item in enumerate(st.session_state.travel_results):
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1.2])
                
                with col_info:
                    st.markdown(f"### {idx+1}. {item.get('name', 'Địa điểm')} `⭐ {item.get('score', '4.7/5.0')}`")
                    st.markdown(f"📍 **Địa chỉ:** {item.get('address', 'Đang cập nhật')} *(Quận {item.get('district', '')})*")
                    st.markdown(f"🎟️ **Vé / Chi phí:** `{item.get('price_range', 'Đang cập nhật')}`")
                    st.markdown(f"🎯 **Trải nghiệm nên thử:** `{item.get('signature_activities', '')}`")
                    st.markdown(f"💬 **Review không gian:** {item.get('review_summary', '')}")
                    
                    col_p, col_c = st.columns(2)
                    with col_p:
                        st.success(f"👍 **Điểm cộng:** {item.get('pros', 'Không gian thoáng mát')}")
                    with col_c:
                        st.warning(f"⚠️ **Lưu ý:** {item.get('cons', 'Không có')}")

                with col_action:
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={item.get('name', '')}+{item.get('address', '')}".replace(" ", "+")
                    st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)
                    
                    is_saved = any(f.get('name') == item.get('name') for f in st.session_state.favorites)
                    if not is_saved:
                        if st.button("⭐ Lưu địa điểm", key=f"save_travel_{idx}", use_container_width=True):
                            st.session_state.favorites.append(item)
                            st.rerun()
                    else:
                        st.caption("✅ Đã lưu vào danh sách")
