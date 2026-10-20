"""
后台管理API（轻量）
- 简单账号密码登录 → 内存 Token
- 数据看板 / 题目管理 / 角色管理 / 用户与订单
"""
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.config import settings
from app.services.cache import cache_service, cache_key
from app.models.user import User
from app.models.test import Test, Question, Option
from app.models.role import Role
from app.models.user_test import UserTest
from app.models.order import Order

router = APIRouter(prefix="/api/admin", tags=["后台管理"])


def bust_test_cache():
    """主题/题目变更后清除小程序端列表缓存"""
    cache_service.delete(cache_key("test", "list"))

# ── 内存会话（重启即失效，开发期够用）──
_sessions: Dict[str, float] = {}
TOKEN_TTL = 12 * 3600


def verify_admin(authorization: Optional[str] = Header(None)):
    """管理端鉴权依赖"""
    token = authorization.replace("Bearer ", "") if authorization else ""
    expire = _sessions.get(token)
    if not expire or expire < time.time():
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return token


# ── 请求模型 ──
class AdminLogin(BaseModel):
    username: str
    password: str


class OptionIn(BaseModel):
    id: Optional[int] = None
    content: str
    score_map: Dict[str, float] = {}
    sort_order: int = 0


class QuestionIn(BaseModel):
    content: str
    sort_order: int = 0
    options: List[OptionIn] = []


class RoleIn(BaseModel):
    test_id: Optional[int] = None
    name: str
    code: str
    description: Optional[str] = None
    detail_text: Optional[str] = None
    personality: Optional[str] = None
    destiny: Optional[str] = None
    advantages: List[str] = []
    weaknesses: List[str] = []
    suggestion: Optional[str] = None
    lucky_number: Optional[str] = None
    lucky_color: Optional[str] = None
    motto: Optional[str] = None
    rarity: float = 0.15
    sort_order: int = 0


class TestIn(BaseModel):
    """测试主题模型"""
    title: str
    description: Optional[str] = None
    share_title: Optional[str] = None
    share_desc: Optional[str] = None
    price: int = 99  # 单位：分
    status: int = 1
    sort_order: int = 0


# ── 登录 ──
@router.post("/login")
async def admin_login(data: AdminLogin):
    if data.username != settings.ADMIN_USERNAME or data.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="账号或密码错误")

    token = uuid.uuid4().hex
    _sessions[token] = time.time() + TOKEN_TTL
    return {"token": token}


