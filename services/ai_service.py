# Mày sửa lại toàn bộ file ai_service.py theo chuẩn này
from openai import AsyncOpenAI

# Link Space
HF_SPACE_URL = "https://holetinnghia-anh-nghai-ai-api.hf.space/v1"

client = AsyncOpenAI(
    base_url=HF_SPACE_URL,
    api_key="sk-khong-can-thiet"
)

async def ask_ai(question):
    try:
        response = await client.chat.completions.create(
            # THAY TÊN MODEL CHO KHỚP VỚI TÊN FILE MISTRAL VỪA TẢI
            model="mistral-7b-instruct-v0.2.Q4_K_M.gguf",

            messages=[
                # ... (System Prompt giữ nguyên)
                {"role": "user", "content": question}
            ],
            max_tokens=200,
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return "Server AI đang bị nghẽn cổ chai, đợi tao tí."