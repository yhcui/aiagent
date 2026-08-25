#!/usr/bin/env node
/**
 * gbqr_login.js —— gbqr.net 登录 / 取 token+uid / 查数字人模型清单
 *
 * 对应前端 SDK 的 Ve.login()，两步：
 *   1) POST /api/Terminal/ThreeJSToLogin
 *        body: {"content":{"obj1":"<账号>"}}
 *        resp: {"result":1,"content":"xxx=..;\nuid=..;\neid=..;\nprivilege=..;\ntoken=.."}
 *        解析: content.split(';\n').map(s => s.split('=')[1]) -> [_, uid, eid, privilege, token]
 *   2) POST /api/Terminal/GetDigitPersonAuthByUserId
 *        body: {"content":{"token":..,"uid":..,"memberID":..}}
 *        resp: content.dpList = 该账号可用的数字人模型列表
 *
 * 注意：第 1 步的 <账号> 是对方签发的租户/应用标识，抓包里看不到（由父页面
 * postMessage({type:'login',data:{name:...}}) 传进 iframe）。用 --capture 打印
 * 在浏览器控制台抓它的代码片段。
 *
 * 用法：
 *   node gbqr_login.js --capture                 # 打印"如何抓到 name"的控制台片段
 *   node gbqr_login.js --name <账号>              # 完整登录，拿新 token/uid
 *   node gbqr_login.js --name <账号> --save       # 同上，并写出 auth.json
 *   node gbqr_login.js                           # 无 name：用内置 token 验证 + 查模型清单
 *   node gbqr_login.js --token X --uuid Y --verify 你好
 *   node gbqr_login.js --config default          # 额外拉每个模型的渲染配置
 *   node gbqr_login.js --name <账号> --json       # 只输出 JSON，便于管道/脚本消费
 *
 * 依赖：Node >= 18（内置 fetch，零外部依赖）
 */
'use strict';

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------- 常量

const API = 'https://api.gbqr.net';
const EP = {
  login: API + '/api/Terminal/ThreeJSToLogin',
  models: API + '/api/Terminal/GetDigitPersonAuthByUserId',
  config: API + '/api/OpenPlatform/GetThreeJsConfigStrJson',
  translate: API + '/api/sign/translate/meta/auto',
};

const UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36';
const BASE_HEADERS = {
  Accept: 'application/json, text/plain, */*',
  'Accept-Language': 'zh-CN,zh;q=0.9',
  'Content-Type': 'application/json',
  Origin: 'https://gbqr.net',
  Referer: 'https://gbqr.net/',
  'User-Agent': UA,
};

// 已知可用凭据（来自此前抓包），仅在未提供 --name/--token 时兜底
const FALLBACK = {
  token: 'E9A146B8BA161E13D942B2CED15A2',
  uid: 'd5004249-c7de-40b6-a61a-54903dff9bf1',
};

// ---------------------------------------------------------------- CLI

function parseArgs(argv) {
  const o = {
    name: null,
    token: null,
    uid: null,
    verify: null, // 用于验证 token 的词，null=不验证
    config: null, // configCode，非空则拉渲染配置
    save: null, // 输出路径
    json: false,
    raw: false,
    capture: false,
    timeout: 25000,
  };
  const flags = new Set(['json', 'raw', 'capture', 'save', 'verify', 'models', 'help', 'h']);
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) throw new Error(`无法识别的参数: ${a}`);
    const key = a.slice(2);
    // --save / --verify 支持"带值"和"纯开关"两种写法
    const next = argv[i + 1];
    const nextIsValue = next !== undefined && !next.startsWith('--');
    const val = flags.has(key) ? (nextIsValue ? (i++, next) : true) : argv[++i];
    if (val === undefined) throw new Error(`参数 --${key} 缺少值`);
    switch (key) {
      case 'help': case 'h': printHelp(); process.exit(0); break;
      case 'name': case 'account': o.name = String(val); break;
      case 'token': o.token = String(val); break;
      case 'uuid': case 'uid': o.uid = String(val); break;
      case 'verify': o.verify = val === true ? '真实' : String(val); break;
      case 'config': o.config = val === true ? 'default' : String(val); break;
      case 'save': o.save = val === true ? path.resolve(__dirname, '..', 'out', 'auth.json') : path.resolve(String(val)); break;
      case 'models': break; // 默认就会查，保留兼容
      case 'json': o.json = true; break;
      case 'raw': o.raw = true; break;
      case 'capture': o.capture = true; break;
      case 'timeout': o.timeout = Number(val); break;
      default: throw new Error(`未知参数 --${key}`);
    }
  }
  return o;
}

