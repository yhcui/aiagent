# -*- coding: utf-8 -*-
"""验证6个新主题的答题计分链路"""
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:8000"
OPENID = "dev_openid_001"

for tid in range(3, 9):
    detail = requests.get(f"{BASE}/api/tests/{tid}").json()
    qs = detail["questions"]
    assert len(qs) == 4, "主题%s应有4题, 实际%s" % (tid, len(qs))
    # 每题选第一个选项
    answers = [q["options"][0]["id"] for q in qs]
    r = requests.post(f"{BASE}/api/quiz/submit",
                      json={"openid": OPENID, "test_id": tid, "answers": answers})
    assert r.status_code == 200, "提交失败: %s %s" % (r.status_code, r.text)
    res = r.json()
    role = res["role"]
    print("[OK] 主题%s %-18s → 测出: %s(%s) 契合度%s%%"
          % (tid, detail["title"], role["name"], role["code"], res["match_score"]))

print("ALL-PASS")
