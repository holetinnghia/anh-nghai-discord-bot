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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": question}
            ],
            # Bỏ hết max_tokens, temperature để tránh lỗi param
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