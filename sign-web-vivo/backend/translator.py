"""把中文句子翻译成手语视频序列。

两种分词引擎，前端可切换：
  local （默认）：句子 -> 按标点切句 -> jieba 分词（词表当自定义词典）-> 去虚词 -> 简单语序调整
  doubao        ：句子 -> 豆包大模型直接给出手语语序的词序列 -> 去虚词

之后都走同一条落地链：每个词查词表（整词 / 同义词 / 数字 / 最大匹配拆词 / 单字）-> 视频片段列表。
豆包这条路失败（没配 key、超时、格式错）会自动回退到 local。
"""

import re
from typing import Dict, List, Optional

import jieba

from vocab import normalize, vocabulary

# ---------------- 词典准备 ----------------

for _w in vocabulary.words():
    # 保证词表里的词一定能被切出来
    jieba.add_word(_w, freq=100000)

# 手语一般不打的虚词、语气词
FUNCTION_WORDS = set("的 地 得 了 着 过 吗 呢 吧 啊 呀 嘛 哦 噢 呗 咯 之 者 而 就 才 被 把 将 所 以及 于 与 且".split())

# 口语说法 -> 词表里实际存在的词
SYNONYMS: Dict[str, str] = {
    "您": "你",
    "咱": "我",
    "咱们": "我们",
    "俺": "我",
    "爸": "爸爸",
    "妈": "妈妈",
    "老爸": "爸爸",
    "老妈": "妈妈",
    "谢谢你": "谢谢",
    "多谢": "谢谢",
    "对不起": "抱歉",
    "不好意思": "抱歉",
    "怎样": "怎么样",
    "哪儿": "哪里",
    "啥": "什么",
    "干嘛": "什么",
    "为啥": "为什么",
    "咋": "怎么样",
    "上厕所": "厕所",
    "开心": "高兴",
    "特别": "很",
    "非常": "很",
    "十分": "很",
    "挺": "很",
    "超": "很",
    "想要": "想",
    "可以": "行",
    "不可以": "不行",
    "没事": "没关系",
    "再见": "见",
}

# 时间词（手语习惯放句首）
TIME_WORDS = set(
    "今天 明天 昨天 前天 后天 今年 明年 去年 现在 刚才 以前 以后 将来 早上 上午 中午 下午 晚上 夜里 春天 夏天 秋天 冬天 今晚 每天 星期一 星期二 星期三 星期四 星期五 星期六 星期天 周末".split()
)

# 疑问词（手语习惯放句尾）
QUESTION_WORDS = set("什么 为什么 哪里 怎么样 谁 几 多少 几点 几岁 怎么".split())

PUNCT_SPLIT_RE = re.compile(r"[。！？!?；;\n\r]+")
PUNCT_CHAR_RE = re.compile(r"^[\s，,、：:\"'“”‘’（）()《》\-—…·.]+$")
DIGIT_RE = re.compile(r"^\d+(\.\d+)?$")

CN_DIGITS = "零一二三四五六七八九"
CN_UNITS = ["", "十", "百", "千"]


# ---------------- 数字处理 ----------------

def number_to_chinese(text: str) -> List[str]:
    """把阿拉伯数字读成中文字，返回逐字列表（词表里都是单字数字）。"""
    if "." in text:
        left, right = text.split(".", 1)
        return number_to_chinese(left) + ["点"] + [CN_DIGITS[int(c)] for c in right]

    value = int(text)
    if value == 0:
        return ["零"]
    if value < 10:
        return [CN_DIGITS[value]]
    if value < 100:
        tens, ones = divmod(value, 10)
        out = (["十"] if tens == 1 else [CN_DIGITS[tens], "十"])
        if ones:
            out.append(CN_DIGITS[ones])
        return out
    if len(text) <= 4:
        out: List[str] = []
        length = len(text)
        for i, ch in enumerate(text):
            d = int(ch)
            unit = CN_UNITS[length - i - 1]
            if d == 0:
                continue
            out.append(CN_DIGITS[d])
            if unit:
                out.append(unit)
        return out
    # 很长的数字（年份、电话号）按位读
    return [CN_DIGITS[int(c)] for c in text]


# ---------------- 匹配 ----------------

def _entry_dict(word: str, source: str, origin: str) -> dict:
    entry = vocabulary.get(word)
    return {
        "word": entry.word,
        "pinyin": entry.pinyin,
        "category": entry.category,
        "video": entry.video,
        "origin": origin,      # 句子里原本的词
        "source": source,      # exact / synonym / split / char / number
    }


def _max_match(text: str) -> Optional[List[str]]:
    """正向最大匹配，把没直接命中的词拆成词表里有的小词。全部拆成功才返回。"""
    result: List[str] = []
    i = 0
    limit = min(vocabulary.max_word_len, len(text))
    while i < len(text):
        for size in range(min(limit, len(text) - i), 0, -1):
            piece = text[i:i + size]
            if vocabulary.has(piece):
                result.append(piece)
                i += size
                break
        else:
            return None
    return result


