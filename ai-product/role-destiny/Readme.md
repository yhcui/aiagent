# 启动后端服务
cd d:/OpenCode-Project/aiagent/ai-product/role-destiny/backend
pip install -r requirements.txt
python init_data.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 配置后端访问地址
修改 miniprogram/app.js 中的 apiBaseUrl：
// 如果在同一台电脑上测试，使用本机IP而非 localhost
const apiBaseUrl = 'http://127.0.0.1:8000/api/v1';