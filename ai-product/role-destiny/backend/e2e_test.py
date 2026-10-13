# -*- coding: utf-8 -*-
"""端到端联调验证脚本（模拟小程序全链路）"""
import sys
import json
import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000"
OPENID = "dev_openid_001"

# 0. 创建测试用户（直接入库）
sys.path.insert(0, ".")
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
user = db.query(User).filter(User.openid == OPENID).first()
if not user:
    user = User(openid=OPENID, nickname="端到端测试官", status=1)
    db.add(user)
    db.commit()
    print("[0] 测试用户已创建:", user.openid)
else:
    print("[0] 测试用户已存在:", user.openid)
db.close()

# 1. 测试列表
r = requests.get(f"{BASE}/api/tests").json()
print("[1] 测试列表:", len(r), "个测试, question_count =", r[0]["question_count"], ", title =", r[0]["title"])

# 2. 测试详情（含题目选项）
detail = requests.get(f"{BASE}/api/tests/1").json()
qs = detail["questions"]
print("[2] 测试详情:", detail["question_count"], "道题")
assert len(qs) == 8, f"期望8题, 实际{len(qs)}"

# 3. 提交答案（每题选第一个选项）
answers = [q["options"][0]["id"] for q in qs]
r = requests.post(
    f"{BASE}/api/quiz/submit",
    json={"openid": OPENID, "test_id": 1, "answers": answers},
)
assert r.status_code == 200, f"提交失败: {r.status_code} {r.text}"
result = r.json()
print("[3] 提交结果: id =", result["id"], ", role =", result["role"]["name"],
      ", code =", result["role"]["code"], ", match =", result["match_score"],
      ", is_paid =", result["is_paid"])
assert result["full_role"] is None, "未付费不应返回完整报告"

# 4. Mock 支付
r = requests.post(
    f"{BASE}/api/payment/create",
    json={"openid": OPENID, "result_id": result["id"]},
)
assert r.status_code == 200, f"支付失败: {r.status_code} {r.text}"
pay = r.json()
print("[4] Mock 支付:", "order_no =", pay["order_no"], ", mock =", pay["mock"])
assert pay["mock"] is True, "DEBUG 模式应返回 mock=True"

# 5. 再查结果（应已解锁）
r = requests.get(f"{BASE}/api/quiz/result/{result['id']}", params={"openid": OPENID}).json()
print("[5] 解锁后结果:", "is_paid =", r["is_paid"], ", full_role 命中 =",
      bool(r["full_role"]), ", personality 片段 =", (r["full_role"] or {}).get("personality", "")[:20] + "...")
assert r["is_paid"] is True and r["full_role"], "支付后应返回完整报告"

# 6. 重复支付应报错
r = requests.post(
    f"{BASE}/api/payment/create",
    json={"openid": OPENID, "result_id": result["id"]},
)
print("[6] 重复支付拦截: status =", r.status_code, ", detail =", r.json().get("detail"))
assert r.status_code == 400, "已支付结果应拦截重复下单"

# 7. 历史记录（含角色名）
r = requests.get(f"{BASE}/api/quiz/history", params={"openid": OPENID, "limit": 10}).json()
print("[7] 历史记录:", len(r), "条, 最新 role_name =", r[0]["role_name"], ", role_code =", r[0]["role_code"])
assert r[0]["role_name"] and r[0]["role_code"], "历史记录应包含角色名与代码"

# 8. 未登录用户信息接口
r = requests.get(f"{BASE}/api/auth/user", params={"openid": OPENID}).json()
print("[8] 用户信息: nickname =", r["nickname"])

print("\n✅ 端到端全链路验证通过：登录用户 → 列表/详情 → 答题 → 出结果 → Mock支付 → 解锁完整报告 → 历史卷宗")