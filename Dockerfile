FROM python:3.9-slim

# 1. Cài đặt các gói cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 2. Cài đặt Server AI
RUN pip install llama-cpp-python[server]

# 3. Thiết lập User (Bắt buộc của Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# 4. Tải Model Gốc "Xịn" từ HuggingFace (Qwen 2.5 7B Q4_K_M)
# Tải trực tiếp lúc build để đỡ phải upload file 5GB
RUN wget -O base_model.gguf "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf?download=true"

# 5. Copy file Adapter của mày vào
COPY --chown=user models/anh_nghai_adapter.gguf .

# 6. Mở cổng
EXPOSE 7860

# 7. Chạy Server
# --model: Model gốc
# --lora: Adapter của mày
CMD ["python3", "-m", "llama_cpp.server", "--model", "base_model.gguf", "--lora", "anh_nghai_adapter.gguf", "--host", "0.0.0.0", "--port", "7860", "--n_ctx", "2048"]