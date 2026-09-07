"""后端接口冒烟测试：登录 → 建想法 → 列表 → 切换 → 删除 → 登出。"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(method, path, body=None, cookie=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None), r.headers.get("Set-Cookie")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw), None
        except Exception:
            return e.code, raw, None


print("1) health:", call("GET", "/api/health")[1])

# 未登录访问 ideas 应 401
code, body, _ = call("GET", "/api/ideas")
print(f"2) 未登录访问 ideas -> {code} (期望 401)")

# 错误密码应 401
code, body, _ = call("POST", "/api/auth/login", {"username": "Y", "password": "bad"})
print(f"3) 错误密码 -> {code} (期望 401)")

# 正确登录
code, body, cookie = call("POST", "/api/auth/login", {"username": "Y", "password": "1"})
print(f"4) 正确登录 -> {code}, cookie={'有' if cookie else '无'}")
sess = cookie.split(";")[0] if cookie else ""

# 建想法
code, created, _ = call("POST", "/api/ideas", {"content": "迁移冒烟测试"}, sess)
print(f"5) 创建想法 -> {code}, id={created.get('id') if isinstance(created, dict) else created}")
idea_id = created.get("id") if isinstance(created, dict) else None

# 列表
code, lst, _ = call("GET", "/api/ideas", cookie=sess)
print(f"6) 列表 -> {code}, 共 {len(lst) if isinstance(lst, list) else 0} 条")

# 切换完成
code, tg, _ = call("PATCH", f"/api/ideas/{idea_id}", None, sess)
print(f"7) 切换完成 -> {code}, {tg}")

# 删除
code, dl, _ = call("DELETE", f"/api/ideas/{idea_id}", None, sess)
print(f"8) 删除 -> {code}, {dl}")

# 登出
code, lo, _ = call("POST", "/api/auth/logout", None, sess)
print(f"9) 登出 -> {code}")
