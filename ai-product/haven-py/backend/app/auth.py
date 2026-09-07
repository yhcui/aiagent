"""凭证校验与会话 Token（与迁移前的 TypeScript 实现逻辑一致）。"""
import os
import time

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "Y")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "1")
SESSION_SECRET = os.getenv("SESSION_SECRET", "haven-session-secret-2026")

SESSION_MAX_AGE = 7 * 24 * 60 * 60 * 1000  # 7 天（毫秒）
COOKIE_NAME = "session"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 天（秒）


def verify_credentials(username: str, password: str) -> bool:
    return username == AUTH_USERNAME and password == AUTH_PASSWORD


def _simple_hash(text: str) -> str:
    """与前端一致的 djb2 变体哈希，仅用于票据签名。"""
    h = 5381
    for ch in text:
        h = ((h << 5) + h) ^ ord(ch)
        h &= 0xFFFFFFFF
    # 转成 base36，对齐 JS 的 toString(36)
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if h == 0:
        return "0"
    out = ""
    while h:
        out = digits[h % 36] + out
        h //= 36
    return out


def _to_base36(n: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = ""
    while n:
        out = digits[n % 36] + out
        n //= 36
    return out


def create_token() -> str:
    """生成 时间戳.随机串.签名 形式的票据。"""
    import random
    import string

    ts = _to_base36(int(time.time() * 1000))
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    sig = _simple_hash(f"{ts}.{rand}.{SESSION_SECRET}")
    return f"{ts}.{rand}.{sig}"


def verify_token(token: str | None) -> bool:
    if not token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    ts, rand, sig = parts
    if sig != _simple_hash(f"{ts}.{rand}.{SESSION_SECRET}"):
        return False
    try:
        created = int(ts, 36)
    except ValueError:
        return False
    age = int(time.time() * 1000) - created
    return 0 < age < SESSION_MAX_AGE