def match_token(token: str) -> dict:
    """把一个分词结果映射成 0~N 个手语视频。"""
    word = normalize(token)
    if not word:
        return {"token": token, "status": "skip", "reason": "punct", "clips": []}

    # 1. 直接命中
    if vocabulary.has(word):
        return {"token": token, "status": "matched", "clips": [_entry_dict(word, "exact", token)]}

    # 2. 同义词
    alias = SYNONYMS.get(word)
    if alias and vocabulary.has(alias):
        return {"token": token, "status": "matched", "clips": [_entry_dict(alias, "synonym", token)]}

    # 3. 数字
    if DIGIT_RE.match(word):
        chars = number_to_chinese(word)
        clips = [_entry_dict(c, "number", token) for c in chars if vocabulary.has(c)]
        if clips:
            return {"token": token, "status": "matched", "clips": clips}

    # 4. 拆成词表里的小词（很开心 -> 很 + 开心）
    if len(word) > 1:
        pieces = _max_match(word)
        if pieces:
            source = "char" if all(len(p) == 1 for p in pieces) else "split"
            return {
                "token": token,
                "status": "matched",
                "clips": [_entry_dict(p, source, token) for p in pieces],
            }

        # 5. 部分单字命中，能打几个算几个
        clips = [_entry_dict(c, "char", token) for c in word if vocabulary.has(c)]
        if clips:
            return {"token": token, "status": "partial", "clips": clips}

    return {"token": token, "status": "missing", "clips": []}


# ---------------- 语序调整 ----------------

def reorder_tokens(tokens: List[str]) -> List[str]:
    """手语语序的一个简化处理：时间词提到最前，疑问词挪到最后。"""
    head, middle, tail = [], [], []
    for token in tokens:
        key = normalize(token)
        if key in TIME_WORDS:
            head.append(token)
        elif key in QUESTION_WORDS:
            tail.append(token)
        else:
            middle.append(token)
    return head + middle + tail


# ---------------- 分词与结果组装 ----------------

def cut_sentence(sentence: str) -> List[str]:
    tokens: List[str] = []
    for token in jieba.cut(sentence, cut_all=False):
        token = token.strip()
        if not token or PUNCT_CHAR_RE.match(token):
            continue
        if normalize(token) in FUNCTION_WORDS:
            continue
        tokens.append(token)
    return tokens


def _build(tokens: List[str]):
    """一串词 -> (分词结果, 视频片段, 未命中词)。两种引擎共用这段落地逻辑。"""
    all_tokens: List[dict] = []
    clips: List[dict] = []
    missing: List[str] = []

    for token in tokens:
        info = match_token(token)
        if info["status"] == "skip":
            continue
        for clip in info["clips"]:
            clip["index"] = len(clips)
            clips.append(clip)
        if info["status"] in ("missing", "partial"):
            missing.append(info["token"])
        all_tokens.append({
            "token": info["token"],
            "status": info["status"],
            "clipIndexes": [c["index"] for c in info["clips"]],
        })

    return all_tokens, clips, missing


def _result(
    text: str,
    tokens: List[str],
    engine: str,
    requested_engine: str,
    gloss: Optional[List[str]] = None,
    fallback_reason: Optional[str] = None,
) -> dict:
    all_tokens, clips, missing = _build(tokens)
    valid = [t for t in all_tokens if t["status"] != "skip"]
    matched = [t for t in valid if t["status"] == "matched"]
    return {
        "text": text,
        "tokens": all_tokens,
        "clips": clips,
        "missing": missing,
        "coverage": round(len(matched) / len(valid), 3) if valid else 0.0,
        "engine": engine,                    # 实际生效的引擎
        "requestedEngine": requested_engine,  # 请求时选的
        "gloss": gloss,                       # 大模型给出的词序列，local 时为 None
        "fallbackReason": fallback_reason,    # 降级原因，没降级为 None
    }


def filter_words(words: List[str]) -> List[str]:
    """去掉标点和不打的虚词。"""
    out: List[str] = []
    for word in words:
        word = (word or "").strip()
        if not word or PUNCT_CHAR_RE.match(word):
            continue
        if normalize(word) in FUNCTION_WORDS:
            continue
        out.append(word)
    return out


# ---------------- 引擎一：本地 jieba（默认，完全离线） ----------------

def translate_local(
    text: str,
    reorder: bool = True,
    requested_engine: str = "local",
    fallback_reason: Optional[str] = None,
) -> dict:
    tokens: List[str] = []
    for sentence in PUNCT_SPLIT_RE.split(text):
        if not sentence.strip():
            continue
        cut = cut_sentence(sentence)
        if reorder:
            cut = reorder_tokens(cut)
        tokens.extend(cut)
    return _result(text, tokens, "local", requested_engine, None, fallback_reason)


# ---------------- 引擎二：豆包大模型 ----------------

def translate_doubao(text: str) -> dict:
    import doubao  # 延迟导入：不选豆包就完全不碰它，也不需要装 httpx

    gloss = doubao.sign_gloss(text)
    return _result(text, filter_words(gloss), "doubao", "doubao", gloss, None)


# ---------------- 对外入口 ----------------

def translate(text: str, reorder: bool = True, engine: str = "local") -> dict:
    """返回分词结果 + 可播放的视频片段序列。engine 只认 local / doubao，其他一律当 local。"""
    text = (text or "").strip()

    if engine != "doubao":
        return translate_local(text, reorder)

    try:
        return translate_doubao(text)
    except Exception as exc:
        reason = str(exc).strip() or exc.__class__.__name__
        return translate_local(text, reorder, requested_engine="doubao", fallback_reason=reason)
