import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

# 1. Lấy cấu hình
api_key = os.getenv("AI_API_KEY")
model_name = os.getenv("AI_MODEL_NAME")

# 2. Kiểm tra API Key
if not api_key:
    print("⚠️ Cảnh báo: Chưa có AI_API_KEY trong file .env")
else:
    # Cấu hình Gemini
    genai.configure(api_key=api_key)

# 3. Khởi tạo Model
# system_instruction: Là nơi mày dạy nó cách nói chuyện (ví dụ: cục súc, thân thiện, hay chửi thề...)
model = genai.GenerativeModel(
    model_name=model_name,
    system_instruction="Mày là bot Discord hỗ trợ sinh viên, nói chuyện thân thiện, dùng từ ngữ giới trẻ, xưng hô mày - tao."
)


async def ask_ai(question):
    """
    Gửi câu hỏi đến Google Gemini và nhận câu trả lời.
    """
    if not api_key:
        return "Chưa lắp não (API Key) nên không trả lời được đâu đại ca."

    try:
        # Gọi hàm tạo nội dung (bất đồng bộ)
        response = await model.generate_content_async(question)

        # Trả về text
        return response.text
    except Exception as e:
        print(f"❌ Lỗi Gemini: {e}")
        return "Đang bị Google chặn họng hoặc lỗi mạng rồi, thử lại sau nhé."