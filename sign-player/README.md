# 手语数字人播放器（果不其然 gbqr 逆向版）

把文本翻译成手语并用 3D 数字人播放。基于对 `cloud.gbqr.net` 播放器前端的逆向实现。

## 快速开始

```bash
node server_full.js
```

然后浏览器打开 **http://localhost:8137**，输入文字（如"深度融合"）点"播放"。

## 目录结构

```
sign-player/
├── server_full.js        # 后端服务：翻译代理 + GBAsset 解密 + 口型解析（token/UUID 已内置）
├── player/               # 前端资源（three.js 渲染，纯前端）
│   ├── index.html        # 播放器页面
│   ├── 1014_01.gltf/.bin # 角色模型「小译」（网格+60关节+27口型blendshape）
│   ├── 09475.gltf/.bin   # 演示动作（"深度"第一段骨骼动画）
│   ├── Zhen.anim         # 演示口型（blendShape I/E/T）
│   └── *.png             # 角色 8 张纹理贴图（面/身体/头发/眼睛/睫毛+法线）
└── tools/                # 逆向工具脚本
    ├── decrypt_asset.js  # GBAsset 加密资源解密（AES-CBC + inflateRaw）
    ├── dl_model.js       # 下载+解密角色模型
    ├── dl_textures.js    # 下载角色纹理贴图
    └── test_api.js       # 后端逻辑一键自测
```

## 工作原理

```
文本 ──▶ /api/translate（调原站翻译接口拆词）
          每个词返回 motion 编号 + expression 拼音
             │
        /api/gltf/{id}    下载动作 .gltf → GBAsset 解密(AES-CBC+inflateRaw) → 骨骼动画
        /api/anim/{name}  下载口型 .anim → 解析 blendShape 曲线 → 驱动模型 morphTarget
             │
        three.js：小译模型(1014_01) + 动作 clip 按骨骼名 remap + 口型 morph 叠加
```

## 关键逆向结论

- **翻译接口**：`POST /api/sign/translate/meta/auto`，返回词的 `motion`（空格分隔多个子动作）和 `expression`（空格分隔拼音）
- **资源接口**：`/api/v3/assets/sign/latest/glb/{id}.gltf` + `glb/bin/{id}.bin`（动作）、`glb/anim/{拼音}.anim`（口型）
- **GBAsset 加密**：文件=7字节头 + AES-256-CBC；key=PBKDF2-SHA1(token, salt=md5(token+请求头Timestamp), 1000, 32)，iv=UUID 前16字节；解密后 inflateRaw 解压
- **角色模型**：`POST /api/Terminal/GetDigitPersonAuthByUserId`（body 需 `memberID=uid`）返回账号拥有的数字人列表，模型路径 `glb/{code}/{code}.gltf`（v2 接口，zlib 压缩），贴图在同目录 `glb/{code}/{name}.png`
- **口型映射**：morphDictionary A:7 B:14 E:8 F:13 I:9 L:12 O:10 T:15 U:11（对应模型 27 个 morphTarget）
- **动画匹配**：动作 gltf 与模型共享 Bip001 骨骼命名，前端按骨骼名 remap 后播放

## 自定义

- 换角色：调 `GetDigitPersonAuthByUserId` 拿 dpList，改 `dl_model.js` 里的 code 重新下载模型+贴图，替换 `player/1014_01.*`
- token/uuid 失效：更新 `server_full.js` 顶部的 `TOKEN` / `UUID`
