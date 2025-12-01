from safetensors.torch import load_file, save_file
import torch
import os
import sys

# 1. Tên file adapter sau khi train
INPUT_PATH = "adapters/adapter_model.safetensors"
# Tên file adapter sau khi sửa lỗi
OUTPUT_PATH = "adapters/adapter_model_fixed_final.safetensors"

print(f"🛠 Bắt đầu sửa đổi file: {INPUT_PATH}")

try:
    if not os.path.exists(INPUT_PATH):
        # Kiểm tra nếu chưa đổi tên checkpoint thành tên chuẩn thì báo lỗi
        raise FileNotFoundError(
            f"Không tìm thấy file chuẩn {INPUT_PATH}. Mày phải đổi tên file 0000200_adapters.safetensors thành adapter_model.safetensors trước.")

    tensors = load_file(INPUT_PATH)
    new_tensors = {}

    for k, v in tensors.items():
        new_key = k

        # 1. Rename keys: .lora_a -> .lora_A.weight
        if k.endswith(".lora_a"):
            new_key = k.replace(".lora_a", ".lora_A.weight")
            v_fixed = v.T.contiguous()  # 2. TRANSPOSE (Xoay chiều ma trận)

        elif k.endswith(".lora_b"):
            new_key = k.replace(".lora_b", ".lora_B.weight")
            v_fixed = v.T.contiguous()  # 3. TRANSPOSE (Xoay chiều ma trận)

        else:
            v_fixed = v

        new_tensors[new_key] = v_fixed

    save_file(new_tensors, OUTPUT_PATH)
    print(f"✅ Sửa lỗi thành công! File đã lưu tại: {OUTPUT_PATH}")

except Exception as e:
    print(f"❌ LỖI FATAL: {e}")
    sys.exit(1)