# ── 数据看板 ──
@router.get("/stats")
async def admin_stats(db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    total_users = db.query(User).count()
    total_taken = db.query(UserTest).count()
    paid_count = db.query(UserTest).filter(UserTest.is_paid == 1).count()

    revenue = db.query(func.sum(Order.amount)).filter(Order.status == "paid").scalar() or 0

    # 角色分布
    role_dist = (
        db.query(Role.name, func.count(UserTest.id).label("cnt"))
        .join(UserTest, UserTest.result_role_id == Role.id)
        .group_by(Role.id, Role.name)
        .order_by(func.count(UserTest.id).desc())
        .all()
    )

    # 近7日答题量
    start = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    daily = (
        db.query(func.substr(UserTest.created_at, 1, 10).label("day"), func.count(UserTest.id))
        .filter(UserTest.created_at >= start)
        .group_by("day")
        .all()
    )
    daily_map = {d: c for d, c in daily}
    days = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

    return {
        "total_users": total_users,
        "total_taken": total_taken,
        "paid_count": paid_count,
        "conversion": round(paid_count / total_taken * 100, 1) if total_taken else 0,
        "revenue": round(float(revenue), 2),
        "role_dist": [{"name": n, "count": c} for n, c in role_dist],
        "daily": [{"day": d, "count": daily_map.get(d, 0)} for d in days],
    }


# ── 测试主题 ──
@router.get("/tests")
async def admin_tests(db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    tests = db.query(Test).order_by(Test.id).all()
    result = []
    for t in tests:
        qcount = db.query(Question).filter(Question.test_id == t.id).count()
        result.append({
            "id": t.id, "title": t.title, "description": t.description,
            "price": t.price, "status": t.status, "question_count": qcount,
        })
    return result


@router.get("/tests/{test_id}")
async def admin_test_detail(test_id: int, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(404, "测试不存在")

    questions = db.query(Question).filter(Question.test_id == test_id).order_by(Question.sort_order).all()
    q_list = []
    for q in questions:
        options = db.query(Option).filter(Option.question_id == q.id).order_by(Option.sort_order).all()
        q_list.append({
            "id": q.id, "content": q.content, "sort_order": q.sort_order,
            "options": [{
                "id": o.id, "content": o.content, "sort_order": o.sort_order,
                "score_map": json.loads(o.score_map) if o.score_map else {},
            } for o in options],
        })
    return {
        "id": test.id, "title": test.title, "description": test.description,
        "share_title": test.share_title, "share_desc": test.share_desc,
        "price": test.price, "status": test.status, "sort_order": test.sort_order,
        "questions": q_list,
    }


@router.post("/tests")
async def create_test(data: TestIn, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    test = Test(
        title=data.title, description=data.description,
        share_title=data.share_title, share_desc=data.share_desc,
        price=data.price, status=data.status, sort_order=data.sort_order,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    bust_test_cache()
    return {"id": test.id}


@router.put("/tests/{test_id}")
async def update_test(test_id: int, data: TestIn, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(404, "测试不存在")

    test.title = data.title
    test.description = data.description
    test.share_title = data.share_title
    test.share_desc = data.share_desc
    test.price = data.price
    test.status = data.status
    test.sort_order = data.sort_order
    test.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    bust_test_cache()
    return {"ok": True}


@router.delete("/tests/{test_id}")
async def delete_test(test_id: int, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    used = db.query(UserTest).filter(UserTest.test_id == test_id).count()
    if used:
        raise HTTPException(400, f"该主题已有 {used} 条答题记录，不能删除（可将主题下架）")

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(404, "测试不存在")

    # 级联清理：选项 → 题目 → 角色 → 主题
    question_ids = [q.id for q in db.query(Question.id).filter(Question.test_id == test_id).all()]
    if question_ids:
        db.query(Option).filter(Option.question_id.in_(question_ids)).delete(synchronize_session=False)
    db.query(Question).filter(Question.test_id == test_id).delete(synchronize_session=False)
    db.query(Role).filter(Role.test_id == test_id).delete(synchronize_session=False)
    db.delete(test)
    db.commit()
    bust_test_cache()
    return {"ok": True}


# ── 题目管理 ──
@router.post("/tests/{test_id}/questions")
async def create_question(test_id: int, data: QuestionIn, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(404, "测试不存在")

    max_sort = db.query(func.max(Question.sort_order)).filter(Question.test_id == test_id).scalar() or 0
    question = Question(test_id=test_id, content=data.content, sort_order=data.sort_order or max_sort + 1)
    db.add(question)
    db.commit()
    db.refresh(question)

    for idx, opt in enumerate(data.options):
        db.add(Option(
            question_id=question.id, content=opt.content,
            score_map=json.dumps(opt.score_map, ensure_ascii=False),
            sort_order=opt.sort_order or idx + 1,
        ))
    db.commit()
    bust_test_cache()
    return {"id": question.id}


@router.put("/questions/{qid}")
async def update_question(qid: int, data: QuestionIn, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    question = db.query(Question).filter(Question.id == qid).first()
    if not question:
        raise HTTPException(404, "题目不存在")

    question.content = data.content
    question.sort_order = data.sort_order or question.sort_order

    # 同步选项：有 id 更新，无 id 新建，缺失的删除
    existing = {o.id: o for o in db.query(Option).filter(Option.question_id == qid).all()}
    keep_ids = set()
    for idx, opt in enumerate(data.options):
        if opt.id and opt.id in existing:
            o = existing[opt.id]
            o.content = opt.content
            o.score_map = json.dumps(opt.score_map, ensure_ascii=False)
            o.sort_order = idx + 1
            keep_ids.add(opt.id)
        else:
            o = Option(
                question_id=qid, content=opt.content,
                score_map=json.dumps(opt.score_map, ensure_ascii=False),
                sort_order=idx + 1,
            )
            db.add(o)
    for oid, o in existing.items():
        if oid not in keep_ids:
            db.delete(o)

    db.commit()
    bust_test_cache()
    return {"ok": True}


@router.delete("/questions/{qid}")
async def delete_question(qid: int, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    question = db.query(Question).filter(Question.id == qid).first()
    if not question:
        raise HTTPException(404, "题目不存在")

    db.query(Option).filter(Option.question_id == qid).delete()
    db.delete(question)
    db.commit()
    bust_test_cache()
    return {"ok": True}


# ── 角色管理 ──
@router.get("/roles")
async def admin_roles(test_id: int, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    roles = db.query(Role).filter(Role.test_id == test_id).order_by(Role.sort_order).all()
    return [{
        "id": r.id, "name": r.name, "code": r.code, "description": r.description,
        "detail_text": r.detail_text, "personality": r.personality, "destiny": r.destiny,
        "advantages": json.loads(r.advantages) if r.advantages else [],
        "weaknesses": json.loads(r.weaknesses) if r.weaknesses else [],
        "suggestion": r.suggestion, "lucky_number": r.lucky_number,
        "lucky_color": r.lucky_color, "motto": r.motto, "rarity": r.rarity,
        "sort_order": r.sort_order,
        "used_count": db.query(UserTest).filter(UserTest.result_role_id == r.id).count(),
    } for r in roles]


@router.post("/roles")
async def create_role(data: RoleIn, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    if not data.test_id:
        raise HTTPException(400, "缺少 test_id")
    role = Role(
        test_id=data.test_id, name=data.name, code=data.code,
        description=data.description, detail_text=data.detail_text,
        personality=data.personality, destiny=data.destiny,
        advantages=json.dumps(data.advantages, ensure_ascii=False),
        weaknesses=json.dumps(data.weaknesses, ensure_ascii=False),
        suggestion=data.suggestion, lucky_number=data.lucky_number,
        lucky_color=data.lucky_color, motto=data.motto,
        rarity=data.rarity, sort_order=data.sort_order,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return {"id": role.id}


@router.put("/roles/{rid}")
async def update_role(rid: int, data: RoleIn, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    role = db.query(Role).filter(Role.id == rid).first()
    if not role:
        raise HTTPException(404, "角色不存在")

    for field in ["name", "code", "description", "detail_text", "personality", "destiny",
                  "suggestion", "lucky_number", "lucky_color", "motto", "rarity", "sort_order"]:
        setattr(role, field, getattr(data, field))
    role.advantages = json.dumps(data.advantages, ensure_ascii=False)
    role.weaknesses = json.dumps(data.weaknesses, ensure_ascii=False)

    db.commit()
    return {"ok": True}


@router.delete("/roles/{rid}")
async def delete_role(rid: int, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    used = db.query(UserTest).filter(UserTest.result_role_id == rid).count()
    if used:
        raise HTTPException(400, f"该角色已被 {used} 条测试记录引用，不能删除（可先下线测试主题）")
    role = db.query(Role).filter(Role.id == rid).first()
    if not role:
        raise HTTPException(404, "角色不存在")
    db.delete(role)
    db.commit()
    return {"ok": True}


# ── 用户与订单 ──
@router.get("/users")
async def admin_users(limit: int = 100, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    users = db.query(User).order_by(User.id.desc()).limit(limit).all()
    return [{
        "id": u.id, "openid": u.openid, "nickname": u.nickname,
        "phone": u.phone, "created_at": u.created_at,
        "test_count": db.query(UserTest).filter(UserTest.user_id == u.id).count(),
        "paid_count": db.query(UserTest).filter(UserTest.user_id == u.id, UserTest.is_paid == 1).count(),
    } for u in users]


@router.get("/orders")
async def admin_orders(limit: int = 100, db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    orders = db.query(Order).order_by(Order.id.desc()).limit(limit).all()
    user_map = {u.id: u for u in db.query(User).filter(
        User.id.in_([o.user_id for o in orders] or [0])).all()}
    return [{
        "id": o.id, "order_no": o.order_no, "amount": o.amount, "status": o.status,
        "pay_time": o.pay_time, "transaction_id": o.transaction_id,
        "user": user_map[o.user_id].nickname or user_map[o.user_id].openid[:8] if o.user_id in user_map else "-",
    } for o in orders]