"""想法（ideas）增删改查。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import get_conn
from ..deps import require_auth

router = APIRouter(prefix="/api/ideas", tags=["ideas"], dependencies=[Depends(require_auth)])


class IdeaCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("")
def list_ideas():
    """未完成在前，已完成在后；同组内按创建时间倒序。"""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, content, is_completed, created_at, completed_at
            FROM ideas
            ORDER BY is_completed ASC, created_at DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
def create_idea(payload: IdeaCreate):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")

    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO ideas (content, created_at) VALUES (?, ?)",
            (content, _now()),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, content, is_completed, created_at, completed_at FROM ideas WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
    return dict(row)


@router.patch("/{idea_id}")
def toggle_idea(idea_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Idea 不存在")

        new_completed = 0 if row["is_completed"] else 1
        conn.execute(
            "UPDATE ideas SET is_completed = ?, completed_at = ? WHERE id = ?",
            (new_completed, _now() if new_completed else None, idea_id),
        )
        conn.commit()
    return {"ok": True, "is_completed": new_completed}


@router.delete("/{idea_id}")
def delete_idea(idea_id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Idea 不存在")
    return {"ok": True}
