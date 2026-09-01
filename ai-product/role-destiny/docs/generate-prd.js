const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
        BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
        TableOfContents } = require('docx');
const fs = require('fs');

// 定义边框样式
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

// 创建表格单元格的辅助函数
function createCell(text, width, isHeader = false, shading = null) {
    return new TableCell({
        borders,
        width: { size: width, type: WidthType.DXA },
        shading: shading ? { fill: shading, type: ShadingType.CLEAR } : undefined,
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
            children: [new TextRun({ text, bold: isHeader, size: isHeader ? 24 : 22 })]
        })]
    });
}

const doc = new Document({
    styles: {
        default: { document: { run: { font: "Microsoft YaHei", size: 22 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 36, bold: true, font: "Microsoft YaHei", color: "2E75B6" },
              paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 30, bold: true, font: "Microsoft YaHei", color: "2E75B6" },
              paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 } },
            { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 26, bold: true, font: "Microsoft YaHei" },
              paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
        ]
    },
    numbering: {
        config: [
            { reference: "bullets",
              levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
                style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
            { reference: "numbers",
              levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
                style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
            { reference: "sub-bullets",
              levels: [{ level: 0, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT,
                style: { paragraph: { indent: { left: 1080, hanging: 360 } } } }] },
        ]
    },
    sections: [{
        properties: {
            page: {
                size: { width: 11906, height: 16838 }, // A4
                margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
            }
        },
        headers: {
            default: new Header({ children: [new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: "角色测算小程序 - 产品规划文档", size: 18, color: "888888" })]
            })] })
        },
        footers: {
            default: new Footer({ children: [new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "第 ", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 }), new TextRun({ text: " 页", size: 18 })]
            })] })
        },
        children: [
            // ========== 封面 ==========
            new Paragraph({ spacing: { before: 2000 }, children: [] }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "角色测算小程序", size: 72, bold: true, color: "2E75B6" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 200 },
                children: [new TextRun({ text: "产品规划文档", size: 48, color: "555555" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 600 },
                children: [new TextRun({ text: "\"你是某本书/电视剧里的谁\" 趣味测试产品", size: 28, italics: true, color: "777777" })]
            }),
            new Paragraph({ spacing: { before: 1500 }, children: [] }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "版本：V1.0", size: 24, color: "666666" })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 100 },
                children: [new TextRun({ text: `日期：${new Date().toLocaleDateString('zh-CN')}`, size: 24, color: "666666" })]
            }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 目录 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("目录")] }),
            new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-3" }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第一章：执行摘要 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("一、执行摘要")] }),
            
            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.1 产品愿景")] }),
            new Paragraph({
                spacing: { after: 120 },
                children: [new TextRun("打造一款基于微信小程序的趣味角色测算产品，通过精心设计的问答系统和算法引擎，让用户发现自己与各类故事角色的内在联系。产品以娱乐性为核心，以社交传播为增长引擎，以微付费为商业模式，成为年轻用户茶余饭后的必备消遣工具。")]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.2 核心数据指标（目标）")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [3000, 2500, 3526],
                rows: [
                    new TableRow({ children: [
                        createCell("指标名称", 3000, true, "D5E8F0"),
                        createCell("首月目标", 2500, true, "D5E8F0"),
                        createCell("六月目标", 3526, true, "D5E8F0"),
                    ]}),
                    new TableRow({ children: [
                        createCell("日活跃用户数 (DAU)", 3000),
                        createCell("5,000", 2500),
                        createCell("50,000", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("付费转化率", 3000),
                        createCell("8%", 2500),
                        createCell("12%", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("ARPU (每用户平均收入)", 3000),
                        createCell("¥2.2", 2500),
                        createCell("¥2.8", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("月收入", 3000),
                        createCell("¥33,000", 2500),
                        createCell("¥504,000", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("分享率", 3000),
                        createCell("15%", 2500),
                        createCell("25%", 3526),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("1.3 商业模式概览")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("定价策略：单次测试 ¥1.99 / 深度报告 ¥2.99")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("核心逻辑：免费体验 → 制造悬念 → 付费解锁深度内容")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("传播机制：社交货币驱动，付费后生成专属分享海报")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("成本结构：低边际成本，主要投入在内容创作和推广")] }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第二章：市场分析 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("二、市场分析与竞品研究")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.1 目标市场画像")] }),
            new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("核心用户群体：年轻女性 (18-30岁)")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [2256, 6770],
                rows: [
                    new TableRow({ children: [
                        createCell("属性", 2256, true, "D5E8F0"),
                        createCell("详细描述", 6770, true, "D5E8F0"),
                    ]}),
                    new TableRow({ children: [
                        createCell("年龄分布", 2256),
                        createCell("18-25岁 (60%) / 26-30岁 (30%) / 其他 (10%)", 6770),
                    ]}),
                    new TableRow({ children: [
                        createCell("兴趣标签", 2256),
                        createCell("追剧、小说阅读、星座命理、心理测试、社交媒体、偶像文化", 6770),
                    ]}),
                    new TableRow({ children: [
                        createCell("消费特征", 2256),
                        createCell("愿意为娱乐体验付费，价格敏感度低(¥3以内)，重视社交分享价值", 6770),
                    ]}),
                    new TableRow({ children: [
                        createCell("使用场景", 2256),
                        createCell("通勤路上、午休时间、睡前放松、朋友聚会互动", 6770),
                    ]}),
                    new TableRow({ children: [
                        createCell("心理诉求", 2256),
                        createCell("自我探索、寻求认同感、话题谈资、情感寄托、炫耀性分享", 6770),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("2.2 市场规模估算")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("微信月活用户：13亿+")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("趣味测试类小程序日均使用人次：500万+ (估算)")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("同类产品头部玩家年收入：千万级")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("市场特点：门槛低、竞争激烈、但爆款可快速获取流量")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("2.3 竞品分析")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [1805, 2256, 2489, 2476],
                rows: [
                    new TableRow({ children: [
                        createCell("产品类型", 1805, true, "E8F0D5"),
                        createCell("代表产品", 2256, true, "E8F0D5"),
                        createCell("优点", 2489, true, "E8F0D5"),
                        createCell("不足/机会点", 2476, true, "E8F0D5"),
                    ]}),
                    new TableRow({ children: [
                        createCell("星座运势类", 1805),
                        createCell("测测、新浪星座", 2256),
                        createCell("用户习惯成熟、付费意愿强", 2489),
                        createCell("同质化严重、缺乏新鲜感", 2476),
                    ]}),
                    new TableRow({ children: [
                        createCell("性格测试类", 1805),
                        createCell("16型人格、MBTI", 2256),
                        createCell("专业性强、社交传播广", 2489),
                        createCell("结果固定、复测率低", 2476),
                    ]}),
                    new TableRow({ children: [
                        createCell("趣味算命类", 1805),
                        createCell("各种H5测试", 2256),
                        createCell("病毒式传播、制作简单", 2489),
                        createCell("生命周期短、信任度低", 2476),
                    ]}),
                    new TableRow({ children: [
                        createCell("IP角色匹配", 1805),
                        createCell("（蓝海）", 2256),
                        createCell("话题性强、粉丝经济", 2489),
                        createCell("版权风险（需规避）", 2476),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("2.4 我们的机会点")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "差异化定位：", bold: true }), new TextRun("用「原创角色原型」替代直接IP引用，既保留吸引力又规避版权风险")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "内容深度：", bold: true }), new TextRun("不只是简单匹配，而是提供有洞察力的性格分析和命运解读")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "社交货币：", bold: true }), new TextRun("付费后生成的精美海报是用户主动分享的动力源")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "持续更新：", bold: true }), new TextRun("紧跟热点，保持内容新鲜感和用户回访率")] }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第三章：产品设计 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("三、产品功能设计")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.1 产品架构总览")] }),
            new Paragraph({ spacing: { after: 100 }, children: [new TextRun("产品由四大核心模块组成：")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "测试引擎模块：", bold: true }), new TextRun("题目管理、选项配置、评分算法、结果匹配")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "内容库模块：", bold: true }), new TextRun("角色原型库、主题分类、文案模板、视觉素材")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "付费模块：", bold: true }), new TextRun("微信支付集成、订单管理、解锁机制、优惠系统")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "社交传播模块：", bold: true }), new TextRun("海报生成、分享卡片、邀请裂变、排行榜")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("3.2 用户旅程设计")] }),
            
            new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("阶段一：入口与吸引（免费）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("首页展示热门测试主题（带精美封面图）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("实时滚动显示：「刚刚 XXX 测出了TA的本命角色」")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("点击进入测试 → 输入基本信息（昵称/生日可选）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("回答 5-8 道趣味选择题（每题配生动插画）")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("阶段二：悬念制造（关键转化点）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("答题结束 → 动画加载效果（营造期待感）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("显示模糊的角色轮廓 + \"你的隐藏身份正在揭晓...\"")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("免费预览：角色类型名称 + 一句话性格描述")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "付费引导：", bold: true, color: "E74C3C" }), new TextRun("「解锁完整命运报告 ¥1.99」按钮（醒目设计）")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("阶段三：付费解锁（价值交付）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("支付成功 → 完整角色形象展示（高清插画+详细描述）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("深度分析内容（详见3.4节）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("生成专属分享海报（带用户昵称+角色名+金句）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("引导分享到朋友圈或好友")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("3.3 测试主题示例（原创角色原型体系）")] }),
            new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "重要说明：", bold: true, color: "E74C3C" }), new TextRun("以下主题均采用「泛化原型」方式描述，不直接引用任何受版权保护的IP名称和角色。用户可根据描述自行联想具体作品，这种模糊性反而增加参与感和讨论度。")] }),
            
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [2000, 3500, 3526],
                rows: [
                    new TableRow({ children: [
                        createCell("主题分类", 2000, true, "F0E8D5"),
                        createCell("主题名称", 3500, true, "F0E8D5"),
                        createCell("角色原型示例", 3526, true, "F0E8D5"),
                    ]}),
                    new TableRow({ children: [
                        createCell("古风权谋", 2000),
                        createCell("「宫廷生存指南」- 你是哪种后宫人设？", 3500),
                        createCell("智慧谋略型·隐忍复仇型·天真入局型·权倾朝野型", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("都市职场", 2000),
                        createCell("「职场生存法则」- 你的办公室人格是什么？", 3500),
                        createCell("精英领袖型·默默耕耘型·圆滑世故型·特立独行型", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("仙侠玄幻", 2000),
                        createCell("「修真界入门」- 你的灵根属性决定了什么？", 3500),
                        createCell("天选之子型·逆袭黑马型·隐世高人型·魔道枭雄型", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("校园青春", 2000),
                        createCell("「青春纪念册」- 你是校园故事里的哪个角色？", 3500),
                        createCell("学霸男神型·元气少女型·暗恋守护型·叛逆酷盖型", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("悬疑推理", 2000),
                        createCell("「迷雾剧场」- 你在悬疑故事中的定位？", 3500),
                        createCell("神探主角型·神秘嫌疑人型·关键证人型·幕后黑手型", 3526),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("3.4 付费内容深度解析（价值锚定）")] }),
            new Paragraph({ spacing: { after: 100 }, children: [new TextRun("用户付费后解锁的完整报告包含以下模块，这是让用户觉得「物超所值」的关键：")] }),
            
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [2200, 6826],
                rows: [
                    new TableRow({ children: [
                        createCell("内容模块", 2200, true, "D5E8F0"),
                        createCell("具体内容描述", 6826, true, "D5E8F0"),
                    ]}),
                    new TableRow({ children: [
                        createCell("角色形象卡", 2200),
                        createCell("高清角色插画 + 角色名称 + 一句灵魂定义语（如「你是那个表面温柔实则心如明镜的人」）", 6826),
                    ]}),
                    new TableRow({ children: [
                        createCell("性格深度剖析", 2200),
                        createCell("200-300字的心理侧写，揭示用户的性格特质、行为模式、内心世界", 6826),
                    ]}),
                    new TableRow({ children: [
                        createCell("优势与挑战", 2200),
                        createCell("列出3个核心优势 + 2个需要注意的成长课题（正面表达，不制造焦虑）", 6826),
                    ]}),
                    new TableRow({ children: [
                        createCell("命运走势", 2200),
                        createCell("近期（本月）的事业/感情/财运趋势预测（趣味性为主，免责声明）", 6826),
                    ]}),
                    new TableRow({ children: [
                        createCell("人生建议", 2200),
                        createCell("2-3条温暖而有启发性的建议金句（适合截图分享）", 6826),
                    ]}),
                    new TableRow({ children: [
                        createCell("匹配度分析", 2200),
                        createCell("与该角色的相似度百分比 + 与其他热门角色的对比排名", 6826),
                    ]}),
                    new TableRow({ children: [
                        createCell("专属分享海报", 2200),
                        createCell("一键生成精美图片，包含用户昵称、角色名、金句、二维码", 6826),
                    ]}),
                ]
            }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第四章：付费转化策略（核心重点）==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("四、付费转化策略（核心重点）")] }),
            new Paragraph({ spacing: { after: 150 }, children: [new TextRun({ text: "本章是产品的商业成功关键，所有设计围绕一个目标：让用户心甘情愿地掏出 ¥1.99-2.99。", bold: true, color: "E74C3C" })] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.1 转化漏斗模型")] }),
            new Paragraph({ spacing: { after: 100 }, children: [new TextRun("我们设计的转化漏斗如下：")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "曝光层 (100%)：", bold: true }), new TextRun("用户看到分享海报/朋友圈广告/搜索推荐")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "点击层 (40%+)：", bold: true }), new TextRun("被标题/封面吸引，进入小程序")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "体验层 (80%+)：", bold: true }), new TextRun("完成免费测试流程（降低门槛）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "悬念层 (90%+)：", bold: true }), new TextRun("看到模糊结果，产生好奇心（关键！）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "付费层 (8-12%)：", bold: true }), new TextRun("转化为付费用户（行业优秀水平）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "传播层 (15-25%)：", bold: true }), new TextRun("付费后分享，带来新用户（自增长引擎）")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("4.2 免费钩子设计（引流）")] }),
            new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("原则：让用户快速体验到「有趣」，但不给「满足感」")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "低门槛进入：", bold: true }), new TextRun("无需注册，打开即测，最多输入昵称（可选）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "精简题量：", bold: true }), new TextRun("5-8道题，每题2-4个选项，总时长控制在2分钟内")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "沉浸体验：", bold: true }), new TextRun("题目配精美插图，选项文案有趣，进度条反馈")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "即时反馈：", bold: true }), new TextRun("答完立即显示「正在为你计算...」动画（3-5秒）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "半遮半掩：", bold: true }), new TextRun("免费只给角色类型名+一句话，完整内容需付费")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("4.3 付费价值包装（说服）")] }),
            new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("定价心理学应用")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "尾数定价：", bold: true }), new TextRun("¥1.99 / ¥2.99 而非 ¥2 / ¥3，给人「不到2块钱」的心理暗示")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "参考锚点：", bold: true }), new TextRun("显示「原价 ¥9.99」划线价，现价显得超值")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "价值量化：", bold: true }), new TextRun("强调「相当于半杯奶茶钱」「一次专业心理咨询的千分之一」")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "限时紧迫：", bold: true }), new TextRun("「新用户首单立减 ¥1」「仅限今日优惠」倒计时")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("付费页面文案模板")] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "【主标题】", bold: true })] }),
            new Paragraph({ spacing: { after: 80 }, shading: { fill: "F5F5F5", type: ShadingType.CLEAR }, children: [new TextRun({ text: "「解锁你的完整命运档案」", italics: true, color: "2E75B6", size: 26 })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "【副标题】", bold: true })] }),
            new Paragraph({ spacing: { after: 80 }, shading: { fill: "F5F5F5", type: ShadingType.CLEAR }, children: [new TextRun({ text: "已有 12,847 人发现了自己的隐藏人格", italics: true, color: "666666" })] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "【价值列表】", bold: true })] }),
            new Paragraph({ numbering: { reference: "sub-bullets", level: 0 }, children: [new TextRun("✓ 高清角色形象卡")] }),
            new Paragraph({ numbering: { reference: "sub-bullets", level: 0 }, children: [new TextRun("✓ 300字深度性格剖析")] }),
            new Paragraph({ numbering: { reference: "sub-bullets", level: 0 }, children: [new TextRun("✓ 本月事业/感情运势")] }),
            new Paragraph({ numbering: { reference: "sub-bullets", level: 0 }, children: [new TextRun("✓ 专属分享海报（永久保存）")] }),
            new Paragraph({ spacing: { before: 80, after: 80 }, children: [new TextRun({ text: "【CTA按钮】", bold: true })] }),
            new Paragraph({ spacing: { after: 150 }, shading: { fill: "E8F4FD", type: ShadingType.CLEAR }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "立即解锁  ¥1.99", bold: true, color: "2E75B6", size: 28 })] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("4.4 促进转化的心理技巧")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [2000, 3500, 3526],
                rows: [
                    new TableRow({ children: [
                        createCell("心理原理", 2000, true, "F0D5E8"),
                        createCell("应用方式", 3500, true, "F0D5E8"),
                        createCell("产品落地示例", 3526, true, "F0D5E8"),
                    ]}),
                    new TableRow({ children: [
                        createCell("好奇心缺口", 2000),
                        createCell("制造信息不对称，激发求知欲", 3500),
                        createCell("模糊预览 + 「你的隐藏身份是...」", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("沉没成本效应", 2000),
                        createCell("已投入时间精力，不愿放弃", 3500),
                        createCell("答完题才显示付费，此时已投入2分钟", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("社会认同", 2000),
                        createCell("他人都在做，我也想做", 3500),
                        createCell("实时显示「XXX刚刚测出了...」", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("稀缺性", 2000),
                        createCell("限时/限量，害怕错过", 3500),
                        createCell("「今日优惠还剩 23 个名额」", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("互惠原理", 2000),
                        createCell("先给予价值，再请求回报", 3500),
                        createCell("免费提供基础结果，再推销深度版", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("自我中心偏差", 2000),
                        createCell("人们关心关于自己的信息", 3500),
                        createCell("个性化结果 + 「你的专属报告」话术", 3526),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("4.5 促销与裂变机制")] }),
            new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("A. 新用户激励")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("首次测试：¥0.99（半价，亏本获客）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("新用户专享：完整报告 ¥1.99（原价 ¥2.99）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("限时福利：注册后24小时内有效")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("B. 邀请裂变（核心增长引擎）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "邀请1位好友：", bold: true }), new TextRun("双方各得 ¥1 优惠券")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "邀请3位好友：", bold: true }), new TextRun("免费解锁1次深度报告")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "拼团模式：", bold: true }), new TextRun("3人成团，每人 ¥1.49（进一步降价刺激）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "排行榜激励：", bold: true }), new TextRun("「邀请达人榜」Top10 送额外奖励")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("C. 复购促进")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "连续测试折扣：", bold: true }), new TextRun("第2次9折，第3次8折，以此类推")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "主题包月卡：", bold: true }), new TextRun("¥9.99/月 无限测试所有主题（提高LTV）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "新主题提醒：", bold: true }), new TextRun("推送通知「你喜欢的XX类型出新测试了」")] }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第五章：社交传播机制 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("五、社交传播机制")] }),
            new Paragraph({ spacing: { after: 150 }, children: [new TextRun("社交传播是这个产品的生命线。我们的目标是让每个付费用户都成为免费的传播节点。")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.1 分享海报设计规范")] }),
            new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("海报必须包含的元素")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "用户昵称：", bold: true }), new TextRun("个性化标识（如「@小甜甜」）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "角色名称：", bold: true }), new TextRun("大字体突出显示（如「智慧谋略型女主」）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "灵魂金句：", bold: true }), new TextRun("一句令人印象深刻的话（如「你以为的退让，其实是以退为进」）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "匹配度：", bold: true }), new TextRun("「92% 相似度」（增加可信度和炫耀资本）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "品牌标识：", bold: true }), new TextRun("小程序Logo + 名称 + 小程序码（方便扫码进入）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "行动召唤：", bold: true }), new TextRun("「扫一扫，测测你是谁」")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("海报风格要求")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("视觉精美：高质量插画/渐变色背景，看起来「值钱」")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("风格统一：每种主题有独特的配色方案和视觉语言")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("适配场景：同时支持朋友圈横版和聊天窗口竖版")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("动态元素：可考虑GIF动效（如闪烁的金光、飘落的花瓣）")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("5.2 分享触发时机设计")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [2000, 3500, 3526],
                rows: [
                    new TableRow({ children: [
                        createCell("触发时机", 2000, true, "D5F0E8"),
                        createCell("引导文案", 3500, true, "D5F0E8"),
                        createCell("用户心理", 3526, true, "D5F0E8"),
                    ]}),
                    new TableRow({ children: [
                        createCell("付费完成后", 2000),
                        createCell("「你的结果太准了！分享给闺蜜看看她是哪种？」", 3500),
                        createCell("兴奋感强，最愿意分享", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("查看报告时", 2000),
                        createCell("「这张海报太好看了，保存到相册吧」", 3500),
                        createCell("审美满足，愿意收藏展示", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("发现有趣结果", 2000),
                        createCell("「只有1%的人是这个角色，快来围观！」", 3500),
                        createCell("稀缺性，引发好奇", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("测试新主题后", 2000),
                        createCell("「你又有了新身份，要不要对比一下？」", 3500),
                        createCell("连续性行为，形成习惯", 3526),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("5.3 传播激励机制")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "分享得奖励：", bold: true }), new TextRun("每次有效分享（被点击）获得积分，积分可兑换免费测试次数")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "晒图返现：", bold: true }), new TextRun("分享到朋友圈并截图发客服，返还 ¥0.5（需真实可见）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "PK功能：", bold: true }), new TextRun("「看看你和TA更配哪个角色？」激发情侣/好友互测")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "话题标签：", bold: true }), new TextRun("预设 #我的本命角色# #你是哪种人# 等话题，便于聚合")] }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第六章：版权合规方案 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("六、版权合规方案")] }),
            new Paragraph({ spacing: { after: 150 }, children: [new TextRun({ text: "版权问题是此类产品的最大法律风险点。本章详细阐述如何在不侵权的前提下，打造同样有吸引力的内容。", bold: true, color: "E74C3C" })] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.1 核心策略：原创角色原型体系")] }),
            new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "核心理念：", bold: true }), new TextRun("我们不测试「你是甄嬛传里的谁」，而是测试「你在古风权谋世界里属于哪种原型」。这种方式的优势：")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "完全合法：", bold: true }), new TextRun("所有角色原型均为原创，不涉及任何第三方IP")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "覆盖面广：", bold: true }), new TextRun("一个原型可以对应多部作品的多个角色，用户自由联想")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "话题性强：", bold: true }), new TextRun("用户会在评论区讨论「我觉得这个像某某剧里的XXX」，自发传播")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "持续可用：", bold: true }), new TextRun("不受任何作品下架/版权到期影响")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("6.2 原型设计方法论")] }),
            new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("步骤一：提取通用 archetype（原型）")] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun("从文学、影视、历史中提炼出跨作品的通用角色类型，例如：")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("英雄之旅类：天选之子、逆袭者、隐世高人、堕落天才")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("权力游戏类：谋略家、傀儡皇帝、权臣、革命者")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("情感关系类：痴情者、负心人、守护者、第三者")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("成长轨迹类：灰姑娘、白雪公主、巫婆、仙女教母")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("步骤二：原创描述文案")] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun("每个原型的描述必须100%原创，参考以下范例：")] }),
            new Paragraph({ spacing: { after: 80 }, shading: { fill: "F5F5F5", type: ShadingType.CLEAR }, children: [new TextRun({ text: "【智慧谋略型】", bold: true })] }),
            new Paragraph({ spacing: { after: 80 }, shading: { fill: "F5F5F5", type: ShadingType.CLEAR }, children: [new TextRun("你拥有超越常人的洞察力和布局能力。表面上云淡风轻，实则心中早已推演过无数种可能。你善于等待时机，从不轻易亮出底牌。在复杂的环境中，你往往能找到那条看似不可能的破局之路。你的沉默不是软弱，而是在积蓄力量。")] }),
            new Paragraph({ spacing: { after: 80 }, shading: { fill: "F5F5F5", type: ShadingType.CLEAR }, children: [new TextRun({ text: "关键词：", bold: true }), new TextRun("深藏不露、运筹帷幄、以退为进、大智若愚")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("步骤三：泛化主题命名")] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun("测试主题使用泛化标签，而非具体作品名：")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [4513, 4513],
                rows: [
                    new TableRow({ children: [
                        createCell("❌ 避免（可能侵权）", 4513, true, "FFD5D5"),
                        createCell("✅ 推荐（安全合规）", 4513, true, "D5FFD5"),
                    ]}),
                    new TableRow({ children: [
                        createCell("「你是甄嬛传里的谁」", 4513),
                        createCell("「宫廷生存指南：你的后宫人设」", 4513),
                    ]}),
                    new TableRow({ children: [
                        createCell("「你是哈利波特里的谁」", 4513),
                        createCell("「魔法世界入门：你的魔法属性」", 4513),
                    ]}),
                    new TableRow({ children: [
                        createCell("「你是红楼梦里的谁」", 4513),
                        createCell("「大家族故事：你的家族角色」", 4513),
                    ]}),
                    new TableRow({ children: [
                        createCell("「你是延禧攻略里的谁」", 4513),
                        createCell("「古代职场：你的晋升路线」", 4513),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("6.3 法律风险排查清单")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "角色名称：", bold: true }), new TextRun("绝不使用任何作品中已有的角色名字（如甄嬛、哈利波特、林黛玉等）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "作品名称：", bold: true }), new TextRun("不在标题、描述中提及具体的书名、剧名")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "剧情细节：", bold: true }), new TextRun("不引用具体情节、台词、设定")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "视觉素材：", bold: true }), new TextRun("所有插画必须原创或购买正版授权，不得使用剧照、封面等")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "背景音乐：", bold: true }), new TextRun("使用无版权音乐或购买授权")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "用户评论：", bold: true }), new TextRun("设置敏感词过滤，提醒用户不要在评论区讨论具体IP")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "免责声明：", bold: true }), new TextRun("在显著位置标注「本测试纯属娱乐，与任何第三方作品无关」")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("6.4 内容更新策略（蹭热点但不侵权）")] }),
            new Paragraph({ spacing: { after: 100 }, children: [new TextRun("当某部作品火爆时，我们可以快速推出相关主题测试，方法如下：")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "速度优先：", bold: true }), new TextRun("在热度峰值期内上线对应类型的测试（如古装剧火就上「古风权谋」主题）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "借势不借名：", bold: true }), new TextRun("宣传文案可以用「最近很火的XX类型故事，测测你是哪种人」")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "用户联想：", bold: true }), new TextRun("引导用户自己建立联系（「是不是很像最近那部剧里的XXX？」）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "持续迭代：", bold: true }), new TextRun("根据用户反馈优化原型描述，使其更贴近大众认知")] }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第七章：内容运营规划 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("七、内容运营规划")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("7.1 内容生产流程")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "选题策划：", bold: true }), new TextRun("每周召开选题会，结合热点、节日、用户反馈确定新主题")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "原型设计：", bold: true }), new TextRun("提炼6-12个角色原型，撰写原创描述文案")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "题目开发：", bold: true }), new TextRun("设计5-8道趣味问题，确保科学性和娱乐性平衡")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "视觉制作：", bold: true }), new TextRun("绘制/采购角色插画、UI界面、分享海报模板")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "测试上线：", bold: true }), new TextRun("内部测试 → 小范围灰度 → 全量发布")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "数据复盘：", bold: true }), new TextRun("监控完测率、付费率、分享率，持续优化")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("7.2 内容更新节奏")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [2000, 3500, 3526],
                rows: [
                    new TableRow({ children: [
                        createCell("频率", 2000, true, "E8D5F0"),
                        createCell("内容类型", 3500, true, "E8D5F0"),
                        createCell("示例", 3526, true, "E8D5F0"),
                    ]}),
                    new TableRow({ children: [
                        createCell("每周", 2000),
                        createCell("1个全新测试主题", 3500),
                        createCell("紧跟热点（如新剧上映同期推出类似题材）", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("每月", 2000),
                        createCell("2-3个常规主题", 3500),
                        createCell("补充经典类型（校园、职场、仙侠等）", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("季度", 2000),
                        createCell("大型专题活动", 3500),
                        createCell("「情人节特辑」「毕业季测试」「万圣节专场」", 3526),
                    ]}),
                    new TableRow({ children: [
                        createCell("年度", 2000),
                        createCell("年度盘点/合集", 3500),
                        createCell("「2026年度最受欢迎角色TOP10」", 3526),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("7.3 热点追踪机制")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "热搜监控：", bold: true }), new TextRun("每日查看微博/抖音/百度热搜，捕捉流行文化趋势")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "影视档期：", bold: true }), new TextRun("提前标记重要剧集/电影上映日期，提前准备内容")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "节日日历：", bold: true }), new TextRun("围绕传统节日、现代节日、网络节日策划专题")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "用户反馈：", bold: true }), new TextRun("收集评论区用户提出的测试建议，快速响应需求")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("7.4 用户生成内容 (UGC) 激励")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "题目投稿：", bold: true }), new TextRun("允许用户提交题目创意，被采纳者获免费测试次数")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "原型共创：", bold: true }), new TextRun("征集用户对角色原型的描述，优秀的纳入官方内容库")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "晒图有奖：", bold: true }), new TextRun("评选最美分享海报，获奖者得月卡或实物奖励")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "社区互动：", bold: true }), new TextRun("搭建「角色交流圈」，让用户讨论测试结果，增加粘性")] }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第八章：技术实现路径 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("八、技术实现路径")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("8.1 技术栈选择")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [2256, 3270, 3500],
                rows: [
                    new TableRow({ children: [
                        createCell("层级", 2256, true, "D5E8F0"),
                        createCell("技术选型", 3270, true, "D5E8F0"),
                        createCell("选型理由", 3500, true, "D5E8F0"),
                    ]}),
                    new TableRow({ children: [
                        createCell("前端", 2256),
                        createCell("微信小程序原生 / Uni-app", 3270),
                        createCell("原生性能好；Uni-app可扩展至其他平台", 3500),
                    ]}),
                    new TableRow({ children: [
                        createCell("后端", 2256),
                        createCell("Node.js + Express / Koa", 3270),
                        createCell("开发效率高，生态丰富，适合IO密集型", 3500),
                    ]}),
                    new TableRow({ children: [
                        createCell("数据库", 2256),
                        createCell("MySQL + Redis", 3270),
                        createCell("MySQL存业务数据，Redis做缓存和计数", 3500),
                    ]}),
                    new TableRow({ children: [
                        createCell("对象存储", 2256),
                        createCell("腾讯云 COS / 阿里云 OSS", 3270),
                        createCell("存储图片、海报等静态资源", 3500),
                    ]}),
                    new TableRow({ children: [
                        createCell("支付", 2256),
                        createCell("微信支付", 3270),
                        createCell("小程序原生支持，用户体验流畅", 3500),
                    ]}),
                    new TableRow({ children: [
                        createCell("海报生成", 2256),
                        createCell("Puppeteer / html2canvas", 3270),
                        createCell("服务端渲染HTML生成精美海报图片", 3500),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("8.2 核心功能模块设计")] }),
            new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("A. 测试引擎")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("题目配置化：JSON格式定义题目、选项、分值权重")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("评分算法：加权计分 + 维度映射（如外向/内向、理性/感性）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("结果匹配：分数区间 → 角色原型映射表")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("随机性控制：加入小幅随机因子，避免相同答案总是同一结果")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("B. 海报生成服务")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("模板系统：预设多种海报布局模板")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("动态填充：将用户数据注入模板（昵称、角色、金句等）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("图片合成：Canvas绘制 + 导出为JPEG/PNG")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("CDN加速：生成后的海报上传OSS，通过CDN分发")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200 }, children: [new TextRun("C. 支付系统")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("微信支付接入：统一下单API")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("订单管理：生成唯一订单号，记录支付状态")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("回调处理：支付成功后自动解锁内容，生成海报")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("异常处理：处理未支付、重复支付、退款等场景")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("8.3 开发里程碑（MVP路线图）")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [1500, 2500, 2500, 2526],
                rows: [
                    new TableRow({ children: [
                        createCell("阶段", 1500, true, "F0E8D5"),
                        createCell("时间", 2500, true, "F0E8D5"),
                        createCell("目标", 2500, true, "F0E8D5"),
                        createCell("交付物", 2526, true, "F0E8D5"),
                    ]}),
                    new TableRow({ children: [
                        createCell("MVP", 1500),
                        createCell("第1-4周", 2500),
                        createCell("核心功能可用", 2500),
                        createCell("1个测试主题 + 支付 + 海报", 2526),
                    ]}),
                    new TableRow({ children: [
                        createCell("V1.1", 1500),
                        createCell("第5-6周", 2500),
                        createCell("内容扩充", 2500),
                        createCell("新增3-5个测试主题", 2526),
                    ]}),
                    new TableRow({ children: [
                        createCell("V1.2", 1500),
                        createCell("第7-8周", 2500),
                        createCell("社交增强", 2500),
                        createCell("邀请裂变 + 排行榜 + 积分", 2526),
                    ]}),
                    new TableRow({ children: [
                        createCell("V2.0", 1500),
                        createCell("第9-12周", 2500),
                        createCell("完善生态", 2500),
                        createCell("会员系统 + 数据分析 + 运营后台", 2526),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("8.4 数据埋点与分析")] }),
            new Paragraph({ spacing: { after: 80 }, children: [new TextRun("关键埋点事件：")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("页面访问：首页、测试页、结果页、支付页")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("测试行为：开始测试、完成测试、退出测试（记录退出题目位置）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("付费行为：发起支付、支付成功、支付失败、取消支付")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("分享行为：生成海报、分享到好友、分享到朋友圈、分享被点击")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("内容偏好：各主题的测试次数、完成率、付费率对比")] }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第九章：风险评估与应对 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("九、风险评估与应对")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("9.1 主要风险识别")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [1500, 2500, 2526, 2500],
                rows: [
                    new TableRow({ children: [
                        createCell("风险类别", 1500, true, "FFD5D5"),
                        createCell("风险描述", 2500, true, "FFD5D5"),
                        createCell("影响程度", 2526, true, "FFD5D5"),
                        createCell("应对策略", 2500, true, "FFD5D5"),
                    ]}),
                    new TableRow({ children: [
                        createCell("法律风险", 1500),
                        createCell("被指控侵犯知识产权", 2500),
                        createCell("高（致命）", 2526),
                        createCell("严格原创审核 + 法务咨询", 2500),
                    ]}),
                    new TableRow({ children: [
                        createCell("竞争风险", 1500),
                        createCell("大厂抄袭或同类产品恶性竞争", 2500),
                        createCell("中", 2526),
                        createCell("快速迭代 + 建立内容壁垒", 2500),
                    ]}),
                    new TableRow({ children: [
                        createCell("政策风险", 1500),
                        createCell("微信平台政策调整（如支付限制）", 2500),
                        createCell("中", 2526),
                        createCell("关注政策动向 + 多平台准备", 2500),
                    ]}),
                    new TableRow({ children: [
                        createCell("用户流失", 1500),
                        createCell("新鲜感过后用户不再使用", 2500),
                        createCell("中高", 2526),
                        createCell("持续内容更新 + 社区运营", 2500),
                    ]}),
                    new TableRow({ children: [
                        createCell("口碑风险", 1500),
                        createCell("用户认为内容不准/无价值", 2500),
                        createCell("中", 2526),
                        createCell("提升内容质量 + 合理预期管理", 2500),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("9.2 应急预案")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "内容下架机制：", bold: true }), new TextRun("如果某个主题引起争议，可在30分钟内下架并替换")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "退款通道：", bold: true }), new TextRun("用户不满意可申请退款（提升口碑，减少投诉）")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "舆情监控：", bold: true }), new TextRun("实时监控社交媒体 mentions，及时响应负面评价")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "法务储备：", bold: true }), new TextRun("预留法务预算，咨询专业知识产权律师")] }),

            // 分页
            new Paragraph({ children: [new PageBreak()] }),

            // ========== 第十章：总结与下一步行动 ==========
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("十、总结与下一步行动")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("10.1 项目核心优势总结")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "市场需求明确：", bold: true }), new TextRun("趣味测试类产品已被验证有大量用户基础和付费意愿")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "商业模式清晰：", bold: true }), new TextRun("低价高频 + 社交传播 = 可规模化的收入模型")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "启动成本低：", bold: true }), new TextRun("MVP阶段不需要大团队，2-3人即可启动")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "版权风险可控：", bold: true }), new TextRun("采用原创原型体系，完全规避IP侵权问题")] }),
            new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "增长潜力大：", bold: true }), new TextRun("社交裂变机制可实现低成本获客")] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("10.2 立即行动计划")] }),
            new Table({
                width: { size: 9026, type: WidthType.DXA },
                columnWidths: [1200, 3000, 2400, 2426],
                rows: [
                    new TableRow({ children: [
                        createCell("序号", 1200, true, "D5F0E8"),
                        createCell("行动项", 3000, true, "D5F0E8"),
                        createCell("负责人", 2400, true, "D5F0E8"),
                        createCell("时间节点", 2426, true, "D5F0E8"),
                    ]}),
                    new TableRow({ children: [
                        createCell("1", 1200),
                        createCell("确认项目立项，组建初始团队", 3000),
                        createCell("项目负责人", 2400),
                        createCell("第1周", 2426),
                    ]}),
                    new TableRow({ children: [
                        createCell("2", 1200),
                        createCell("完成第一个测试主题的内容创作（题目+角色原型+文案）", 3000),
                        createCell("内容策划", 2400),
                        createCell("第1-2周", 2426),
                    ]}),
                    new TableRow({ children: [
                        createCell("3", 1200),
                        createCell("UI设计（首页、测试页、结果页、支付页、海报模板）", 3000),
                        createCell("设计师", 2400),
                        createCell("第2-3周", 2426),
                    ]}),
                    new TableRow({ children: [
                        createCell("4", 1200),
                        createCell("前后端开发（MVP核心功能）", 3000),
                        createCell("开发工程师", 2400),
                        createCell("第2-4周", 2426),
                    ]}),
                    new TableRow({ children: [
                        createCell("5", 1200),
                        createCell("微信支付接入 + 测试", 3000),
                        createCell("开发工程师", 2400),
                        createCell("第4周", 2426),
                    ]}),
                    new TableRow({ children: [
                        createCell("6", 1200),
                        createCell("MVP版本内部测试 + Bug修复", 3000),
                        createCell("全员", 2400),
                        createCell("第4周末", 2426),
                    ]}),
                    new TableRow({ children: [
                        createCell("7", 1200),
                        createCell("提交微信审核 + 上线", 3000),
                        createCell("项目负责人", 2400),
                        createCell("第5周", 2426),
                    ]}),
                    new TableRow({ children: [
                        createCell("8", 1200),
                        createCell("种子用户推广 + 数据收集 + 快速迭代", 3000),
                        createCell("运营", 2400),
                        createCell("第5-8周", 2426),
                    ]}),
                ]
            }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300 }, children: [new TextRun("10.3 成功指标（KPI）")] }),
            new Paragraph({ spacing: { after: 100 }, children: [new TextRun("MVP阶段（前4周）的核心考核指标：")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("上线2周内达到 1000+ 注册用户")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("付费转化率达到 5% 以上")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("分享率达到 10% 以上")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("用户好评率 > 4.5星（满分5星）")] }),
            new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("月收入突破 ¥10,000")] }),

            new Paragraph({ spacing: { before: 400 }, children: [new TextRun({ text: "— 文档结束 —", color: "999999", size: 20 })] }),
        ]
    }]
});

// 生成文档
Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync("d:/OpenCode-Project/aiagent/ai-product/role-destiny/docs/产品规划文档.docx", buffer);
    console.log("✅ 产品规划文档已生成：role-destiny/docs/产品规划文档.docx");
});
