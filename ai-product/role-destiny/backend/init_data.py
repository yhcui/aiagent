"""
初始化数据库并插入示例数据（宫廷命运测算主题）

用法：
  python init_data.py             # 首次初始化
  python init_data.py --reset     # 清空并重建全部数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import json
from app.database import engine, Base, SessionLocal
from app.models import User, Test, Question, Option, Role

RESET = "--reset" in sys.argv


def init_database():
    """初始化数据库"""
    if RESET:
        print("⚠️ 重置模式：清空所有数据…")
        Base.metadata.drop_all(bind=engine)
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")


def insert_sample_data():
    """插入「宫闱命格」主题数据"""
    db = SessionLocal()

    try:
        if db.query(Test).first():
            print("数据已存在，跳过插入（如需重建请运行 python init_data.py --reset）")
            return

        # ── 测试主题 ──
        test = Test(
            title="测测你的宫闱命格",
            description="八道题入宫，看看你在深宫里是哪一号人物。是天生被偏爱的宠儿，还是运筹帷幄的谋士？",
            cover_image="/static/images/test_cover.png",
            share_title="我在深宫里居然混成了「宠儿」？你也来测！",
            share_desc="八道题，测出你的宫闱命格",
            price=99,  # 0.99元
            status=1,
            sort_order=100,
        )
        db.add(test)
        db.commit()
        db.refresh(test)

        # ── 题目（每题 4 选项；每选项 = 主角色 +2 分、副角色 +1 分；每题覆盖全部 8 个角色）──
        questions_data = [
            {
                "content": "晨起对镜，你的一天通常这样开始：",
                "options": [
                    ("细细挑一支花钿，描好口脂再出门", {"A": 2, "G": 1}),
                    ("利落梳妆，赶上当差的点", {"C": 2, "H": 1}),
                    ("先舒展拳脚，一天才有精气神", {"D": 2, "E": 1}),
                    ("把昨日之事在脑中过一遍再起身", {"B": 2, "F": 1}),
                ],
            },
            {
                "content": "宫宴之上，你更愿意：",
                "options": [
                    ("把新学的养生方子说给姐妹们，句句俏皮逗得满座笑", {"E": 2, "A": 1}),
                    ("趁兴抚琴助兴，曲罢留意各人的神色变化", {"F": 2, "B": 1}),
                    ("盘算着回去绣一幅宫宴图，把仪制规矩都记牢", {"H": 2, "C": 1}),
                    ("给小姐妹们画小像，下笔干脆从不拖沓", {"G": 2, "D": 1}),
                ],
            },
            {
                "content": "宫中突然传开一则离奇传闻，你会：",
                "options": [
                    ("先笑着安抚周围人，再暗中打探一二", {"A": 2, "B": 1}),
                    ("立即清点人手门户，查明传言来处", {"C": 2, "D": 1}),
                    ("熬一锅安神汤水，弹支小曲安定人心", {"E": 2, "F": 1}),
                    ("把它记下来，日后绣进屏风的故事里", {"H": 2, "G": 1}),
                ],
            },
            {
                "content": "上头赐下一箱珍宝，你的第一反应是：",
                "options": [
                    ("不急着要，先想想这箱东西到底什么意思", {"B": 2, "A": 1}),
                    ("想替大家多争一份彩头，当众说得响亮", {"D": 2, "C": 1}),
                    ("高兴得想唱一曲，还不忘提醒别饮酒伤身", {"F": 2, "E": 1}),
                    ("细细端详纹样，日后好用在画稿上", {"G": 2, "H": 1}),
                ],
            },
            {
                "content": "若有一日你掌了一宫之事，最先要做的是：",
                "options": [
                    ("先把大家哄开心，再谈正经事", {"A": 2, "C": 1}),
                    ("处决几桩积案，立了威信再振局面", {"B": 2, "D": 1}),
                    ("开一场小宴庆贺，顺便为绣房添置新线", {"F": 2, "H": 1}),
                    ("先查宫人们的伙食与药膳够不够", {"E": 2, "G": 1}),
                ],
            },
            {
                "content": "难得的休沐日，你最喜欢：",
                "options": [
                    ("把杂务一件件理清，心里才踏实", {"C": 2, "A": 1}),
                    ("到校场去，出一身汗比什么都舒服", {"D": 2, "B": 1}),
                    ("坐在绣架前一整天，只做手工谁也不理", {"H": 2, "F": 1}),
                    ("支起画板，把窗外一景描到天色暗", {"G": 2, "E": 1}),
                ],
            },
            {
                "content": "宫里的姐妹起了争执，你会：",
                "options": [
                    ("先逗乐双方，把气捋顺了再说", {"A": 2, "H": 1}),
                    ("站在中间一嗓子镇住场子，谁也别动", {"D": 2, "F": 1}),
                    ("先看有没有人伤了身子，再慢慢评理", {"E": 2, "B": 1}),
                    ("把两边叫过来画像，画着画着就和好了", {"G": 2, "C": 1}),
                ],
            },
            {
                "content": "若许你出宫成家立业，你的心愿是：",
                "options": [
                    ("开一间书肆，也替街坊把脉问诊", {"B": 2, "E": 1}),
                    ("开一家规矩最全的客栈，迎来送往", {"C": 2, "G": 1}),
                    ("开一间小乐馆，天天有朋友来听曲", {"F": 2, "A": 1}),
                    ("开一间绣坊，罩着学徒们不受欺负", {"H": 2, "D": 1}),
                ],
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
                    score_map=json.dumps(score_map, ensure_ascii=False),
                    sort_order=opt_idx + 1,
                )
                db.add(option)

        db.commit()

        # ── 八大宫闱角色 ──
        roles_data = [
            {
                "code": "A",
                "name": "宠儿",
                "description": "天生被偏爱，走到哪里都是人群的光",
                "detail_text": "「桃之夭夭，灼灼其华」——你是宫里那朵开得最热闹的花，不必争抢，宠爱自会寻你而来。",
                "personality": "天真烂漫，心性活络，眉眼带笑，天生讨人喜欢。你不太设防，也不爱算计，好的坏的都写在脸上。旁人费尽心思想要的东西，你往往不费吹灰之力就得到了。",
                "destiny": "早年顺遂，得贵人庇护；中年凭人缘与直觉屡遇良机；晚年热闹依旧，福气绵长。命里唯一的功课，是学会分辨真心，别被甜言哄了去。",
                "advantages": json.dumps(["人见人爱", "自带好运", "心思透明", "治愈人心"], ensure_ascii=False),
                "weaknesses": json.dumps(["不太会拒绝", "容易被哄", "依赖心重", "吃软不吃硬"], ensure_ascii=False),
                "suggestion": "你的福气是天赐的，但长久要靠自己。多听两句逆耳忠言，学会在甜里尝出分寸，宠爱才会守你一辈子。",
                "lucky_number": "7",
                "lucky_color": "樱粉",
                "motto": "桃花开处，人人让路",
                "rarity": 0.08,
            },
            {
                "code": "B",
                "name": "谋士",
                "description": "藏在棋局背后的人，看得比谁都远",
                "detail_text": "「运筹帷幄之中，决胜千里之外」——热闹是别人的，你早已把答案攥在手里。",
                "personality": "冷静，逻辑强，藏得住心事。你习惯先算三步再开口，话不多，但句句在点子上。别人看见的是局面，你看见的是棋路。",
                "destiny": "少年时慧极早开，轻易看穿世故；中年执掌一方棋盘，得遇明主；晚年退居幕后，名声在外。需防思虑过重，反误了眼前风光。",
                "advantages": json.dumps(["思虑周全", "一眼看穿", "口风极紧", "进退有度"], ensure_ascii=False),
                "weaknesses": json.dumps(["思虑过重", "不易交心", "偶尔毒舌", "高处不胜寒"], ensure_ascii=False),
                "suggestion": "棋局之外还有人间烟火。别把人人都当成对手，偶尔输一句、笑一场，路反而更宽。",
                "lucky_number": "3",
                "lucky_color": "黛蓝",
                "motto": "一步看十步",
                "rarity": 0.12,
            },
            {
                "code": "C",
                "name": "女官",
                "description": "宫中最靠得住的一双手，公道自有千钧",
                "detail_text": "「秉公持重，宫事井然」——有你在的地方，乱麻也会自己排好队。",
                "personality": "靠谱、公正、原则性强。你天生的秩序感让乱局也能理顺，答应的事一定做到。旁人爱把事情交给你，因为交给你，就等于稳了。",
                "destiny": "早年辛苦担责，口碑渐起；中年执掌要务，一呼百应；晚年德高望重，受人敬仰。一生坦荡，问心无愧。",
                "advantages": json.dumps(["公正可靠", "条理分明", "说到做到", "临事不乱"], ensure_ascii=False),
                "weaknesses": json.dumps(["揽事太多", "原则有余变通不足", "不轻易示弱", "偶尔较真"], ensure_ascii=False),
                "suggestion": "你撑得起大局，也要学会把担子分给别人。偶尔放自己一马，这世界不会乱。",
                "lucky_number": "5",
                "lucky_color": "鎏金",
                "motto": "持心如秤，不动如山",
                "rarity": 0.15,
            },
            {
                "code": "D",
                "name": "将星",
                "description": "骨子里燃着火的人，舞台在你脚下",
                "detail_text": "「飒爽英姿，不让须眉」——越是紧要关头，你眼里的光越亮。",
                "personality": "果敢、热血、行动派。你讨厌拖泥带水，认定的事八匹马都拉不回。别人在犹豫的时候，你已经冲了出去，天生为挑战而生。",
                "destiny": "早年屡经磨砺，反而越挫越勇；中年一战成名，登上舞台中央；晚年把故事讲给后人听，一开口仍是传奇。",
                "advantages": json.dumps(["行动力爆表", "越挫越勇", "仗义执言", "天生的主心骨"], ensure_ascii=False),
                "weaknesses": json.dumps(["容易冲动", "听不进劝", "不擅等待", "偶尔伤了身边人"], ensure_ascii=False),
                "suggestion": "冲锋之前，回头看一眼身边人的牵挂。你的剑再快，也要给温柔留一寸鞘。",
                "lucky_number": "1",
                "lucky_color": "绛红",
                "motto": "虽千万人吾往矣",
                "rarity": 0.11,
            },
            {
                "code": "E",
                "name": "医女",
                "description": "温柔是一味药，你恰好随身带着",
                "detail_text": "「妙手仁心，济人以困」——你总能在别人开口之前，先伸出援手。",
                "personality": "柔和、细腻、共情力强。你总能在别人开口前察觉对方的难受，然后不动声色地递上帮助。你不争不抢，却是许多人最想依靠的人。",
                "destiny": "早年积累仁心与技艺；中年以善结缘，路遇贵人；晚年平静喜乐，余庆绵长。种下的每一份好，都会开花。",
                "advantages": json.dumps(["极强的共情", "温柔坚定", "治愈人心", "细节见真章"], ensure_ascii=False),
                "weaknesses": json.dumps(["不擅拒绝", "情绪易被卷入", "习惯委屈自己", "慢热"], ensure_ascii=False),
                "suggestion": "医人先医己。你的温柔要留给值得的人，也留一份给自己，别替别人疼完了所有。",
                "lucky_number": "6",
                "lucky_color": "玉青",
                "motto": "手中有药，心中有灯",
                "rarity": 0.15,
            },
            {
                "code": "F",
                "name": "乐师",
                "description": "一弦一柱，都是你与人间的对话",
                "detail_text": "「弦歌不辍，知音自寻」——只要你在场，空气都会温柔下来。",
                "personality": "感性、浪漫、天生的气氛大师。你对美有敏锐的直觉，情绪像旋律一样流动。你很少大声说话，但你的存在本身就是一首曲子。",
                "destiny": "早年才情初露，得识音律之师；中年凭才华与性情结交天下，处处是朋友；晚年琴鹤相伴，一生风雅。",
                "advantages": json.dumps(["审美在线", "情绪感染力", "人缘极佳", "浪漫细胞"], ensure_ascii=False),
                "weaknesses": json.dumps(["情绪化", "不切实际", "常常拖延", "怕吵闹"], ensure_ascii=False),
                "suggestion": "生活不只是一首曲子，也要有柴米油盐的节拍。把才华落在地上，知音会更多。",
                "lucky_number": "4",
                "lucky_color": "紫檀",
                "motto": "琴声所至，皆有回响",
                "rarity": 0.13,
            },
            {
                "code": "G",
                "name": "画师",
                "description": "把日子过成画的人，眼里都是风景",
                "detail_text": "「丹青不知老将至」——你的眼睛从不骗人，你的画替你说了一切。",
                "personality": "内秀、专注、观察力惊人。热闹的地方你爱躲在角落，把每个人的神态偷偷描在心里。你话不多，但下笔的时候，全世界都安静了。",
                "destiny": "早年潜修不显，中年一画惊人；晚年作品千金难求，自由如风。走过的路，都成了你的画。",
                "advantages": json.dumps(["观察入微", "专注力强", "创造力", "沉得住气"], ensure_ascii=False),
                "weaknesses": json.dumps(["社交耗电", "过于挑剔", "习惯独自消化情绪", "容易拖延"], ensure_ascii=False),
                "suggestion": "好画要留白，人生也要。别把自己关在画室里太久，外面的光也在等你入画。",
                "lucky_number": "8",
                "lucky_color": "青碧",
                "motto": "心中有山水，处处皆画卷",
                "rarity": 0.16,
            },
            {
                "code": "H",
                "name": "绣娘",
                "description": "一针一线里，藏着你的万里山河",
                "detail_text": "「金针度世，锦绣藏心」——你不声不响，却能把最难的日子织成想要的样子。",
                "personality": "耐心、手巧、心细如发。你可以安静地做同一件事很久很久，把寻常日子绣出花来。你很少言语，但你的作品件件都有回响。",
                "destiny": "早年默默打磨技艺；中年手艺开花，声名渐起；晚年岁月静好，手中始终有活、有光。",
                "advantages": json.dumps(["耐心惊人", "手工天赋", "审美细腻", "擅长坚持"], ensure_ascii=False),
                "weaknesses": json.dumps(["过于安静", "不易表达", "容易钻牛角尖", "对瑕疵零容忍"], ensure_ascii=False),
                "suggestion": "你已经把日子过成了手艺，记得偶尔抬头，让风进来。绣绷之外，还有山水。",
                "lucky_number": "2",
                "lucky_color": "棠红",
                "motto": "一针一线，皆是修行",
                "rarity": 0.10,
            },
        ]

        for idx, role_data in enumerate(roles_data):
            role = Role(
                test_id=test.id,
                **role_data,
                sort_order=idx + 1,
            )
            db.add(role)

        db.commit()
        print("✅ 「宫闱命格」数据插入完成（8 题 × 8 角色）")

    except Exception as e:
        print(f"❌ 插入数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("角色测算小程序 - 数据库初始化（宫闱命格）")
    print("=" * 50)

    init_database()
    insert_sample_data()

    print("=" * 50)
    print("🎉 初始化完成！")
    print("=" * 50)