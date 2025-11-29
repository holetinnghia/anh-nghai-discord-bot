from mlx_lm import load, generate

# LƯU Ý: Phải dùng đúng tên model mày đã để trong file lora_config.yaml
# Lúc nãy tao bảo mày đổi sang Qwen, nên ở đây cũng phải là Qwen
model_name = "mlx-community/Qwen2.5-7B-Instruct-4bit"

print(f"Loading model: {model_name}")
print("Loading adapter...")

model, tokenizer = load(
    model_name,
    adapter_path="adapters" # Thư mục chứa kết quả train
)

# Test thử
prompt = "User: Mày tên gì?\nAssistant:"
print(f"Generating for prompt: {prompt}")

response = generate(
    model,
    tokenizer,
    prompt=prompt,
    verbose=True,
    max_tokens=100
)