function printHelp() {
  const doc = fs.readFileSync(__filename, 'utf8').split('*/')[0];
  console.log(doc.replace(/^\/\*\*?/, '').replace(/^ ?\* ?/gm, ''));
}

// ---------------------------------------------------------------- 输出

let QUIET = false;
const say = (...a) => { if (!QUIET) console.log(...a); };
const log = {
  step: (...a) => say('\n▶', ...a),
  info: (...a) => say('  ', ...a),
  ok: (...a) => say('  ✓', ...a),
  warn: (...a) => say('  !', ...a),
};

// ---------------------------------------------------------------- HTTP

async function postJson(url, payload, { timeout = 25000, retries = 2 } = {}) {
  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt++) {
    if (attempt) await new Promise(r => setTimeout(r, 600 * attempt));
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), timeout);
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: BASE_HEADERS,
        body: JSON.stringify(payload),
        signal: ctl.signal,
      });
      const text = await res.text();
      if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText} @ ${url}\n${text.slice(0, 300)}`);
      try { return JSON.parse(text); }
      catch { throw new Error(`响应不是 JSON @ ${url}\n${text.slice(0, 300)}`); }
    } catch (e) {
      lastErr = e.name === 'AbortError' ? new Error(`请求超时 ${timeout}ms @ ${url}`) : e;
    } finally {
      clearTimeout(timer);
    }
  }
  throw lastErr;
}

// ---------------------------------------------------------------- 步骤 1：登录

/**
 * 严格复刻 SDK：content 按 ';\n' 切，每段取 '=' 右边，位置 1..4 = uid/eid/privilege/token。
 * 同时做一次 key=value 正则兜底，两者不一致时告警（防对方调整字段顺序）。
 */
function parseLoginContent(content) {
  const raw = String(content);
  const segs = raw.split(';\n');
  const byPos = segs.map(s => (s.split('=')[1] || '').trim());
  const positional = { uid: byPos[1], eid: byPos[2], privilege: byPos[3], token: byPos[4] };

  const kv = {};
  for (const m of raw.matchAll(/([A-Za-z_][\w]*)\s*=\s*([^;\r\n]*)/g)) kv[m[1].toLowerCase()] = m[2].trim();
  const byKey = { uid: kv.uid, eid: kv.eid, privilege: kv.privilege, token: kv.token };

  const mismatch = ['uid', 'eid', 'privilege', 'token']
    .filter(k => byKey[k] !== undefined && positional[k] !== undefined && byKey[k] !== positional[k]);

  // 以 key 解析为准（更稳），位置解析仅作对照
  const out = {
    uid: byKey.uid || positional.uid,
    eid: byKey.eid || positional.eid,
    privilege: byKey.privilege || positional.privilege,
    token: byKey.token || positional.token,
  };
  return { auth: out, segments: segs, positional, byKey, mismatch, raw };
}

async function doLogin(name, opt) {
  log.step(`登录 ThreeJSToLogin  (obj1="${name}")`);
  const d = await postJson(EP.login, { content: { obj1: name } }, { timeout: opt.timeout });
  if (opt.raw) log.info('原始响应:', JSON.stringify(d));
  if (d.result !== 1) {
    throw new Error(`登录被拒绝 result=${d.result} description=${d.description || '(无)'}\n` +
      '  --name 的值需要是对方签发的账号/应用标识，用 --capture 看怎么从浏览器里抓。');
  }
  const p = parseLoginContent(d.content);
  if (!p.auth.token || !p.auth.uid) {
    throw new Error(`登录响应缺少 token/uid，原始 content:\n${p.raw}`);
  }
  log.ok(`token      = ${p.auth.token}`);
  log.ok(`uid        = ${p.auth.uid}`);
  log.info(`eid        = ${p.auth.eid ?? '(无)'}`);
  log.info(`privilege  = ${p.auth.privilege ?? '(无)'}`);
  if (p.segments.length && p.segments[0]) log.info(`段[0]      = ${p.segments[0]}  (SDK 里丢弃不用)`);
  if (p.mismatch.length) {
    log.warn(`字段顺序与 SDK 假设不一致: ${p.mismatch.join(', ')}，已按 key=value 解析。原始 content:`);
    log.warn(`  ${p.raw.replace(/\n/g, '\\n')}`);
  }
  return p.auth;
}

// ---------------------------------------------------------------- 步骤 2：模型清单

async function fetchModels(auth, opt) {
  log.step('查询数字人模型清单 GetDigitPersonAuthByUserId');
  const d = await postJson(EP.models, {
    content: { token: auth.token, uid: auth.uid, memberID: auth.uid },
  }, { timeout: opt.timeout });
  if (opt.raw) log.info('原始响应:', JSON.stringify(d));
  if (d.result !== 1) {
    log.warn(`result=${d.result} description=${d.description || '(无)'}  -> token 可能已失效`);
    return { ok: false, result: d.result, description: d.description, list: [] };
  }
  const list = (d.content && d.content.dpList) || [];

  // 同一 digitPersonCode 常有多条（不同授权记录），按 code 去重后才是真实模型数
  const uniq = [];
  const seen = new Set();
  for (const m of list) {
    const code = m.digitPersonCode || m.resourceName;
    if (seen.has(code)) continue;
    seen.add(code);
    uniq.push(m);
  }

  log.ok(`授权记录 ${list.length} 条 -> 去重后 ${uniq.length} 个模型`);
  const show = opt.raw ? uniq : uniq.slice(0, 15);
  for (const m of show) {
    log.info(`- ${String(m.digitPersonName ?? '?').padEnd(12)} code=${String(m.digitPersonCode ?? '?').padEnd(18)} path=${m.resourcePath ?? '?'}`);
  }
  if (show.length < uniq.length) log.info(`... 其余 ${uniq.length - show.length} 个已省略（加 --raw 看全部，或 --save 落盘）`);

  const extra = Object.keys(d.content || {}).filter(k => k !== 'dpList');
  if (extra.length) log.info(`content 其他字段: ${extra.map(k => `${k}=${JSON.stringify(d.content[k])}`).join('  ')}`);
  return { ok: true, count: list.length, uniqueCount: uniq.length, list, unique: uniq, extra };
}

// ---------------------------------------------------------------- 可选：渲染配置

async function fetchConfig(auth, model, configCode, opt) {
  const code = model.resourceName || model.digitPersonCode;
  const d = await postJson(EP.config, {
    content: { token: auth.token, uid: auth.uid, digitPersonCode: code, configCode },
  }, { timeout: opt.timeout });
  if (d.result !== 1) {
    log.warn(`${code}/${configCode} 配置获取失败 result=${d.result}`);
    return null;
  }
  let parsed = d.content;
  if (typeof parsed === 'string') { try { parsed = JSON.parse(parsed); } catch { /* 保持字符串 */ } }
  log.ok(`${code}/${configCode} 配置 OK  ${typeof parsed === 'object' ? 'keys=' + Object.keys(parsed).join(',') : String(parsed).slice(0, 80)}`);
  return { digitPersonCode: code, configCode, config: parsed };
}

// ---------------------------------------------------------------- 可选：验证 token

async function verifyToken(auth, word, opt) {
  log.step(`验证 token（翻译 "${word}"）`);
  const res = await fetch(EP.translate, {
    method: 'POST',
    headers: { ...BASE_HEADERS, token: auth.token, uuid: auth.uid, IsOnLine: 'true', type: '1' },
    body: JSON.stringify({ content: word, type: 1 }),
  });
  const text = await res.text();
  let d;
  try { d = JSON.parse(text); }
  catch { log.warn(`响应不是 JSON: ${text.slice(0, 200)}`); return { ok: false }; }
  if (opt.raw) log.info('原始响应:', JSON.stringify(d));
  if (d.result !== 1) {
    log.warn(`result=${d.result} description=${d.description || '(无)'}  -> token 无效或无权限`);
    return { ok: false, result: d.result, description: d.description };
  }
  const items = Array.isArray(d.content) ? d.content : [];
  log.ok(`token 有效，返回 ${items.length} 个手语词: ${items.map(i => i.meaning).join(' ')}`);
  items.forEach(i => log.info(`- ${i.meaning}  motion=${i.motion}  expression=${i.expression}  behavior=${i.behavior}`));
  return { ok: true, items };
}

// ---------------------------------------------------------------- 抓 name 的片段

function printCapture() {
  console.log(`
