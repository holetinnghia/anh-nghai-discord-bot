import json
import os
import sys

# File config của Adapter
ADAPTER_CONFIG_PATH = "adapters/adapter_config.json"

try:
    with open(ADAPTER_CONFIG_PATH, "r") as f:
        data = json.load(f)

    # Đọc rank (r) và scale từ config gốc của MLX
    rank = data.get("r", data.get("rank", 8)) # Lấy rank, mặc định là 8
    scale = data.get("scale", 16.0)         # Lấy scale, mặc định là 16.0

    # Tính toán lora_alpha: Alpha = Scale * Rank
    lora_alpha = int(rank * scale)

    # Chèn key bị thiếu vào
    data["lora_alpha"] = lora_alpha

    with open(ADAPTER_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Sửa file config thành công! Đã chèn lora_alpha: {lora_alpha}")

except Exception as e:
    print(f"❌ LỖI FATAL: {e}")
    sys.exit(1)