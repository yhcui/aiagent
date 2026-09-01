# 角色测算小程序 - Python后端

基于 Python + FastAPI + SQLite 的轻量级技术栈实现的角色测算小程序后端服务。

## 技术栈

- **Web框架**: Python 3.9+ / FastAPI
- **数据库**: SQLite 3（单文件嵌入式数据库）
- **缓存**: cachetools TTLCache（纯内存LRU缓存）
- **图片处理**: Pillow
- **数据校验**: Pydantic 2.0

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入微信相关配置
```

### 3. 初始化数据库

```bash
python init_data.py
```

### 4. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python app/main.py
```

### 5. 访问API文档

打开浏览器访问: http://localhost:8000/docs

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI入口
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库配置
│   ├── models/           # 数据模型
│   ├── schemas/          # Pydantic模型
│   ├── services/         # 业务逻辑
│   └── api/              # API路由
├── static/               # 静态文件
├── data/                 # 数据文件
├── schema.sql            # 数据库建表SQL
├── requirements.txt      # 依赖列表
└── init_data.py          # 初始化脚本
```

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 小程序登录 |
| `/api/auth/user` | GET | 获取用户信息 |
| `/api/tests` | GET | 获取测试列表 |
| `/api/tests/{id}` | GET | 获取测试详情 |
| `/api/quiz/submit` | POST | 提交测试 |
| `/api/quiz/result/{id}` | GET | 获取测试结果 |
| `/api/payment/create` | POST | 发起支付 |
| `/api/poster/generate` | GET | 生成海报 |

## 微信配置

在 `.env` 文件中配置以下微信参数：

```
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_MCH_ID=your_mch_id
WECHAT_API_KEY=your_api_key
```

## 生产部署

### 使用systemd

```bash
sudo cp role-destiny.service /etc/systemd/system/
sudo systemctl enable role-destiny
sudo systemctl start role-destiny
```

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/backend/static;
        expires 30d;
    }
}
```

## 优势对比

| 对比项 | 原方案(Node.js) | 新方案(Python) |
|--------|----------------|----------------|
| 服务数量 | 3个(Node+MySQL+Redis) | 1个 |
| 内存占用 | >1GB | <200MB |
| 月成本 | ¥200-500 | ¥50-200 |
| 复杂度 | 高 | 低 |
| 开发效率 | 中 | 高 |
