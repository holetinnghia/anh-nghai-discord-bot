# 🤖 Anh Nghãi Bot - AI Trợ lý Cục Súc (Discord)

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0-purple)
![AI Model](https://img.shields.io/badge/Model-Qwen%2FLLaMA-orange)

Dự án Chatbot Discord tích hợp AI (LLM), được huấn luyện (Fine-tune) để có tính cách "đàn anh IT", cục súc nhưng tốt bụng.

## 🏗 Kiến trúc Dự án (Ecosystem)

Dự án này được chia thành các module microservices:

| Thành phần | Vai trò | Trạng thái | Link Truy cập |
| :--- | :--- | :--- | :--- |
| **🤖 Bot Client** | **[REPO NÀY]** Code xử lý logic Discord, kết nối API | ✅ Active | _(Bạn đang ở đây)_ |
| **🧠 AI Brain** | Server API chạy model AI (Llama.cpp) | 🟢 Running | [👉 Hugging Face Space](https://huggingface.co/spaces/holetinnghia/anh-nghai-ai-api) |
| **📦 Model** | File trọng số đã train (`.gguf`) | 📦 Archived | [👉 Hugging Face Model](https://huggingface.co/holetinnghia/anh-nghai-ai-model) |
| **📚 Dataset** | Dữ liệu huấn luyện (`.jsonl`) | 📄 Data | [👉 Hugging Face Dataset](https://huggingface.co/datasets/holetinnghia/anh-nghai-ai-data) |