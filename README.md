# 🍲 Hà Nội Food AI — Review Search Engine

Ứng dụng AI hỗ trợ tìm kiếm và tổng hợp đánh giá quán ăn tại Hà Nội dựa trên dữ liệu thời gian thực từ Google Maps, TikTok, Facebook Review & Threads thông qua **Google Gemini 2.5 Flash API**.

---

## 🚀 1. Chạy Ứng Dụng ở Môi Trường Local

### Bước 1: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 2: Tạo tệp `.env` (Tùy chọn)
Nếu không muốn nhập API Key thủ công trên giao diện Streamlit mỗi lần khởi chạy, bạn hãy tạo tệp `.env` ở thư mục gốc:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### Bước 3: Khởi chạy ứng dụng
```bash
streamlit run app.py
```
Truy cập tại địa chỉ: `http://localhost:8501`

---

## 🌐 2. Hướng Dẫn Deploy Triển Khai Online

### 🟢 Cách 1: Deploy lên Streamlit Community Cloud (Khuyên dùng - Miễn phí 100%)

1. **Đưa mã nguồn lên GitHub**:
   - Tạo một Repository mới trên GitHub (ví dụ: `hanoi-food-ai`).
   - Push toàn bộ mã nguồn của dự án lên GitHub.

2. **Kết nối và Deploy**:
   - Truy cập [share.streamlit.io](https://share.streamlit.io/) và đăng nhập bằng tài khoản GitHub.
   - Nhấn nút **"New app"**.
   - Chọn Repository, Branch (`main` hoặc `master`) và Main file path (`app.py`).

3. **Cấu hình Secret API Key (Bắt buộc nếu muốn ứng dụng tự nhận API Key cho người dùng)**:
   - Trong trang cấu hình Deploy (hoặc phần **Settings -> Secrets** của app), thêm dòng sau:
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     ```
   - Nhấn **Deploy!** Ứng dụng sẽ được khởi tạo thành công và tạo cho bạn một đường link công khai dạng `https://your-app.streamlit.app`.

---

### 🟨 Cách 2: Deploy lên Hugging Face Spaces (Miễn phí & Nhanh chóng)

1. Truy cập [huggingface.co/spaces](https://huggingface.co/spaces) và nhấn **"Create new Space"**.
2. Đặt tên Space và chọn SDK là **Streamlit**.
3. Clone repository của Space về máy hoặc upload trực tiếp các file: `app.py`, `requirements.txt`, `.streamlit/config.toml`.
4. Vào phần **Settings -> Variables and secrets** của Space:
   - Tạo một **New secret** tên `GEMINI_API_KEY` và điền giá trị API Key của bạn vào.

---

### 💙 Cách 3: Deploy qua Docker / Render / Railway / Google Cloud Run

Dự án đã chuẩn bị sẵn `Dockerfile` và `Procfile`.

#### Đóng gói & chạy với Docker:
```bash
# Build image
docker build -t hanoi-food-ai .

# Run container (truyền API Key qua môi trường)
docker run -d -p 8501:8501 -e GEMINI_API_KEY="your_api_key" --name food-ai hanoi-food-ai
```

#### Deploy lên Render.com:
1. Tạo Web Service mới trên [Render.com](https://render.com).
2. Kết nối với GitHub Repository.
3. Render sẽ tự động nhận diện `Dockerfile` hoặc `Procfile`.
4. Trong phần **Environment Variables**, thêm key `GEMINI_API_KEY`.
5. Nhấn **Create Web Service**.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
HN_foot/
├── .streamlit/
│   └── config.toml      # Cấu hình theme & server của Streamlit
├── app.py               # Mã nguồn chính của ứng dụng
├── requirements.txt     # Các thư viện Python cần thiết
├── Dockerfile           # File đóng gói container Docker
├── .dockerignore        # Bỏ qua file rác khi build Docker
├── Procfile             # Cấu hình lệnh chạy cho Render / Heroku / Railway
├── .gitignore           # Bỏ qua các file nhạy cảm khi push git
└── README.md            # Hướng dẫn sử dụng & triển khai
```

---

## 🔑 Cách Lấy Gemini API Key Miễn Phí
1. Truy cập [Google AI Studio](https://aistudio.google.com/).
2. Đăng nhập tài khoản Google và nhấn **"Get API Key"** -> **"Create API key"**.
3. Copy API Key và dán vào thanh cấu hình ở Sidebar ứng dụng hoặc thiết lập biến môi trường `GEMINI_API_KEY`.
# HNFoot
