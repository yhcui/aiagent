"""
测试主题相关API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.test import Test, Question, Option
from app.schemas.test import TestSchema, TestListSchema, QuestionSchema, OptionSchema
from app.services.cache import cache_service, cache_key
from loguru import logger

router = APIRouter(prefix="/api/tests", tags=["测试"])


@router.get("", response_model=List[TestListSchema])
async def get_test_list(db: Session = Depends(get_db)):
    """
    获取测试主题列表
    """
    # 尝试从缓存获取
    cache_k = cache_key("test", "list")
    cached = cache_service.get(cache_k)
    if cached:
        logger.debug("返回测试列表缓存")
        return cached

    # 从数据库查询
    tests = db.query(Test).filter(Test.status == 1).order_by(Test.sort_order.desc()).all()

    result = []
    for test in tests:
        question_count = db.query(Question).filter(Question.test_id == test.id).count()
        test_dict = {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "cover_image": test.cover_image,
            "share_title": test.share_title,
            "price": test.price,
            "status": test.status,
            "sort_order": test.sort_order,
            "question_count": question_count,
        }
        result.append(test_dict)

    # 缓存5分钟
    cache_service.set(cache_k, result, ttl=300)

    return result


@router.get("/{test_id}", response_model=TestSchema)
async def get_test_detail(test_id: int, db: Session = Depends(get_db)):
    """
    获取测试详情
    """
    test = db.query(Test).filter(Test.id == test_id, Test.status == 1).first()

    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")

    # 查询题目和选项
    questions = db.query(Question).filter(
        Question.test_id == test_id
    ).order_by(Question.sort_order).all()

    question_list = []
    for q in questions:
        options = db.query(Option).filter(
            Option.question_id == q.id
        ).order_by(Option.sort_order).all()

        question_list.append({
            "id": q.id,
            "content": q.content,
            "sort_order": q.sort_order,
            "options": [
                {
                    "id": opt.id,
                    "content": opt.content,
                    "sort_order": opt.sort_order,
                }
                for opt in options
            ]
        })

    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "cover_image": test.cover_image,
        "share_title": test.share_title,
        "share_desc": test.share_desc,
        "price": test.price,
        "question_count": len(questions),
        "questions": question_list,
    }


@router.get("/{test_id}/share-info")
async def get_share_info(test_id: int, db: Session = Depends(get_db)):
    """
    获取分享信息
    """
    test = db.query(Test).filter(Test.id == test_id, Test.status == 1).first()

    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")

    return {
        "title": test.share_title or test.title,
        "desc": test.share_desc or test.description,
        "image": test.cover_image,
        "path": f"/pages/test/detail?id={test_id}",
    }
