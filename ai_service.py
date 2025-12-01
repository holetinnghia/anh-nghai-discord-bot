from openai import AsyncOpenAI, APIStatusError # <--- Dùng AsyncOpenAI

# Link Space
HF_SPACE_URL = "https://holetinnghia-anh-nghai-ai-api.hf.space/v1"

# Khởi tạo Client Async
client = AsyncOpenAI(
    base_url=HF_SPACE_URL,
    api_key="sk-khong-can-thiet"
)

# Thêm 'async' vào trước def
async def ask_ai(question):
    print(f"--- Đang hỏi AI: {question} ---")
    try:
        # Thêm 'await' vào trước client.chat...
        response = await client.chat.completions.create(
            model="./base_model.gguf",
            messages=[
                {"role": "system", "content": "Mày là Anh Nghãi SPKT. Cục súc, ngắn gọn."},
                # FEW-SHOT mẫu (giữ nguyên như cũ của mày)
                {"role": "user", "content": "Chào anh"},
                {"role": "assistant", "content": "Chào cái đéo gì. Có việc gì nói lẹ đi."},
                {"role": "user", "content": question}
            ],
            max_tokens=500,
            temperature=0.8
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return "Lỗi rồi, tao đang bận."