如何拿到 --name 的值（对方签发的账号/应用标识）
-------------------------------------------------
它不在任何网络请求里，是父页面用 postMessage 传给手语 iframe 的。
打开 https://gbqr.net/ ，F12 控制台粘贴下面这段，然后触发一次手语翻译：

// 拦截发往 iframe 的 postMessage
(() => {
  const orig = window.HTMLIFrameElement.prototype.contentWindow;
  const patch = w => {
    if (!w || w.__patched) return; w.__patched = true;
    const p = w.postMessage.bind(w);
    w.postMessage = function (msg, ...rest) {
      if (msg && msg.type === 'login') console.log('%c[LOGIN]', 'color:#0a0;font-weight:bold', JSON.stringify(msg.data));
      else if (msg && msg.type) console.log('[MSG]', msg.type, JSON.stringify(msg.data ?? null));
      return p(msg, ...rest);
    };
  };
  document.querySelectorAll('iframe').forEach(f => patch(f.contentWindow));
  new MutationObserver(() => document.querySelectorAll('iframe').forEach(f => patch(f.contentWindow)))
    .observe(document.documentElement, { childList: true, subtree: true });
  console.log('已挂钩，去点一次"翻译"。找 [LOGIN] 那行里的 name 字段。');
})();

若手语插件本身就在当前页（非 iframe），改用：
  const k = window.yiyu && window.yiyu.kernel; // 存在则说明就在本页
  // 直接读已登录凭据：SDK 把它缓存在闭包里，可从任意一次资源请求头 Token/UUID 反推
