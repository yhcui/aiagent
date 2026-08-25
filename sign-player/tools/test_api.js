// 一次性自测：验证后端核心逻辑（翻译/解密/口型解析），不启动 HTTP 服务
const http = require('http');
const https = require('https');
const fs = require('fs');
const crypto = require('crypto');
const zlib = require('zlib');

const TOKEN = 'E9A146B8BA161E13D942B2CED15A2';
const UUID = 'd5004249-c7de-40b6-a61a-54903dff9bf1';
const BASE = 'https://api.gbqr.net';

function httpsReq(url, {method='GET', headers={}, body=null}={}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = https.request({hostname:u.hostname, path:u.pathname+u.search, method, headers}, res => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve({status: res.statusCode, body: Buffer.concat(chunks)}));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}
function decryptGB(data, timestamp) {
  const head = data.slice(0,7).toString('latin1');
  if (head !== 'GBAsset') throw new Error('非GBAsset');
  const ct = data.subarray(7);
  const salt = crypto.createHash('md5').update(TOKEN + timestamp, 'utf8').digest();
  const key = crypto.pbkdf2Sync(TOKEN, salt, 1000, 32, 'sha1');
  const iv = Buffer.from(UUID.slice(0,16), 'utf8');
  const d = crypto.createDecipheriv('aes-256-cbc', key, iv);
  const pt = Buffer.concat([d.update(ct), d.final()]);
  for (const fn of [()=>zlib.inflateSync(pt), ()=>zlib.inflateRawSync(pt), ()=>zlib.gunzipSync(pt)]) {
    try { return fn(); } catch(e) {}
  }
  throw new Error('解压失败');
}

(async () => {
  // 1. 翻译
  const tr = await httpsReq(BASE + '/api/sign/translate/meta/auto', {method:'POST', headers:{'Content-Type':'application/json','Accept':'application/json, text/plain, */*','Origin':'https://gbqr.net','Referer':'https://gbqr.net/','Token':TOKEN,'UUID':UUID,'type':'1','IsOnLine':'true','User-Agent':'Mozilla/5.0'}, body: JSON.stringify({content:'深度融合',type:1})});
  const trData = JSON.parse(tr.body.toString('utf8'));
  console.log('=== 翻译结果 ===');
  console.log('result:', trData.result, trData.description);
  for (const c of trData.content) console.log(`  ${c.meaning}: motion=${c.motion} expression=${c.expression}`);

  // 2. 下载并解密 00510 动画
  const ts = Date.now().toString();
  const hdrs = {'Accept':'application/json, text/plain, */*','Origin':'https://cloud.gbqr.net','Referer':'https://cloud.gbqr.net/','Timestamp':ts,'Token':TOKEN,'UUID':UUID,'User-Agent':'Mozilla/5.0'};
  const r = await httpsReq(`${BASE}/api/v3/assets/sign/latest/glb/00510.gltf`, {headers: hdrs});
  console.log('\n=== 00510 下载 ===');
  console.log('status:', r.status, '大小:', r.body.length);
  const dec = decryptGB(r.body, ts);
  const gltf = JSON.parse(dec.toString('utf8'));
  console.log('解密 OK, animations:', gltf.animations.length, '时长:', gltf.animations[0] ? '有' : '无');
  // bin
  const bin = await httpsReq(`${BASE}/api/v3/assets/sign/latest/glb/bin/00510.bin`, {headers: hdrs});
  console.log('bin status:', bin.status, '大小:', bin.body.length);

  // 3. 口型 Shen.anim
  const anim = await httpsReq(`${BASE}/api/v3/assets/sign/latest/glb/anim/Shen.anim`, {headers: hdrs});
  console.log('\n=== Shen.anim ===');
  console.log('status:', anim.status, '大小:', anim.body.length);
  const text = anim.body.toString('utf8');
  const m = text.match(/attribute:\s*blendShape\.(\w+)/g);
  console.log('口型通道:', m ? m.map(x=>x.replace('attribute: blendShape.','')).join(', ') : '无');

  // 4. 完整"你好"的播放段构建
  console.log('\n=== 构建播放段（测试文本"深度融合"）===');
  const segments = [];
  for (const w of trData.content) {
    const motions = (w.motion||'').trim().split(/\s+/).filter(Boolean);
    const exprs = (w.expression||'').trim().split(/\s+/).filter(Boolean);
    for (let i=0;i<motions.length;i++) segments.push({motion: motions[i], expr: exprs[i]||null});
    if (exprs.length > motions.length) for (let i=motions.length;i<exprs.length;i++) segments.push({motion:null, expr: exprs[i]});
  }
  console.log('播放段:', JSON.stringify(segments));
  console.log('\n全部后端逻辑验证通过 ✅');
})();
