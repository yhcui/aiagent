"""
测算相关API - 核心业务逻辑
"""
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.test import Test, Question, Option
from app.models.role import Role
from app.models.user_test import UserTest
from app.schemas.user_test import UserTestResultSchema, UserTestSchema
from app.schemas.role import RolePreviewSchema, RoleFullSchema
from app.services.cache import cache_service, cache_key
from loguru import logger

router = APIRouter(prefix="/api/quiz", tags=["测算"])


def calculate_role(answers: List[int], db: Session, test_id: int) -> Dict[str, Any]:
    """
    计算测试结果

    算法说明：
    1. 统计各选项的得分
    2. 根据得分计算各角色匹配度
    3. 返回最高匹配度的角色
    """
    # 获取测试的所有角色
    roles = db.query(Role).filter(Role.test_id == test_id).all()

    if not roles:
        raise HTTPException(status_code=404, detail="测试角色未配置")

    # 角色得分统计
    role_scores: Dict[int, float] = {role.id: 0.0 for role in roles}
    total_score = 0

    # 遍历用户答案，计算各角色得分
    for idx, option_id in enumerate(answers):
        option = db.query(Option).filter(Option.id == option_id).first()

        if not option:
            continue

        # 解析得分映射
        if option.score_map:
            try:
                score_map = json.loads(option.score_map)
                for role_code, score in score_map.items():
                    # 找到对应code的角色
                    for role in roles:
                        if role.code == role_code:
                            role_scores[role.id] += float(score)
                            total_score += float(score)
                            break
            except json.JSONDecodeError:
                logger.warning(f"选项{option_id}的score_map解析失败")
                continue

    # 计算匹配度
    results = []
    for role in roles:
        if total_score > 0:
            match_score = (role_scores[role.id] / total_score) * 100
        else:
            match_score = role.rarity * 100 if role.rarity else 0

        results.append({
            "role": role,
            "score": role_scores[role.id],
            "match_score": round(match_score, 1),
        })

    # 按匹配度排序
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results[0]  # 返回匹配度最高的角色


@router.post("/submit", response_model=UserTestResultSchema)
async def submit_test(
    openid: str,
    test_id: int,
    answers: List[int],
    db: Session = Depends(get_db)
):
    """
    提交测试，获取结果
    """
    # 验证用户
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 验证测试
    test = db.query(Test).filter(Test.id == test_id, Test.status == 1).first()
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")

    # 验证题目数量
    questions = db.query(Question).filter(Question.test_id == test_id).all()
    if len(answers) != len(questions):
        raise HTTPException(status_code=400, detail=f"题目数量不匹配，期望{len(questions)}题")

    # 计算结果
    result = calculate_role(answers, db, test_id)
    role = result["role"]
    match_score = result["match_score"]

    # 保存测试记录
    user_test = UserTest(
        user_id=user.id,
        test_id=test_id,
        answers=json.dumps(answers),
        result_role_id=role.id,
        match_score=match_score,
        is_paid=0,
        status="completed",
    )
    db.add(user_test)
    db.commit()
    db.refresh(user_test)

    logger.info(f"用户测试完成: openid={openid}, test_id={test_id}, role={role.name}, score={match_score}")

    # 返回结果（免费预览信息）
    return {
        "id": user_test.id,
        "test_id": test_id,
        "role": role.to_preview_dict(),
        "full_role": None,  # 完整信息需要付费
        "match_score": match_score,
        "is_paid": False,
        "can_generate_poster": True,
    }


@router.get("/result/{result_id}", response_model=UserTestResultSchema)
async def get_test_result(
    result_id: int,
    openid: str,
    db: Session = Depends(get_db)
):
    """
    获取测试结果详情
    """
    # 验证用户
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 查询结果
    user_test = db.query(UserTest).filter(
        UserTest.id == result_id,
        UserTest.user_id == user.id
    ).first()

    if not user_test:
        raise HTTPException(status_code=404, detail="测试结果不存在")

    # 获取角色信息
    role = db.query(Role).filter(Role.id == user_test.result_role_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 根据是否付费返回不同信息
    full_role = None
    if user_test.is_paid:
        full_role = role.to_full_dict()

    return {
        "id": user_test.id,
        "test_id": user_test.test_id,
        "role": role.to_preview_dict(),
        "full_role": full_role,
        "match_score": user_test.match_score,
        "is_paid": bool(user_test.is_paid),
        "can_generate_poster": True,
    }


@router.get("/history", response_model=List[UserTestSchema])
async def get_test_history(
    openid: str,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取用户测试历史
    """
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    history = db.query(UserTest).filter(
        UserTest.user_id == user.id
    ).order_by(UserTest.created_at.desc()).limit(limit).offset(offset).all()

    return [
        {
            "id": h.id,
            "test_id": h.test_id,
            "result_role_id": h.result_role_id,
            "match_score": h.match_score,
            "is_paid": bool(h.is_paid),
            "status": h.status,
            "created_at": h.created_at,
        }
        for h in history
    ]
