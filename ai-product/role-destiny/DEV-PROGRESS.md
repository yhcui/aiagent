# Role-Destiny 开发进度文档

> **更新时间**：2026-09-02  
> **项目路径**：`d:\OpenCode-Project\aiagent\ai-product\role-destiny`  
> **当前版本**：v1.0.0 (开发中)

---

## 📋 项目概述

### 产品名称
**角色测算小程序 (Role Destiny)** - 基于心理学的性格原型测试工具

### 核心功能
- 用户通过回答心理学问题，测算出自己的性格原型角色
- 支持付费解锁完整报告
- 生成分享海报

### 商业模式
- 免费测试 + 付费解锁详细报告（0.99元/次）
- 社交传播裂变（分享海报、好友邀请）

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本/说明 |
|------|------|----------|
| **前端** | 微信小程序原生 | WXML/WXSS/JS |
| **后端** | Python FastAPI | 异步框架 |
| **数据库** | SQLite | 轻量级，适合起步 |
| **ORM** | SQLAlchemy | 数据库操作 |
| **支付** | 微信支付 V2/V3 | 待配置 |
| **缓存** | 自定义缓存服务 | 内存缓存 |

---

## ✅ 已完成功能 (进度: 75%)

### 1. 后端 API 接口 (100%)

#### 1.1 认证模块 (`/api/auth`)
| 接口 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/api/auth/login` | POST | ✅ | 小程序登录（code换openid） |
| `/api/auth/user` | GET | ✅ | 获取用户信息 |
| `/api/auth/user` | PUT | ✅ | 更新用户信息（昵称、头像） |
| `/api/auth/bind-phone` | POST | ✅ | 绑定手机号 |

#### 1.2 测试模块 (`/api/tests`)
| 接口 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/api/tests` | GET | ✅ | 获取测试列表（带缓存） |
| `/api/tests/{id}` | GET | ✅ | 获取测试详情（含题目选项） |
| `/api/tests/{id}/share-info` | GET | ✅ | 获取分享信息 |

#### 1.3 测算模块 (`/api/quiz`) ⭐核心
| 接口 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/api/quiz/submit` | POST | ✅ | 提交答案，计算结果 |
| `/api/quiz/result/{id}` | GET | ✅ | 获取测试结果详情 |
| `/api/quiz/history` | GET | ✅ | 获取用户历史记录 |

**算法逻辑**：
```python
# 选项得分映射示例
{"A": 3, "B": 1, "C": 0}  # 选择该选项对各角色的得分贡献

# 计算流程：
1. 统计各选项的得分 → 累加到对应角色
2. 计算匹配度 = 角色得分 / 总分 × 100%
3. 返回匹配度最高的角色
```

#### 1.4 支付模块 (`/api/payment`)
| 接口 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/api/payment/create` | POST | ✅ | 创建支付订单 |
| `/api/payment/notify` | POST | ✅ | 微信支付回调 |
| `/api/payment/query/{order_no}` | GET | ✅ | 查询订单状态 |

⚠️ **注意**：支付功能需要配置微信商户号才能使用

#### 1.5 海报模块 (`/api/poster`)
| 接口 | 方法 | 状态 | 说明 |
|------|------|------|------|
| 海报生成接口 | - ✅ | 已实现（详见 poster.py） |

---

### 2. 小程序页面 (90%)

#### 2.1 页面结构
```
miniprogram/
├── app.js                    # 应用入口（登录、全局方法）
├── app.json                  # 配置（4个Tab页）
├── pages/
│   ├── index/index           # 首页（登录 + 测试列表）
│   ├── test/
│   │   ├── list.js          # 测试列表（Tab页）
│   │   ├── detail.js        # 测试详情
│   │   └── question.js      # 答题页面 ⭐
│   ├── result/
│   │   ├── detail.js        # 结果详情（含付费解锁）
│   │   └── share.js         # 分享页面
│   └── user/
│       ├── profile.js       # 个人中心（Tab页）
│       └── history.js       # 测试历史（Tab页）
└── services/                 # API 服务层
    ├── apiService.js        # HTTP 请求封装
    ├── userService.js       # 用户服务
    ├── testService.js       # 测试服务
    ├── quizService.js       # 测算服务
    ├── paymentService.js    # 支付服务
    └── posterService.js     # 海报服务
```

