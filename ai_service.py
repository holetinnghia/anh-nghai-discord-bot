import requests
import json

# Khai báo biến cần thiết
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma:2b"


def get_ai_response(prompt: str) -> str:
    """Gửi prompt đến Ollama API và trả về câu trả lời."""

    # Payload cần thiết để gọi API của Ollama
    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False  # Chờ câu trả lời hoàn chỉnh
    }

    try:
        response = requests.post(OLLAMA_URL, json=data)
        response.raise_for_status()  # Báo lỗi HTTP nếu có
        result = response.json()

        # Ollama trả về kết quả trong key 'response'
        return result.get("response", "Lỗi: Không tìm thấy phản hồi từ mô hình.")

    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối với Ollama hoặc API: {e}")
        return "Xin lỗi, server AI của tao đang bị sập rồi. Kiểm tra Ollama đi m."