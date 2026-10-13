# 角色测算小程序（宫闱命格）

## 启动后端
```bash
cd d:/OpenCode-Project/aiagent/ai-product/role-destiny/backend
pip install -r requirements.txt
python init_data.py --reset        # 首次初始化/重置数据
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 小程序
- 微信开发者工具导入 `miniprogram/`（AppID 已配置）
- 开发环境默认后端地址：`http://127.0.0.1:8000`（见 `miniprogram/app.js` 的 `apiBaseUrl`，真机调试改为局域网 IP）

## 说明
- 支付为 DEBUG Mock 模式（商户号申请前）
- 进度与设计系统详见 `DEV-PROGRESS.md`