拿到后：
  node gbqr_login.js --name <抓到的name> --save
`.trim());
}

// ---------------------------------------------------------------- 主流程

async function main() {
  const opt = parseArgs(process.argv);
  if (opt.capture) { printCapture(); return; }
  QUIET = opt.json;

  const result = {
    generatedAt: new Date().toISOString(),
    api: API,
    mode: null,
    auth: null,
    models: null,
    configs: null,
    verify: null,
  };

  // 1. 取凭据
  let auth;
  if (opt.name) {
    result.mode = 'login';
    auth = await doLogin(opt.name, opt);
    result.account = opt.name;
  } else {
    result.mode = 'existing';
    auth = { token: opt.token || FALLBACK.token, uid: opt.uid || FALLBACK.uid };
    log.step('未提供 --name，使用现有凭据');
    log.info(`token = ${auth.token}${opt.token ? '' : '  (内置兜底值)'}`);
    log.info(`uid   = ${auth.uid}${opt.uid ? '' : '  (内置兜底值)'}`);
    log.info('要现场登录换新 token，请加 --name <账号>；不知道 name 就先跑 --capture');
  }
  result.auth = auth;

  // 2. 模型清单（同时也是一次 token 有效性检查）
  const models = await fetchModels(auth, opt);
  result.models = models;

  // 3. 渲染配置（可选，默认只拉前 3 个，避免一次打 100+ 请求）
  const models2 = models.unique || [];
  if (opt.config && models2.length) {
    const targets = models2.slice(0, 3);
    log.step(`拉取渲染配置 configCode="${opt.config}"（前 ${targets.length} 个模型）`);
    result.configs = [];
    for (const m of targets) {
      const c = await fetchConfig(auth, m, opt.config, opt);
      if (c) result.configs.push(c);
      await new Promise(r => setTimeout(r, 400));
    }
  }

  // 4. 验证（可选）
  if (opt.verify) result.verify = await verifyToken(auth, opt.verify, opt);

  // 5. 落盘
  if (opt.save) {
    fs.mkdirSync(path.dirname(opt.save), { recursive: true });
    fs.writeFileSync(opt.save, JSON.stringify(result, null, 2));
    log.step('已写出');
    log.ok(opt.save);
  }

  if (opt.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  console.log('\n================ 结果 ================');
  console.log(`token : ${auth.token}`);
  console.log(`uid   : ${auth.uid}`);
  if (auth.eid) console.log(`eid   : ${auth.eid}`);
  if (auth.privilege) console.log(`权限  : ${auth.privilege}`);
  if (models.ok) {
    const names = (models.unique || []).map(m => m.digitPersonName || m.resourceName);
    console.log(`模型  : ${models.uniqueCount} 个（${models.count} 条授权记录）`);
    console.log(`        ${names.slice(0, 12).join('、')}${names.length > 12 ? ` … 等 ${names.length} 个` : ''}`);
  } else {
    console.log('模型  : 查询失败（token 可能已失效）');
  }
  console.log('\n直接喂给爬取脚本：');
  console.log(`  node gbqr_pack.js --token ${auth.token} --uuid ${auth.uid} --words 真实 --decode-meshopt --glb`);
}

main().catch(e => {
  console.error('\n✗ 失败:', e.message);
  if (process.env.DEBUG) console.error(e.stack);
  process.exit(1);
});
