"""手语翻译后端：FastAPI + 双分词引擎（jieba / 豆包）+ 本地视频。

启动： uvicorn app:app --reload --port 8000
"""

import os
import random
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# .env 只给豆包引擎用，没装 python-dotenv / 没这个文件都不影响启动
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(BASE_DIR, ".env"))
except Exception:
    pass

from translator import translate
from vocab import VIDEO_DIR, vocabulary

JOKES_PATH = os.path.join(BASE_DIR, "data", "jokes.txt")

ENGINES = ("local", "doubao")

app = FastAPI(title="手语翻译服务", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 视频直接用静态目录提供，前端拿到的 /videos/xxx.mp4 就能播
app.mount("/videos", StaticFiles(directory=VIDEO_DIR), name="videos")


def load_jokes() -> list:
    if not os.path.exists(JOKES_PATH):
        return []
    with open(JOKES_PATH, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


JOKES = load_jokes()


def doubao_summary() -> dict:
    """豆包引擎的可用情况。导入失败也不能影响本地引擎。"""
    try:
        import doubao

        return doubao.config_summary()
    except Exception as exc:
        return {"available": False, "model": None, "reason": "豆包模块不可用：{}".format(exc)}


def pick_engine(value: Optional[str]) -> str:
    return value if value in ENGINES else "local"


class TranslateRequest(BaseModel):
    text: str
    reorder: bool = True
    engine: str = "local"


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "words": len(vocabulary.entries),
        "jokes": len(JOKES),
        "skippedRows": vocabulary.skipped_rows,
        "doubaoConfigured": bool(doubao_summary().get("available")),
    }


@app.get("/api/engines")
def api_engines():
    """可用分词引擎。local 恒为可用，不依赖任何探测。"""
    summary = doubao_summary()
    return {
        "items": [
            {"id": "local", "name": "本地分词（jieba）", "available": True, "default": True},
            {
                "id": "doubao",
                "name": "豆包大模型",
                "available": bool(summary.get("available")),
                "reason": summary.get("reason"),
                "model": summary.get("model"),
            },
        ]
    }


@app.post("/api/translate")
def api_translate(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text 不能为空")
    return translate(req.text, reorder=req.reorder, engine=pick_engine(req.engine))


@app.get("/api/words")
def api_words(q: Optional[str] = None, limit: int = 30):
    return {"total": len(vocabulary.entries), "items": vocabulary.search(q or "", limit=limit)}


@app.get("/api/joke")
def api_joke(index: Optional[int] = None, reorder: bool = True, engine: str = "local"):
    """随机（或指定序号）返回一个笑话，并附带手语翻译结果。"""
    jokes = load_jokes() if not JOKES else JOKES
    if not jokes:
        raise HTTPException(status_code=404, detail="没有可用的笑话")
    if index is None:
        index = random.randrange(len(jokes))
    index = index % len(jokes)
    text = jokes[index]
    return {
        "index": index,
        "total": len(jokes),
        "text": text,
        "translation": translate(text, reorder=reorder, engine=pick_engine(engine)),
    }


@app.get("/api/jokes")
def api_jokes():
    jokes = load_jokes() if not JOKES else JOKES
    return {"total": len(jokes), "items": [{"index": i, "text": t} for i, t in enumerate(jokes)]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
