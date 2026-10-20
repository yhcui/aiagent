# Role-Destiny 开发进度文档

> **更新时间**：2026-10-13
> **项目路径**：`d:\OpenCode-Project\aiagent\ai-product\role-destiny`
> **当前版本**：v1.0.0 (开发中) · 主题：「宫闱命格」甜美宫廷风

---

## 📋 项目概述

**角色测算小程序 (Role Destiny)** - 微信小程序原生 + FastAPI + SQLite

- 用户回答 8 道「宫廷情境题」，测算出宫闱命格角色（宠儿/谋士/女官/将星/医女/乐师/画师/绣娘）
- 免费看角色名与契合度 → ¥0.99 解锁完整命格报告 → Canvas 生成分享海报
- 目标用户：18-30 岁女性；商业模式：低价冲动消费 + 社交裂变

---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | 微信小程序原生 | WXML/WXSS/JS，Canvas 2D 海报 |
| 后端 | Python FastAPI | 异步框架，5 组路由 |
| 数据库 | SQLite + SQLAlchemy | `backend/data/role_destiny.db` |
| 登录 | 微信 code2session | **已配真实 AppID/Secret（测试环境）** |
| 支付 | DEBUG Mock / 预留真实支付 | 商户号未申请前走模拟支付 |

---

## ✅ 本轮已完成（2026-10-13）

### 1. 配置与联调
- [x] 创建 `backend/.env`，填入真实 AppID `wxcb849637ca14cee5` + AppSecret（仅测试环境，备案前不能上线）
- [x] 修复 `wechat.py` 死代码 bug、`TestListSchema` 缺 `question_count` 字段
- [x] 修复多处 **POST 接口 query/body 契约错配**（此前 submit/payment 从未真正跑通！）：
  - `/api/quiz/submit`、`/api/payment/create`、`/api/auth/bind-phone`、`PUT /api/auth/user` 全部改为 JSON body
- [x] Mock 支付：DEBUG 模式 `/api/payment/create` 直接标记已支付并返回 `mock: true`
- [x] 历史接口补 `role_name / role_code` 字段
- [x] **端到端全链路验证通过**：登录用户→列表/详情→答题→出结果→Mock支付→解锁完整报告→历史卷宗

### 2. 设计体系（甜美宫廷风，frontend-design 技能）
- [x] `app.wxss` 全局设计系统：胭脂 `#FF6B9D`/杏柿/鎏金 `#C9A24B`/黛蓝/云白/玄墨；宋体展示标题 + 系统正文；卡片纸券/金线/玉牌签/骨架屏/编排入场动效
- [x] `utils/roleStyle.js`：8 角色视觉档案（徽记 emoji/袍色渐变/hex 色柱/稀有度玉档），全端共用

### 3. 页面重做（8 页）
- [x] **首页**：沉浸式月门英雄区（宫廷金环+三种角色徽记漂浮）、「开始测算」CTA、滚动播报、本期限定卡
- [x] **测试列表**：卷轴式卡片、金边纹样、玉牌标签
- [x] **测试详情**：封面英雄 + 奏折说明卡 + 卷册信息 + 底部 CTA
- [x] **答题页**：宫灯进度（点亮/呼吸动效）+ 丝绸进度条 + 天干印章选项（甲乙丙丁）+ 两段式切换动画
- [x] **结果页**：角色徽记圆盘 + 稀有度印 + 契合度丝带填满动画 + **模糊封存卡+鎏金解锁按钮+社会认同**（未付费）/ 判词·性格·命运·天赋暗影·箴言·幸运之物（已付费）
- [x] **分享页**：Canvas 2D 绘制命格御画（角色渐变底/红印章/契合度/金角/昵称），保存相册+分享好友
- [x] **个人中心**：命牌头图（渐变+金环头像）、统计、宫务菜单
- [x] **历史记录**：命格卷宗列表（角色徽记圆+解锁玉档），空态带 CTA

### 4. 内容扩充（宫廷主题）
- [x] `init_data.py` 重写：8 道情境题 × 4 选项（每题覆盖全部 8 角色，主+2/副+1 计分）+ 8 个角色全字段（判词/性格/命运/天赋/暗影/箴言/幸运物/稀有度，全原创避开版权）
- [x] 支持 `python init_data.py --reset` 重建；控制台 UTF-8 输出修复

