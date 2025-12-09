# Sử dụng Python 3.10 bản nhẹ (slim) làm nền
FROM python:3.10-slim

# Cập nhật hệ thống và cài đặt FFmpeg + Opus + các thư viện bổ trợ
# Đây là bước quan trọng để bot hát được trên Render
RUN apt-get update && \
    apt-get install -y ffmpeg libopus0 libsodium23 gcc && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements và cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code của bro vào trong Docker
COPY . .

# --- QUAN TRỌNG ---
# Thay chữ 'main.py' bằng tên file chạy bot chính của bro
# Ví dụ: bot.py, run.py, v.v.
CMD ["python", "bot.py"]