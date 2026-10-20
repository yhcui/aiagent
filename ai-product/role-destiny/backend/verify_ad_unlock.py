# -*- coding: utf-8 -*-
"""验证广告解锁模式：UNLOCK_MODE=ad 时的全链路"""
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:8000"
OPENID = "dev_openid_001"

# 1. 答题拿一个新结果（主题3 甄嬛传）
detail = requests.get(f"{BASE}/api/tests/3").json()
answers = [q["options"][0]["id"] for q in detail["questions"]]
r = requests.post(f"{BASE}/api/quiz/submit",
                  json={"openid": OPENID, "test_id": 3, "answers": answers}).json()
rid = r["id"]
print("[1] 新答题结果: id =", rid, ", is_paid =", r["is_paid"])

# 2. 查结果：未付费时应返回广告解锁信息
res = requests.get(f"{BASE}/api/quiz/result/{rid}", params={"openid": OPENID}).json()
print("[2] 结果信息: unlock_mode =", res["unlock_mode"], ", ad_unit_id =", res["ad_unit_id"], ", price_fen =", res["price_fen"])
assert res["unlock_mode"] == "ad", "UNLOCK_MODE=ad 时应返回 ad"
assert res["ad_unit_id"], "应返回广告位ID"
assert res["full_role"] is None, "未解锁不应有完整报告"

# 3. 广告解锁
r = requests.post(f"{BASE}/api/payment/ad-unlock",
                  json={"openid": OPENID, "result_id": rid}).json()
print("[3] 广告解锁: ", r)
assert r["unlocked"] is True

# 4. 解锁后应有完整报告
res = requests.get(f"{BASE}/api/quiz/result/{rid}", params={"openid": OPENID}).json()
print("[4] 解锁后: is_paid =", res["is_paid"], ", full_role 命中 =", bool(res["full_role"]),
      ", unlock_mode =", res["unlock_mode"], "(已付费回退 pay 展示)")
assert res["is_paid"] and res["full_role"], "解锁后应返回完整报告"

# 5. 幂等：重复解锁不报错
r = requests.post(f"{BASE}/api/payment/ad-unlock",
                  json={"openid": OPENID, "result_id": rid}).json()
print("[5] 幂等重复解锁:", r)
assert r["unlocked"] is True

print("AD-UNLOCK-PASS")
