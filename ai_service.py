from openai import OpenAI, APIStatusError

# Link Space của mày
HF_SPACE_URL = "https://holetinnghia-anh-nghai-ai-api.hf.space/v1"

client = OpenAI(
    base_url=HF_SPACE_URL,
    api_key="sk-khong-can-thiet"
)


def ask_ai(question):
    print(f"--- Đang hỏi AI: {question} ---")
    try:
        response = client.chat.completions.create(
            # SỬA CHỖ NÀY: Gọi đúng tên file trên server
            model="base_model.gguf",  # <--- Thay gpt-3.5-turbo bằng cái này

            messages=[
                {"role": "system", "content": "Mày là Anh Nghãi SPKT. Trả lời ngắn gọn, cục súc."},
                {"role": "user", "content": question}
            ],
            # Bỏ max_tokens nếu muốn an toàn tuyệt đối, hoặc để 500 cũng được
            max_tokens=500
        )
        return response.choices[0].message.content

    except APIStatusError as e:
        print(f"🔥 LỖI SERVER ({e.status_code}): {e.response.text}")
        return f"Lỗi: {e.status_code}"
    except Exception as e:
        print(f"❌ Lỗi lạ: {e}")
        return "Lỗi kết nối."

if __name__ == "__main__":
    print(ask_ai("Xin chào, mày là ai?"))