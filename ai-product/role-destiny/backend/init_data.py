"""
初始化数据库并插入示例数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from app.database import engine, Base, SessionLocal
from app.models import User, Test, Question, Option, Role


def init_database():
    """初始化数据库"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")


def insert_sample_data():
    """插入示例数据"""
    db = SessionLocal()

    try:
        # 检查是否已有数据
        if db.query(Test).first():
            print("数据已存在，跳过插入")
            return

        # 创建测试主题
        test = Test(
            title="测测你是哪种性格原型",
            description="基于荣格心理学理论，探索你内心深处的性格原型",
            cover_image="/static/images/test_cover.png",
            share_title="我居然是「智者」原型！太准了",
            share_desc="基于荣格心理学，测出你的隐藏性格",
            price=99,  # 0.99元
            status=1,
            sort_order=100,
        )
        db.add(test)
        db.commit()
        db.refresh(test)

        # 创建题目
        questions_data = [
            {
                "content": "面对困难时，你通常会？",
                "options": [
                    ("冷静分析，制定计划", json.dumps({"A": 3, "B": 1, "C": 0})),
                    ("寻求他人的建议和帮助", json.dumps({"A": 1, "B": 3, "C": 1})),
                    ("凭直觉行动，随机应变", json.dumps({"A": 0, "B": 1, "C": 3})),
                ]
            },
            {
                "content": "你更看重的是？",
                "options": [
                    ("智慧与知识", json.dumps({"A": 3, "B": 1, "C": 0})),
                    ("情感与人际关系", json.dumps({"A": 1, "B": 3, "C": 1})),
                    ("行动与成就", json.dumps({"A": 0, "B": 1, "C": 3})),
                ]
            },
            {
                "content": "你理想的生活方式是？",
                "options": [
                    ("不断学习，探索未知", json.dumps({"A": 3, "B": 1, "C": 0})),
                    ("与爱的人在一起，享受生活", json.dumps({"A": 1, "B": 3, "C": 1})),
                    ("挑战自我，实现目标", json.dumps({"A": 0, "B": 1, "C": 3})),
                ]
            },
        ]

        for idx, q_data in enumerate(questions_data):
            question = Question(
                test_id=test.id,
                content=q_data["content"],
                sort_order=idx + 1,
            )
            db.add(question)
            db.commit()
            db.refresh(question)

            for opt_idx, (content, score_map) in enumerate(q_data["options"]):
                option = Option(
                    question_id=question.id,
                    content=content,
                    score_map=score_map,
                    sort_order=opt_idx + 1,
                )
                db.add(option)

        db.commit()

        # 创建角色原型
        roles_data = [
            {
                "code": "A",
                "name": "智者",
                "description": "你是一个追求真理和智慧的人",
                "detail_text": "你拥有强烈的好奇心和求知欲，喜欢思考抽象的问题。你善于分析问题，追求真理，往往能够看透事物的本质。",
                "personality": "理性、独立、好奇、善于思考",
                "destiny": "适合从事教育、研究、咨询等领域",
                "advantages": json.dumps(["逻辑思维强", "善于分析", "求知欲强", "理性冷静"]),
                "weaknesses": json.dumps(["有时过于理性", "可能忽视情感", "容易钻牛角尖"]),
                "suggestion": "多关注自己的情感需求，学会平衡理性与感性",
                "lucky_number": "7",
                "lucky_color": "深蓝色",
                "motto": "知识就是力量",
                "rarity": 0.33,
            },
            {
                "code": "B",
                "name": "爱人",
                "description": "你是一个充满爱心和同理心的人",
                "detail_text": "你重视人际关系，善于倾听和理解他人。你拥有强烈的同理心，总是愿意帮助需要帮助的人。",
                "personality": "温柔、善解人意、富有同情心、关怀他人",
                "destiny": "适合从事心理咨询、护理、教育等服务型工作",
                "advantages": json.dumps(["同理心强", "善于沟通", "人际关系好", "温暖体贴"]),
                "weaknesses": json.dumps(["有时过于在意他人", "难以拒绝别人", "容易受伤"]),
                "suggestion": "学会设立边界，保护自己的情感能量",
                "lucky_number": "2",
                "lucky_color": "粉色",
                "motto": "爱是世界上最强大的力量",
                "rarity": 0.33,
            },
            {
                "code": "C",
                "name": "英雄",
                "description": "你是一个勇敢无畏、追求成就的人",
                "detail_text": "你充满勇气和决心，敢于面对挑战。你追求成就，渴望证明自己的价值，往往能够在逆境中崛起。",
                "personality": "勇敢、自信、果断、有领导力",
                "destiny": "适合创业、管理、竞技等领域",
                "advantages": json.dumps(["勇敢果断", "执行力强", "抗压能力好", "领导力强"]),
                "weaknesses": json.dumps(["有时过于冲动", "忽视细节", "可能刚愎自用"]),
                "suggestion": "学会倾听他人意见，三思而后行",
                "lucky_number": "1",
                "lucky_color": "红色",
                "motto": "没有不可能的事",
                "rarity": 0.34,
            },
        ]

        for role_data in roles_data:
            role = Role(
                test_id=test.id,
                **role_data,
                sort_order=1,
            )
            db.add(role)

        db.commit()
        print("✅ 示例数据插入完成")

    except Exception as e:
        print(f"❌ 插入数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("角色测算小程序 - 数据库初始化")
    print("=" * 50)

    init_database()
    insert_sample_data()

    print("=" * 50)
    print("🎉 初始化完成！")
    print("=" * 50)
