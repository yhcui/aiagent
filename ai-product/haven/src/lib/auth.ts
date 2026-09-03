// 纯 JS 实现，无 node: 依赖，可用于 middleware 和 API Route
// 凭证从环境变量读取
export const AUTH_USERNAME = process.env.AUTH_USERNAME ?? 'Y';
export const AUTH_PASSWORD = process.env.AUTH_PASSWORD ?? '1';
export const SESSION_SECRET = process.env.SESSION_SECRET ?? 'haven-session-secret-2026';

const SESSION_MAX_AGE = 7 * 24 * 60 * 60 * 1000; // 7 天

export function verifyCredentials(username: string, password: string): boolean {
  return username === AUTH_USERNAME && password === AUTH_PASSWORD;
}

// 生成 token: 时间戳.随机字符串
export function createToken(): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 10);
  const sig = simpleHash(`${ts}.${rand}.${SESSION_SECRET}`);
  return `${ts}.${rand}.${sig}`;
}

export function verifyToken(token: string): boolean {
  if (!token) return false;
  const parts = token.split('.');
  if (parts.length !== 3) return false;
  const [ts, rand, sig] = parts;
  const expectedSig = simpleHash(`${ts}.${rand}.${SESSION_SECRET}`);
  if (sig !== expectedSig) return false;
  const age = Date.now() - parseInt(ts, 36);
  return age > 0 && age < SESSION_MAX_AGE;
}

// 简单的 hash 函数（避免引入 crypto 依赖）
function simpleHash(str: string): string {
  let h = 5381;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) + h) ^ str.charCodeAt(i);
    h = h >>> 0; // 转成无符号 32 位
  }
  return h.toString(36);
}