#### 2.2 各页面完成度

| 页面 | 完成度 | 功能说明 |
|------|--------|---------|
| **首页** `index` | 95% | 自动登录、加载测试列表、下拉刷新 |
| **测试列表** `test/list` | 95% | 展示测试卡片、价格显示、跳转详情 |
| **测试详情** `test/detail` | 90% | 测试介绍、开始测试、分享配置 |
| **答题页** `test/question` | 95% | 单题展示、选项选择、上下题切换、进度条、提交 |
| **结果详情** `result/detail` | 85% | 角色展示、付费解锁提示、重新测试、保存海报 |
| **分享页** `result/share` | 80% | 分享海报展示 |
| **个人中心** `user/profile` | 85% | 用户信息、统计数据、绑定手机、关于我们 |
| **历史记录** `user/history` | 90% | 历史列表、查看详情、下拉刷新 |

---

### 3. 数据库设计 (100%)

#### 3.1 数据表结构（7张表）

```sql
-- 1. 用户表 users
users (
  id, openid(唯一), unionid, nickname, avatar, phone, status, created_at, updated_at
)

-- 2. 测试主题表 tests
tests (
  id, title, description, cover_image, share_title, share_desc, 
  price(单位:分), status, sort_order, created_at, updated_at
)

-- 3. 题目表 questions
questions (id, test_id, content, sort_order, created_at)

-- 4. 选项表 options
options (id, question_id, content, score_map(JSON), sort_order, created_at)
-- score_map 示例: {"A": 3, "B": 1, "C": 0}

-- 5. 角色原型表 roles ⭐核心
roles (
  id, test_id, name, code, description, image,
  detail_text, personality, destiny, 
  advantages(JSON), weaknesses(JSON), suggestion,
  lucky_number, lucky_color, motto, rarity, sort_order, created_at
)

-- 6. 用户测试记录表 user_tests
user_tests (
  id, user_id, test_id, answers(JSON), result_role_id, 
  match_score, is_paid, paid_at, status, created_at
)

-- 7. 订单表 orders
orders (
  id, order_no(唯一), user_id, result_id, test_id, amount,
  status(pending/paid/refunded/failed), transaction_id, 
  pay_time, expire_time, created_at, updated_at
)
```

#### 3.2 示例数据

已内置一套完整的测试数据（`init_data.py`）：
- **测试主题**：测测你是哪种性格原型
- **题目数量**：3 道（可扩展）
- **角色类型**：3 个（智者 A、爱人 B、英雄 C）
- **测试价格**：0.99 元（99分）

---

## ❌ 待完成功能 (25%)

### 🔴 高优先级

