const https = require('https');
const fs = require('fs');
const crypto = require('crypto');
const zlib = require('zlib');

const token = 'E9A146B8BA161E13D942B2CED15A2';
const uid = 'd5004249-c7de-40b6-a61a-54903dff9bf1';

function httpGet(url, headers) {
  return new Promise((resolve, reject) => {
    https.get(url, {headers}, res => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks)));
    }).on('error', reject);
  });
}

function decryptGB(data, timestamp) {
  const head = data.slice(0, 7).toString('latin1');
  if (head !== 'GBAsset') throw new Error('非 GBAsset: ' + head);
  const ct = data.subarray(7);
  const salt = crypto.createHash('md5').update(token + timestamp, 'utf8').digest();
  const key = crypto.pbkdf2Sync(token, salt, 1000, 32, 'sha1');
  const iv = Buffer.from(uid.slice(0,16), 'utf8');
  const d = crypto.createDecipheriv('aes-256-cbc', key, iv);
  const pt = Buffer.concat([d.update(ct), d.final()]);
  for (const [n, fn] of [['inflate', ()=>zlib.inflateSync(pt)], ['inflateRaw', ()=>zlib.inflateRawSync(pt)], ['ungzip', ()=>zlib.gunzipSync(pt)]]) {
    try { return {data: fn(), method: n}; } catch(e) {}
  }
  throw new Error('解压失败');
}

(async () => {
  const ts = Date.now().toString();
  const url = 'https://api.gbqr.net/api/v3/assets/sign/latest/glb/Idle_Closed.gltf';
  const headers = {
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://cloud.gbqr.net',
    'Referer': 'https://cloud.gbqr.net/',
    'Timestamp': ts,
    'Token': token,
    'UUID': uid,
    'User-Agent': 'Mozilla/5.0'
  };
  const raw = await httpGet(url, headers);
  console.log('下载大小:', raw.length);
  const {data, method} = decryptGB(raw, ts);
  console.log('解密方式:', method, ' 明文大小:', data.length, ' 头:', data.slice(0,30).toString('latin1'));
  const outPath = 'sign_assets/Idle_Closed_model.gltf';
  fs.writeFileSync(outPath, data);
  console.log('已保存:', outPath, ' 使用的 timestamp:', ts);
  // 解析 gltf 结构
  try {
    const gltf = JSON.parse(data.toString('utf8'));
    console.log('=== 模型结构 ===');
    console.log('asset:', JSON.stringify(gltf.asset));
    console.log('buffers:', JSON.stringify(gltf.buffers));
    console.log('bufferViews:', (gltf.bufferViews||[]).length, 'accessors:', (gltf.accessors||[]).length);
    console.log('meshes:', (gltf.meshes||[]).length, 'nodes:', (gltf.nodes||[]).length, 'skins:', (gltf.skins||[]).length);
    console.log('materials:', (gltf.materials||[]).length, 'animations:', (gltf.animations||[]).length);
    console.log('scenes:', JSON.stringify(gltf.scenes));
    if (gltf.extensionsUsed) console.log('extensionsUsed:', gltf.extensionsUsed);
    if (gltf.meshes && gltf.meshes[0]) {
      const m = gltf.meshes[0];
      console.log('mesh[0] primitives:', JSON.stringify(m.primitives).slice(0,300));
      console.log('mesh[0] weights:', m.weights);
    }
    fs.writeFileSync('sign_assets/Idle_Closed_ts.txt', ts);
  } catch(e) {
    console.log('gltf 解析失败:', e.message);
  }
})();
