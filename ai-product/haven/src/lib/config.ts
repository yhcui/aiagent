// 从环境变量读取凭证（.env.local 不提交到 Git）
// 默认值仅用于本地开发，生产环境请配置 .env.local
export const AUTH_USERNAME = process.env.AUTH_USERNAME ?? 'Y';
export const AUTH_PASSWORD = process.env.AUTH_PASSWORD ?? '1';
export const SESSION_SECRET = process.env.SESSION_SECRET ?? 'haven-session-secret-2026';
