# Haven · Python 版

由 Next.js 版本迁移而来：**FastAPI + React(Vite) + SQLite**，界面与功能保持一致。

## 目录结构

```
haven-py/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 入口、CORS、路由注册
│   │   ├── database.py      # SQLite 连接与建表
│   │   ├── auth.py          # 凭证校验 + 会话票据
│   │   ├── deps.py          # 登录校验依赖
│   │   └── routers/
│   │       ├── auth.py      # 登录 / 登出
│   │       └── ideas.py     # 想法增删改查
│   ├── requirements.txt
│   └── data/haven.db        # 数据库（首次启动自动创建）
│
└── frontend/                # React 前端
    ├── src/
    │   ├── main.tsx         # 入口
    │   ├── App.tsx          # 路由
    │   ├── api/             # 接口层（cookie 鉴权）
    │   ├── components/
    │   │   ├── layout/Sidebar.tsx
    │   │   └── ProtectedRoute.tsx   # 路由守卫
    │   ├── features/ideas/  # 想法模块组件
    │   ├── pages/           # 登录页 / 想法页
    │   └── styles/globals.css       # 全量样式（原样迁移）
    └── vite.config.ts       # 含 /api 开发代理
```

---

## 本地开发

### 一、启动后端

#### Windows（PowerShell）

```powershell
cd backend

python -m venv .venv
.\.venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> 若 `activate` 提示执行策略受限，先执行一次：
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

#### Linux / macOS

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

激活成功后命令行前会出现 `(.venv)` 前缀，表示已进入虚拟环境。

#### 验证后端

浏览器打开 **http://localhost:8000/docs** —— FastAPI 自动生成的接口文档，可直接在页面上调试所有接口。

或命令行验证：

```bash
curl http://localhost:8000/api/health
# 返回 {"status":"ok"}
```

### 二、启动前端

新开一个终端（后端保持运行）：

```bash
cd frontend
npm install
npm run dev
```

打开 **http://localhost:5173**，用默认账号 `Y` / `1` 登录。

> 前端 `/api` 请求已通过 Vite 代理转发到后端 8000 端口，无需手动配 CORS。

---

## 接口一览

| 方法 | 路径 | 说明 | 需要登录 |
|------|------|------|---------|
| POST | `/api/auth/login` | 登录，下发 Cookie | 否 |
| POST | `/api/auth/logout` | 登出，清除 Cookie | 否 |
| GET | `/api/ideas` | 想法列表（未完成优先） | 是 |
| POST | `/api/ideas` | 新建想法 | 是 |
| PATCH | `/api/ideas/{id}` | 切换完成状态 | 是 |
| DELETE | `/api/ideas/{id}` | 删除想法 | 是 |
| GET | `/api/health` | 健康检查 | 否 |

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AUTH_USERNAME` | `Y` | 登录用户名 |
| `AUTH_PASSWORD` | `1` | 登录密码 |
| `SESSION_SECRET` | `haven-session-secret-2026` | 票据签名密钥，**生产必须改** |
| `DB_DIR` | `backend/data` | 数据库目录 |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | 允许的前端来源，多个用逗号分隔 |
| `COOKIE_SECURE` | `false` | HTTPS 部署时设为 `true` |

> ⚠️ 不设置凭证则任何人可用默认的 `Y` / `1` 登录，生产环境务必修改。

Windows 临时设置（PowerShell）：

```powershell
$env:AUTH_USERNAME="admin"
$env:AUTH_PASSWORD="你的密码"
$env:SESSION_SECRET="随机字符串"
```

---

## 生产部署（Ubuntu）

### 后端

```bash
cd /var/www/haven-py/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export AUTH_USERNAME=你的用户名
export AUTH_PASSWORD=你的强密码
export SESSION_SECRET=$(openssl rand -hex 32)
export ALLOWED_ORIGINS=https://your-domain.com
export COOKIE_SECURE=true

# 用 systemd 守护（或 pm2）
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd /var/www/haven-py/frontend
npm install
npm run build      # 产物在 dist/
```

### Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态资源
    location / {
        root /var/www/haven-py/frontend/dist;
        try_files $uri $uri/ /index.html;   # SPA 路由回退，必须
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 后端接口
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> `try_files ... /index.html` 是 SPA 必需的，否则刷新 `/ideas` 会 404。

HTTPS：`sudo certbot --nginx -d your-domain.com`

---

## 与 Next.js 版的主要差异

| 项 | Next.js 版 | Python 版 |
|---|---|---|
| 后端运行时 | Node.js | Python (FastAPI) |
| 数据库 | `node:sqlite` | Python 内置 `sqlite3`（同一 db 文件） |
| 路由守卫 | `middleware.ts` | 前端 `ProtectedRoute` + 后端 Depends 双重校验 |
| 样式 | Tailwind + 纯 CSS | 纯 CSS（Tailwind 已移除） |
| 接口文档 | 无 | FastAPI 自动生成 `/docs` |
| 部署形态 | 单服务 | 前端静态 + 后端 API 两个服务 |

## 数据迁移

两版使用**完全相同的表结构**，把原 `haven/data/haven.db` 复制到 `haven-py/backend/data/` 即可，无需转换。
