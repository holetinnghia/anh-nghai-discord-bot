import asyncio

# Tạo một "ổ khóa" duy nhất cho toàn bộ dịch vụ AI
# Khi ai đó giữ khóa này, người khác không thể có được nó.
_ai_lock = asyncio.Lock()

def is_ai_busy():
    """Kiểm tra xem AI có đang bị khóa (đang bận) hay không."""
    return _ai_lock.locked()

def get_ai_lock():
    """Lấy đối tượng khóa để sử dụng."""
    return _ai_lock