# Haven · 个人工作台

温暖、私属、专注的个人空间。支持登录鉴权、想法管理（增删改查、完成切换）等功能。

## 技术栈

| 类别 | 选型 |
|------|------|
| 框架 | Next.js 14 (App Router) + React 18 |
| 语言 | TypeScript |
| 样式 | Tailwind CSS |
| 动效 | Framer Motion |
| 图标 | lucide-react |
| 数据库 | node:sqlite（Node.js 22 内置，零原生依赖） |
| 鉴权 | Cookie + 自实现 Token（HMAC 签名），Middleware 路由守卫 |

## 环境要求

- **Node.js ≥ 22.0.0**（使用内置 `node:sqlite` 模块）
- **pnpm**（推荐）或 npm / yarn
- 操作系统：Windows / macOS / Linux 均可

## 目录结构

```
haven/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── layout.tsx            # 根布局（含侧边栏）
│   │   ├── page.tsx              # 首页
│   │   ├── login/page.tsx        # 登录页
│   │   └── api/
│   │       ├── auth/
│   │       │   ├── login/route.ts    # 登录接口
│   │       │   └── logout/route.ts   # 登出接口
│   │       └── ideas/route.ts        # 想法 CRUD 接口
│   ├── components/layout/Sidebar.tsx # 侧边栏（含退出按钮）
│   ├── features/ideas/              # 想法功能模块
│   ├── lib/
│   │   ├── auth.ts                 # 鉴权工具（Token 签发/验证）
│   │   ├── config.ts               # 凭证配置（读环境变量）
│   │   └── db/index.ts             # SQLite 数据库单例
│   ├── middleware.ts              # 路由守卫（未登录重定向）
│   └── styles/globals.css         # 全局样式
├── data/                         # SQLite 数据库文件（自动生成，已 gitignore）
├── .env.local                    # 环境变量（需手动创建，已 gitignore）
├── .env.local.example            # 环境变量示例
├── next.config.mjs               # Next.js 配置
├── tailwind.config.ts            # Tailwind 配置
├── tsconfig.json                 # TypeScript 配置
└── package.json
```

## 凭证配置

登录凭证通过环境变量配置，**不提交到 Git**。

1. 复制示例文件：
   ```bash
   cp .env.local.example .env.local
   ```
2. 编辑 `.env.local`，设置自己的用户名和密码：
   ```env
   AUTH_USERNAME=Y
   AUTH_PASSWORD=1
   SESSION_SECRET=haven-session-secret-2026-change-in-production
   ```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AUTH_USERNAME` | 登录用户名 | `Y` |
| `AUTH_PASSWORD` | 登录密码 | `1` |
| `SESSION_SECRET` | Token 签名密钥（生产环境务必修改） | `haven-session-secret-2026` |

## 本地开发

```bash
# 安装依赖
pnpm install

# 创建环境变量文件
cp .env.local.example .env.local

# 启动开发服务器
pnpm dev
```

访问 [http://localhost:3000](http://localhost:3000)，会自动跳转到登录页。

## 打包编译

```bash
# 生产构建
pnpm build
```

构建产物输出到 `.next/` 目录。

## 生产部署

### 方式一：Node.js 服务器部署

```bash
# 1. 安装依赖（含 devDependencies，构建需要）
pnpm install

# 2. 配置环境变量
cp .env.local.example .env.local
# 编辑 .env.local 设置凭证

# 3. 构建
pnpm build

# 4. 启动生产服务器（默认监听 3000 端口）
pnpm start

# 指定端口
PORT=8080 pnpm start
```

### 方式二：PM2 进程守护

```bash
# 安装 PM2
npm install -g pm2

# 构建
pnpm build

# 用 PM2 启动
pm2 start pnpm --name haven -- start

# 查看日志
pm2 logs haven

# 设置开机自启
pm2 save
pm2 startup
```

### 方式三：Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
EXPOSE 3000
CMD ["pnpm", "start"]
```

构建并运行：

```bash
docker build -t haven .
docker run -d -p 3000:3000 \
  -e AUTH_USERNAME=Y \
  -e AUTH_PASSWORD=1 \
  -e SESSION_SECRET=your-secret \
  -v $(pwd)/data:/app/data \
  --name haven haven
```

## 数据存储

- 数据库文件位于 `data/haven.db`（SQLite，WAL 模式）
- 数据库文件已加入 `.gitignore`，不会提交到仓库
- 首次启动自动创建表结构（`ideas` 表）
- 备份：直接复制 `data/haven.db` 文件即可

## Nginx 反向代理示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 鉴权机制

- 未登录用户访问任何页面会被 `middleware.ts` 重定向到 `/login`
- 登录成功后服务端设置 `session` Cookie（httpOnly，7 天有效期）
- Token 包含时间戳 + 随机串 + HMAC 签名，篡改即失效
- `/api/auth/*` 路径免鉴权（登录/登出接口本身需要放行）

## 常见问题

**Q: 启动报错 `Cannot find module 'node:sqlite'`？**
A: 确认 Node.js 版本 ≥ 22，可用 `node -v` 检查。

**Q: 登录提示"网络错误"？**
A: 检查 `.env.local` 是否存在、dev server 是否正常运行、浏览器控制台是否有报错。

**Q: 构建时 `autoprefixer` 找不到？**
A: 确保使用 pnpm 且存在 `.npmrc`（内容为 `shamefully-hoist=true`）。

**Q: 如何重置数据库？**
A: 删除 `data/haven.db`、`data/haven.db-wal`、`data/haven.db-shm`，重启应用自动重建。
