"""豆包大模型客户端：把中文句子转成手语语序的词序列。

只负责调接口和解析结果，不认识词表、也不认识视频。
配置全部走环境变量，见 .env.example。
"""

import json
import os
import re
from collections import OrderedDict
from typing import List, Optional

# httpx 是可选依赖，没装也不能影响本地 jieba 那条链路
try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None


DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seed-1-6-250615"
DEFAULT_TIMEOUT = 12.0

CACHE_LIMIT = 256

# 模型输出可能被 ```json ``` 包起来
CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")
# 兜底切分用的分隔符
SPLIT_RE = re.compile(r"[\s,，、/|>+]+")

SYSTEM_PROMPT = """你是中国手语（CSL）语序转换助手。把用户给的普通中文句子，改写成中国手语打法的词序列。
规则：
1. 用手语语序：时间在最前，其次主体，动作/谓语靠后，疑问词放句尾。
2. 去掉「的、了、着、吗、呢、把、被」这类不打的虚词。
3. 否定词放在被否定的动作后面（例：不想去 -> 去 不）。
4. 修饰语后置（例：红苹果 -> 苹果 红）。
5. 拆成常用、具体的单词，尽量用 1~2 个字的基础词，避免书面语和成语；不认识的专有名词按字拆开。
6. 阿拉伯数字写成中文（8 点 -> 八 点）。
只输出 JSON：{"gloss": ["词1","词2"]}，不要解释。"""


class DoubaoError(Exception):
    """豆包这条链路上的任何问题，统一抛这个，由上层决定是否回退。"""


# ---------------- 配置 ----------------

def api_key() -> str:
    return (os.getenv("ARK_API_KEY") or "").strip()


def model() -> str:
    return (os.getenv("ARK_MODEL") or "").strip() or DEFAULT_MODEL


def base_url() -> str:
    return ((os.getenv("ARK_BASE_URL") or "").strip() or DEFAULT_BASE_URL).rstrip("/")


def timeout() -> float:
    try:
        return float(os.getenv("ARK_TIMEOUT") or DEFAULT_TIMEOUT)
    except ValueError:
        return DEFAULT_TIMEOUT


def unavailable_reason() -> Optional[str]:
    """不可用时返回原因，可用时返回 None。"""
    if httpx is None:
        return "未安装 httpx，执行 pip install -r backend/requirements.txt"
    if not api_key():
        return "未配置 ARK_API_KEY"
    return None


def is_configured() -> bool:
    return unavailable_reason() is None


def config_summary() -> dict:
    reason = unavailable_reason()
    return {
        "available": reason is None,
        "model": model(),
        "baseUrl": base_url(),
        "reason": reason,
    }


# ---------------- 缓存 ----------------

_cache: "OrderedDict[str, List[str]]" = OrderedDict()


def _cache_get(key: str) -> Optional[List[str]]:
    if key not in _cache:
        return None
    _cache.move_to_end(key)
    return list(_cache[key])


def _cache_put(key: str, value: List[str]) -> None:
    _cache[key] = list(value)
    _cache.move_to_end(key)
    while len(_cache) > CACHE_LIMIT:
        _cache.popitem(last=False)


def clear_cache() -> None:
    _cache.clear()


# ---------------- 解析 ----------------

def _parse_gloss(content: str) -> List[str]:
    """从模型回复里抠出词序列。"""
    text = CODE_FENCE_RE.sub("", (content or "").strip())
    if not text:
        raise DoubaoError("豆包返回内容为空")

    words: List[str] = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None

    if isinstance(data, dict):
        raw = data.get("gloss")
        if isinstance(raw, list):
            words = [str(w) for w in raw]
        elif isinstance(raw, str):
            words = SPLIT_RE.split(raw)
    elif isinstance(data, list):
        words = [str(w) for w in data]
    else:
        # 不是 JSON 就按分隔符硬切一遍
        words = SPLIT_RE.split(text)

    words = [w.strip().strip("\"'“”‘’") for w in words]
    words = [w for w in words if w]
    if not words:
        raise DoubaoError("豆包返回格式无法解析：" + text[:80])
    return words


# ---------------- 对外入口 ----------------

def sign_gloss(text: str) -> List[str]:
    """中文句子 -> 手语语序的词序列。失败抛 DoubaoError。"""
    text = (text or "").strip()
    if not text:
        return []

    reason = unavailable_reason()
    if reason:
        raise DoubaoError(reason)

    cached = _cache_get(text)
    if cached is not None:
        return cached

    payload = {
        "model": model(),
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }

    try:
        with httpx.Client(timeout=timeout()) as client:
            resp = client.post(
                base_url() + "/chat/completions",
                headers={
                    "Authorization": "Bearer " + api_key(),
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except Exception as exc:  # 超时、连不上、DNS…
        raise DoubaoError("豆包请求失败：{}".format(exc)) from exc

    if resp.status_code != 200:
        detail = resp.text[:120].replace("\n", " ")
        raise DoubaoError("豆包返回 {}：{}".format(resp.status_code, detail))

    try:
        content = resp.json()["choices"][0]["message"]["content"]
        print("豆包回复：", content)
    except Exception as exc:
        raise DoubaoError("豆包响应结构异常：{}".format(exc)) from exc

    words = _parse_gloss(content)
    _cache_put(text, words)
    return words
