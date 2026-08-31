"""手语词表加载：把 sign_language_words.csv 与 videos/ 下的实际视频文件对应起来。"""

import csv
import os
import re
from typing import Dict, List, Optional

# 项目根目录（csv 和 videos 都在这里）
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT_DIR, "sign_language_words.csv")
VIDEO_DIR = os.path.join(ROOT_DIR, "videos")

# 词条里的 ①②③ 表示同一个词的不同打法，匹配时要去掉
VARIANT_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]")


def normalize(word: str) -> str:
    """把词条统一成用于查表的形式：去掉变体标记、空格。"""
    return VARIANT_RE.sub("", word or "").strip().replace(" ", "")


class SignEntry:
    """一个手语词 = 文字 + 拼音 + 视频地址。"""

    __slots__ = ("word", "pinyin", "category", "video", "variants")

    def __init__(self, word: str, pinyin: str, category: str, video: str):
        self.word = word
        self.pinyin = pinyin
        self.category = category
        self.video = video          # 形如 /videos/common/xxx.mp4
        self.variants: List[str] = [video]

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "pinyin": self.pinyin,
            "category": self.category,
            "video": self.video,
            "variants": self.variants,
        }


class Vocabulary:
    def __init__(self):
        self.entries: Dict[str, SignEntry] = {}   # normalize(word) -> SignEntry
        self.max_word_len = 1
        self.skipped_rows = 0
        self._load()

    # ---------- 加载 ----------

    def _index_video_files(self) -> Dict[str, str]:
        """扫描 videos 目录，建立 文件名 -> 相对路径 索引。

        csv 里同一个视频常被多个分类引用，但文件只下载到了其中一个分类目录下，
        所以按文件名全局查找，命中率最高。
        """
        index: Dict[str, str] = {}
        if not os.path.isdir(VIDEO_DIR):
            return index
        for dirpath, _dirnames, filenames in os.walk(VIDEO_DIR):
            rel_dir = os.path.relpath(dirpath, VIDEO_DIR).replace("\\", "/")
            for name in filenames:
                if not name.lower().endswith(".mp4"):
                    continue
                rel = name if rel_dir == "." else f"{rel_dir}/{name}"
                index.setdefault(name, f"/videos/{rel}")
        return index

    def _load(self) -> None:
        video_index = self._index_video_files()
        with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                raw_word = (row.get("word") or "").strip()
                key = normalize(raw_word)
                if not key:
                    continue
                filename = os.path.basename((row.get("video_url") or "").strip())
                video = video_index.get(filename)
                if not video:
                    self.skipped_rows += 1
                    continue

                exist = self.entries.get(key)
                if exist is None:
                    self.entries[key] = SignEntry(
                        word=key,
                        pinyin=(row.get("pinyin") or "").strip(),
                        category=(row.get("category") or "").strip(),
                        video=video,
                    )
                    self.max_word_len = max(self.max_word_len, len(key))
                elif video not in exist.variants:
                    # 同一个词的其他打法，留着备用
                    exist.variants.append(video)

    # ---------- 查询 ----------

    def get(self, word: str) -> Optional[SignEntry]:
        return self.entries.get(normalize(word))

    def has(self, word: str) -> bool:
        return normalize(word) in self.entries

    def words(self) -> List[str]:
        return list(self.entries.keys())

    def search(self, keyword: str, limit: int = 30) -> List[dict]:
        keyword = normalize(keyword)
        if not keyword:
            return [e.to_dict() for e in list(self.entries.values())[:limit]]
        starts, contains = [], []
        for key, entry in self.entries.items():
            if key.startswith(keyword):
                starts.append(entry)
            elif keyword in key or keyword in entry.pinyin:
                contains.append(entry)
            if len(starts) >= limit:
                break
        return [e.to_dict() for e in (starts + contains)[:limit]]


vocabulary = Vocabulary()
