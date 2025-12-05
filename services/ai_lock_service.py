import asyncio

_ai_lock = asyncio.Lock()

def is_ai_busy():
    return _ai_lock.locked()

def get_ai_lock():
    return _ai_lock