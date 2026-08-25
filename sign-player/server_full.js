const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const zlib = require('zlib');

const TOKEN = 'E9A146B8BA161E13D942B2CED15A2';
const UUID = 'd5004249-c7de-40b6-a61a-54903dff9bf1';
const BASE = 'https://api.gbqr.net';
const PORT = 8137;

function httpsReq(url, {method='GET', headers={}, body=null}={}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = https.request({hostname:u.hostname, path:u.pathname+u.search, method, headers}, res => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve({status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks)}));
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

// 翻译
async function translate(text) {
  const body = JSON.stringify({content: text, type: 1});
  const r = await httpsReq(BASE + '/api/sign/translate/meta/auto', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/plain, */*',
      'Origin': 'https://gbqr.net',
      'Referer': 'https://gbqr.net/',
      'Token': TOKEN, 'UUID': UUID, 'type': '1', 'IsOnLine': 'true',
      'User-Agent': 'Mozilla/5.0'
    },
    body
  });
  return JSON.parse(r.body.toString('utf8'));
}

// 下载并解密 gltf，返回自包含 gltf JSON（bin 内嵌 base64）
async function fetchSignGltf(id) {
  const ts = Date.now().toString();
  const headers = {'Accept':'application/json, text/plain, */*','Origin':'https://cloud.gbqr.net','Referer':'https://cloud.gbqr.net/','Timestamp':ts,'Token':TOKEN,'UUID':UUID,'User-Agent':'Mozilla/5.0'};
  const r = await httpsReq(`${BASE}/api/v3/assets/sign/latest/glb/${id}.gltf`, {headers});
  if (r.status !== 200) throw new Error('gltf ' + r.status);
  const dec = decryptGB(r.body, ts);
  const gltf = JSON.parse(dec.toString('utf8'));
  // 内嵌 bin
  for (const b of gltf.buffers) {
    if (b.uri && !b.uri.startsWith('data:')) {
      const br = await httpsReq(`${BASE}/api/v3/assets/sign/latest/glb/bin/${b.uri}`, {headers});
      if (br.status === 200) b.uri = 'data:application/octet-stream;base64,' + br.body.toString('base64');
    }
  }
  return gltf;
}

// 下载 .anim 口型
async function fetchAnim(name) {
  const ts = Date.now().toString();
  const headers = {'Accept':'application/json, text/plain, */*','Origin':'https://cloud.gbqr.net','Referer':'https://cloud.gbqr.net/','Timestamp':ts,'Token':TOKEN,'UUID':UUID,'User-Agent':'Mozilla/5.0'};
  const r = await httpsReq(`${BASE}/api/v3/assets/sign/latest/glb/anim/${name}.anim`, {headers});
  if (r.status !== 200) throw new Error('anim ' + r.status);
  return r.body.toString('utf8');
}

const MIME = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.gltf':'application/json','.bin':'application/octet-stream','.anim':'text/plain','.png':'image/png'};
const STATIC_DIR = path.join(__dirname, 'player');

const server = http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://localhost');
  const p = u.pathname;
  try {
    // API: 翻译
    if (p === '/api/translate') {
      const text = u.searchParams.get('text') || '';
      if (!text) { res.writeHead(400); res.end('需要 text 参数'); return; }
      const data = await translate(text);
      res.writeHead(200, {'Content-Type':'application/json'});
      res.end(JSON.stringify(data));
      return;
    }
    // API: 动画 gltf（自包含）
    if (p.startsWith('/api/gltf/')) {
      const id = p.slice('/api/gltf/'.length);
      const gltf = await fetchSignGltf(id);
      res.writeHead(200, {'Content-Type':'application/json'});
      res.end(JSON.stringify(gltf));
      return;
    }
    // API: 口型 anim -> 解析为曲线 JSON
    if (p.startsWith('/api/anim/')) {
      const name = p.slice('/api/anim/'.length);
      const yaml = await fetchAnim(name);
      // 解析 curves
      const curves = {};
      const blocks = yaml.split(/\s+attribute:\s*/);
      for (let i = 1; i < blocks.length; i++) {
        const block = blocks[i];
        const m = block.match(/^blendShape\.(\w+)/);
        if (!m) continue;
        const times = [], values = [];
        let t;
        const tRe = /time:\s*([\d.]+)/g;
        const vRe = /value:\s*(-?[\d.]+)/g;
        while ((t = tRe.exec(block))) times.push(parseFloat(t[1]));
        while ((t = vRe.exec(block))) values.push(parseFloat(t[1]));
        if (times.length && times.length === values.length) curves[m[1]] = { times, values };
      }
      res.writeHead(200, {'Content-Type':'application/json'});
      res.end(JSON.stringify({name, curves}));
      return;
    }
    // 静态文件
    let fp = path.join(STATIC_DIR, p === '/' ? 'index.html' : p);
    if (!fs.existsSync(fp) || !fp.startsWith(STATIC_DIR)) { res.writeHead(404); res.end('404'); return; }
    res.writeHead(200, {'Content-Type': MIME[path.extname(fp)]||'application/octet-stream'});
    res.end(fs.readFileSync(fp));
  } catch(e) {
    res.writeHead(500, {'Content-Type':'application/json'});
    res.end(JSON.stringify({error: e.message}));
  }
});

server.listen(PORT, () => console.log('手语播放器服务: http://localhost:' + PORT));