### 5. 后台管理系统（2026-10-13 新增）
- [x] **访问**：后端启动后浏览器打开 `http://127.0.0.1:8000/admin`
- [x] 账号密码在 `backend/.env`（ADMIN_USERNAME / ADMIN_PASSWORD，默认 admin / gongge@2026，上线前务必改）
- [x] 数据看板：用户量 / 答题量 / 解锁数 / 付费转化率 / 累计收入 / 命格分布 / 近7日答题量
- [x] 题目管理：选测试主题 → 编辑题干、选项内容、计分映射 JSON（格式 `{"A":2,"G":1}`）；新增/删除题目
- [x] 角色管理：编辑全部字段（名称/代号/稀有度/判词/性格/命运/天赋/暗影/箴言/幸运物）；新增/删除（被引用的角色禁止删除）
- [x] 用户 / 订单列表
- [x] 鉴权：内存 Token（12h 过期，后端重启需重新登录）；未登录访问 API 返回 401
- [x] 代码：`backend/app/api/admin.py` + `backend/static/admin.html`（单文件无依赖）
- [ ] 待办：角色徽记/颜色目前在前端 `utils/roleStyle.js` 按 code 匹配，后台改 code 需同步改前端

---

## ❌ 待完成

### 需要你操作（外部依赖）
- [ ] **域名备案**（进行中）→ 通过后可配置正式环境
- [ ] 申请微信支付商户号 → 替换 Mock 支付（`payment.py` 已预留真实支付分支）
- [ ] 小程序码生成（需认证主体调 `wxacode.getUnlimited`，海报红印位可替换成真码）

### 开发侧
- [ ] 微信开发者工具 + 真机走一遍完整流程（重点：Canvas 海报在真机的渲染、emoji 显示、自定义导航栏适配）
- [ ] 表情包式插画资源（如需，可替换纯代码视觉）
- [ ] 数据埋点（分享率、解锁转化、各角色分布）
- [ ] 服务器部署 + HTTPS + 日志监控

---

## 🚀 快速启动

```bash
# 后端
cd d:/OpenCode-Project/aiagent/ai-product/role-destiny/backend
pip install -r requirements.txt
python init_data.py --reset        # 首次或重置数据
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 小程序
# 微信开发者工具导入 miniprogram 目录（AppID 已设为 wxcb849637ca14cee5）
# 真机调试时把 miniprogram/app.js 的 apiBaseUrl 改成局域网 IP
```

**验证**：`http://127.0.0.1:8000/health` → `{"status":"ok"}` · API 文档 `/docs`

---

## 📁 关键文件索引

| 文件 | 用途 |
|------|------|
| `backend/app/api/quiz.py` | 测算算法（计分 → 匹配度 → 结果/历史） |
| `backend/app/api/payment.py` | 支付（Mock 分支 + 真实支付预留） |
| `backend/init_data.py` | 宫廷主题数据（8 题 × 8 角色） |
| `backend/.env` | 真实配置（已被 .gitignore 保护） |
| `miniprogram/app.wxss` | **设计系统**（色板/字体/组件/动效） |
| `miniprogram/utils/roleStyle.js` | **角色视觉档案**（改角色样式来这） |
| `miniprogram/pages/result/detail.js` | 结果页（付费墙核心页） |
| `miniprogram/pages/result/share.js` | Canvas 2D 海报绘制 |
| `miniprogram/pages/test/question.js` | 答题逻辑（宫灯进度/切题动画） |

---

## 📝 开发日志

### 2026-10-13
- ✅ 配置真实 AppID/Secret、修复全部 query/body 契约错配、接入 Mock 支付、E2E 验证通过
- ✅ 甜美宫廷风全套重设计（8 页 + 设计系统 + 角色视觉档案 + Canvas 海报）
- ✅ 宫廷主题内容扩充（8 题 × 8 角色全字段）
- ⏳ 待真机验证 + 备案/商户号

### 2026-09-02
- 项目结构搭建、后端 API、小程序页面雏形、示例数据（旧版心理原型 3 题 3 角色，已被替换）

---

## 💡 开发提示

- 改 UI 颜色/字体/圆角 → 先看 `app.wxss` 顶部的设计系统注释
- 改角色样式（徽记/颜色）→ `miniprogram/utils/roleStyle.js`（前端）与数据库角色表（后端）两处
- 后端改动后需重启 uvicorn；历史/结果缓存极短，无需操心
- 设计规范原文件：`docs/V1.0-UI设计规范.md`（樱花粉基调，本轮在其基础上融入宫廷金/黛蓝）