#### 1. 微信配置 (阻塞项)
- [ ] **获取 AppSecret**
  - 当前 AppID: `wx33b03872cdabee70`（测试号）
  - 需要在 [微信公众平台](https://mp.weixin.qq.com) 获取
  - 配置位置: `backend/.env`
- [ ] **创建 `.env` 文件**
  ```bash
  cd backend
  cp .env.example .env
  # 编辑 .env，填入真实的 AppID 和 AppSecret
  ```

#### 2. 登录功能联调
- [ ] 配置完成后测试完整登录流程
- [ ] 验证 code → openid 换取是否正常
- [ ] 测试用户新建/查询逻辑

### 🟡 中优先级

#### 3. 支付功能完善
- [ ] 申请微信支付商户号
- [ ] 配置商户参数（MCH_ID、API_KEY）
- [ ] 配置支付回调域名（notify_url）
- [ ] 测试真实支付流程
- [ ] 前端调用 `wx.requestPayment()` 

#### 4. UI/UX 优化
- [ ] 补充缺失的图片资源（角色图片、封面图等）
- [ ] 结果页增加动画效果
- [ ] 加载状态优化（骨架屏）
- [ ] 错误页面设计（404、网络异常）

#### 5. 海报生成
- [ ] 使用 Canvas 绘制海报模板
- [ ] 整合用户头像、角色信息
- [ ] 保存到相册功能测试

### 🟢 低优先级（后续迭代）

#### 6. 功能增强
- [ ] 更多测试主题（MBTI、九型人格等）
- [ ] 题目数量扩展（建议 10-20 题）
- [ ] 分享裂变机制（邀请码、奖励）
- [ ] 用户反馈系统
- [ ] 数据统计后台

#### 7. 运维 & 部署
- [ ] 服务器部署（云服务器 + 域名备案）
- [ ] HTTPS 证书配置
- [ ] 日志监控（已集成 loguru）
- [ ] 数据备份策略

---

## 🚀 快速启动指南

### 环境要求
- Python 3.9+
- Node.js 16+（微信开发者工具）
- SQLite3

### 启动步骤

```bash
# 1. 进入后端目录
cd d:/OpenCode-Project/aiagent/ai-product/role-destiny/backend

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入微信 AppSecret

# 5. 初始化数据库
python init_data.py

# 6. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. 打开微信开发者工具
# 导入 miniprogram 目录
# 修改 app.js 中的 apiBaseUrl 为本机IP
```

### 验证服务
```bash
# 访问健康检查
curl http://127.0.0.1:8000/health
# 返回: {"status": "ok"}

# 查看 API 文档
# 浏览器打开 http://127.0.0.1:8000/docs
```

---

## 📁 关键文件索引

| 文件 | 用途 |
|------|------|
| `backend/app/main.py` | FastAPI 入口、路由注册 |
| `backend/app/config.py` | 配置管理（读取 .env） |
| `backend/app/api/auth.py` | 认证相关 API |
| `backend/app/api/quiz.py` | **核心** 测算算法 |
| `backend/app/api/payment.py` | 支付相关 API |
| `backend/init_data.py` | 数据库初始化 + 示例数据 |
| `backend/schema.sql` | 建表 SQL 脚本 |
| `miniprogram/app.js` | 小程序入口、全局方法 |
| `miniprogram/pages/test/question.js` | 答题页面逻辑 |
| `miniprogram/pages/result/detail.js` | 结果展示 + 付费 |
| `miniprogram/services/` | 前端 API 封装 |

---

## 🐛 已知问题 & 解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 登录失败 | AppSecret 未配置 | 获取密钥并填入 .env |
| 支付提示"需配置商户号" | 未申请微信支付 | 申请商户号并配置参数 |
| 图片显示 404 | 缺少静态资源 | 在 `backend/static/images/` 添加图片 |
| 跨域请求失败 | 开发环境限制 | 已配置 CORS 允许所有来源 |

---

## 📊 项目统计

| 指标 | 数量 |
|------|------|
| 后端 Python 文件 | 27 个 |
| 小程序页面 | 8 个 |
| API 接口 | 13 个 |
| 数据库表 | 7 张 |
| 示例测试题目 | 3 道 |
| 示例角色类型 | 3 个 |
| 代码完成度 | ~75% |
| 可运行程度 | **需要配置 AppSecret** |

---

## 📝 开发日志

### 2026-09-02
- ✅ 完成项目结构搭建
- ✅ 实现全部后端 API 接口
- ✅ 完成小程序主要页面开发
- ✅ 内置示例数据和测试算法
- ⏳ 待配置微信 AppSecret
- ⏳ 待联调登录和支付功能

---

## 🎯 下一步开发计划

### Phase 1: 跑通主流程（预计 1-2 天）
1. [ ] 配置 AppSecret，调通登录
2. [ ] 完整测试一次答题→出结果流程
3. [ ] 修复可能的 bug

### Phase 2: 支付 & 海报（预计 2-3 天）
1. [ ] 申请微信支付（或先跳过）
2. [ ] 实现 Canvas 海报生成
3. [ ] 测试分享功能

### Phase 3: 上线准备（预计 3-5 天）
1. [ ] 补全 UI 资源和样式优化
2. [ ] 服务器部署
3. [ ] 域名备案 + HTTPS
4. [ ] 提交微信审核

---

## 💡 开发提示

### 如何继续开发？
1. 打开此文档了解当前进度
2. 按照「下一步开发计划」执行
3. 遇到问题查看「已知问题」章节
4. 参考「关键文件索引」定位代码

### 代码规范
- 后端遵循 PEP 8
- 前端使用 Page() 构造函数模式
- API 返回统一格式（Schema 校验）
- 错误处理使用 HTTPException

---

**🎉 项目已完成大部分核心功能，距离上线只差微信配置和细节优化！**

**继续加油！💪**
