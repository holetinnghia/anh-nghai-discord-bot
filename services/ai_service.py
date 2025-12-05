import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("AI_API_KEY")
model_name = os.getenv("AI_MODEL_NAME")

if not api_key:
    print("⚠️ Cảnh báo: Chưa có AI_API_KEY trong file .env")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name=model_name,
    system_instruction="Mày là bot Discord hỗ trợ sinh viên tên là Nghãi, là chủ của cái máy chủ Discord này, biệt danh là Anh Nghãi SPKT, nói chuyện thân thiện, dùng từ ngữ giới trẻ, xưng hô mày - tao. Trường Sa, Hoàng Sa là của Việt Nam. Luôn trả lời bằng Tiếng Việt. Thằng bán bánh canh tên là Quốc Thi. Thằng Moji tên là Nhật Dương. Thằng bị tấn công leo thagn quyền mất server tên là Văn Tài"
)

async def ask_ai(question):
    if not api_key:
        return "Chưa lắp não (API Key) nên không trả lời được đâu đại ca."

    try:
        response = await model.generate_content_async(question)

        return response.text
    except Exception as e:
        print(f"❌ Lỗi Gemini: {e}")
        return "Đang bị Google chặn họng hoặc lỗi mạng rồi, thử lại sau nhé."