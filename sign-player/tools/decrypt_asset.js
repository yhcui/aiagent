const fs = require('fs');
const crypto = require('crypto');
const zlib = require('zlib');

const token = 'E9A146B8BA161E13D942B2CED15A2';
const timestamp = '1787629225375';
const uid = 'd5004249-c7de-40b6-a61a-54903dff9bf1';

const file = fs.readFileSync('sign_assets/09475.gltf');
console.log('原文件大小:', file.length, '头:', file.slice(0,9).toString('latin1'));

const data = file.subarray(7);  // 去掉 "GBAsset"
console.log('去头后大小:', data.length);

const salt = crypto.createHash('md5').update(token + timestamp, 'utf8').digest();
console.log('salt:', salt.toString('hex'));

const key = crypto.pbkdf2Sync(token, salt, 1000, 32, 'sha1');
console.log('key:', key.toString('hex'));

const iv = Buffer.from(uid.slice(0,16), 'utf8');
console.log('iv:', iv.toString('utf8'));

let pt;
try {
  const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
  pt = Buffer.concat([decipher.update(data), decipher.final()]);
  console.log('AES-CBC 解密成功, 明文大小:', pt.length, '头:', pt.slice(0,16).toString('hex'));
} catch(e) {
  console.log('AES-CBC 解密失败:', e.message);
  process.exit(1);
}

// 尝试解压
let out = null;
for (const [name, fn] of [['inflate', ()=>zlib.inflateSync(pt)], ['inflateRaw', ()=>zlib.inflateRawSync(pt)], ['ungzip', ()=>zlib.gunzipSync(pt)]]) {
  try { out = fn(); console.log(`解压方式 ${name} 成功, 大小:`, out.length, '头:', out.slice(0,16).toString('hex'), 'ASCII:', out.slice(0,16).toString('latin1')); break; }
  catch(e) { console.log(`  ${name} 失败:`, e.message.slice(0,40)); }
}
if (out) {
  fs.writeFileSync('sign_assets/09475_decoded.glb', out);
  console.log('已保存 sign_assets/09475_decoded.glb');
}
