const https = require('https');
const fs = require('fs');
const zlib = require('zlib');
const TOKEN = 'E9A146B8BA161E13D942B2CED15A2';
const UUID = 'd5004249-c7de-40b6-a61a-54903dff9bf1';
function httpGet(url, headers) {
  return new Promise((resolve, reject) => {
    https.get(url, {headers}, res => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve({status: res.statusCode, buf: Buffer.concat(chunks)}));
    }).on('error', reject);
  });
}
(async () => {
  const hdrs = {'Accept':'*/*','Origin':'https://cloud.gbqr.net','Referer':'https://cloud.gbqr.net/','Timestamp':Date.now().toString(),'Token':TOKEN,'UUID':UUID,'User-Agent':'Mozilla/5.0'};
  const images = ['hair_n.png','hair_01.png','face.png','eye.png','eyelash.png','body.png','upper_n.png','shirt_n.png'];
  for (const img of images) {
    // 尝试 v2 模型目录下的贴图
    const url = `https://api.gbqr.net/api/v2/assets/sign/latest/glb/1014_01/${img}`;
    const r = await httpGet(url, hdrs);
    console.log(`${img}: status=${r.status} size=${r.buf.length} head=${r.buf.slice(0,8).toString('latin1').replace(/[^\x20-\x7e]/g,'.')}`);
    if (r.status === 200 && r.buf.length > 100) {
      // 尝试解压（贴图可能 zlib 压缩）
      let out = r.buf;
      for (const [n, fn] of [['inflate',()=>zlib.inflateSync(r.buf)],['inflateRaw',()=>zlib.inflateRawSync(r.buf)],['gunzip',()=>zlib.gunzipSync(r.buf)]]) {
        try { out = fn(); console.log(`  -> ${n} 解压 ${out.length}`); break; } catch(e) {}
      }
      fs.writeFileSync(`sign_assets/1014_01_${img}`, out);
    }
  }
})();
