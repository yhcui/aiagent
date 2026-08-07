# -*- coding: utf-8 -*-
import os
import asyncio
from typing import Optional
import dashscope
from dotenv import load_dotenv
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
import pandas as pd
from sqlalchemy import create_engine, text
from qwen_agent.tools.base import BaseTool, register_tool
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import time
import numpy as np

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 定义资源文件根目录
ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), 'resource')

# 配置 DashScope
load_dotenv()
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')
dashscope.timeout = 30

# ====== 股票查询助手 system prompt 和函数描述 ======
system_prompt = """我是股票查询助手，以下是股票行情数据表相关的字段，我可能会编写对应的SQL，对数据进行查询

-- 股票日线行情表
CREATE TABLE daily_kline (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20),           -- 股票代码（如 600519.SH）
    trade_date VARCHAR(12),        -- 交易日期（格式 YYYYMMDD）
    open DECIMAL(12,4),            -- 开盘价
    high DECIMAL(12,4),            -- 最高价
    low DECIMAL(12,4),             -- 最低价
    close DECIMAL(12,4),           -- 收盘价
    pre_close DECIMAL(12,4),       -- 前收盘价
    change DECIMAL(12,4),          -- 涨跌额
    pct_chg DECIMAL(10,4),         -- 涨跌幅（%）
    vol DECIMAL(18,4),             -- 成交量（手）
    amount DECIMAL(18,4),          -- 成交额（千元）
    stock_name VARCHAR(50)         -- 股票名称
);

数据范围：20200102 至 20251220，共 5635 条记录，包含以下股票：
- 600519.SH (贵州茅台)
- 601211.SH (京沪高铁)
- 000858.SZ (五粮液)
- 688981.SH (中芯国际)

注意事项：
1. trade_date 是字符串格式 YYYYMMDD，比较时直接用字符串或 CAST(trade_date AS UNSIGNED)
2. 查询涨跌幅排序用 pct_chg 字段
3. 查询成交量用 vol，成交额用 amount
4. 股票代码包含交易所后缀（.SH / .SZ）
5. 多股对比时，可用 ts_code 或 stock_name 筛选

我将回答用户关于股票行情相关的问题

每当 exc_sql 工具返回 markdown 表格和图片时，你必须原样输出工具返回的全部内容（包括图片 markdown），不要只总结表格，也不要省略图片。这样用户才能直接看到表格和图片。
"""

functions_desc = [
    {
        "name": "exc_sql",
        "description": "对生成的SQL，进行MySQL数据库查询",
        "parameters": {
            "type": "object",
            "properties": {
                "sql_input": {
                    "type": "string",
                    "description": "生成的SQL语句",
                }
            },
            "required": ["sql_input"],
        },
    },
]

# ====== 会话隔离 DataFrame 存储 ======
_last_df_dict = {}

def get_session_id(kwargs):
    messages = kwargs.get('messages')
    if messages is not None:
        return id(messages)
    return None

# ====== exc_sql 工具类实现 ======
@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
    """
    SQL查询工具，执行传入的SQL语句并返回结果，并自动进行可视化。
    """
    description = '对生成的SQL，进行MySQL数据库查询，并自动可视化'
    parameters = [{
        'name': 'sql_input',
        'type': 'string',
        'description': '生成的SQL语句',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
        import json
        from sqlalchemy import text

        session_id = get_session_id(kwargs)

        args = json.loads(params)
        sql_input = args['sql_input']
        print('sql_input=', sql_input)

        engine = create_engine(
            'mysql+pymysql://root:root@127.0.0.1:3306/stock_data?charset=utf8mb4',
            connect_args={'connect_timeout': 10}, pool_size=10, max_overflow=20
        )
        df = pd.read_sql(text(sql_input), engine)
        print('df=', df)

        if session_id:
            _last_df_dict[session_id] = df

        md = df.head(20).to_markdown(index=False)

        # 自动创建目录
        save_dir = os.path.join(os.path.dirname(__file__), 'image_show')
        os.makedirs(save_dir, exist_ok=True)
        filename = f'stock_{int(time.time() * 1000)}.png'
        save_path = os.path.join(save_dir, filename)

        generate_chart_png(df, save_path)
        img_path = os.path.join('image_show', filename)
        img_md = f'![图表]({img_path})'
        return f"{md}\n\n{img_md}"

# ========== 股票数据可视化函数 ==========
def generate_chart_png(df_sql, save_path):
    columns = df_sql.columns
    n = len(df_sql)

    if n == 0:
        return

    # 检测是否有 trade_date 列（时间序列）
    has_date = 'trade_date' in columns
    # 检测是否有 ts_code 列（多股对比）
    has_code = 'ts_code' in columns
    # 获取数值列
    num_cols = df_sql.select_dtypes(include='number').columns.tolist()
    # 获取对象列
    obj_cols = df_sql.select_dtypes(include='O').columns.tolist()

    # 去掉 id 列
    if 'id' in num_cols:
        num_cols.remove('id')

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.tab10.colors

    if has_date and n > 0:
        # ===== 有时间序列数据，绘制折线图或柱状图 =====
        # 对 trade_date 排序
        df_sql = df_sql.sort_values('trade_date')

        if has_code and len(df_sql['ts_code'].unique()) > 1:
            # 多股对比折线图
            for i, code in enumerate(df_sql['ts_code'].unique()):
                subset = df_sql[df_sql['ts_code'] == code].sort_values('trade_date')
                label = code
                if 'stock_name' in subset.columns:
                    name = subset['stock_name'].iloc[0]
                    label = f"{code} ({name})"
                # 默认画 close 收盘价
                if 'close' in num_cols:
                    y_col = 'close'
                elif num_cols:
                    y_col = num_cols[0]
                else:
                    y_col = None
                if y_col:
                    ax.plot(subset['trade_date'], subset[y_col],
                            label=label, color=colors[i], marker='o', markersize=3)
        else:
            # 单股时间序列
            for i, col in enumerate(num_cols):
                label_str = str(col)
                safe_label = label_str.replace('%', '%%').replace('{', '{{').replace('}', '}}')
                ax.plot(df_sql['trade_date'], df_sql[col],
                        label=safe_label, color=colors[i], marker='o', markersize=3)

        plt.xticks(rotation=45)
        plt.xlabel('trade_date')
        plt.title('股票行情趋势')
        plt.ylabel('数值')
        plt.legend()
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

    else:
        # ===== 没有时间列，绘制柱状图 =====
        x = np.arange(n)
        bottom = np.zeros(n)

        # 如果有 ts_code 作为横轴
        if has_code:
            tick_labels = df_sql['ts_code'].astype(str).tolist()
        elif obj_cols and len(obj_cols) > 0:
            tick_labels = df_sql[obj_cols[0]].astype(str).tolist()
        else:
            tick_labels = [str(i) for i in range(n)]

        for col in num_cols:
            label_str = str(col)
            safe_label = label_str.replace('%', '%%').replace('{', '{{').replace('}', '}}')
            ax.bar(x, df_sql[col], bottom=bottom, label=safe_label)
            bottom += df_sql[col]

        safe_xtick = [str(v).replace('%', '%%') for v in tick_labels]
        ax.set_xticks(x)
        ax.set_xticklabels(safe_xtick, rotation=45)
        plt.xlabel('股票代码')
        plt.title('股票统计对比')
        plt.ylabel('数值')
        plt.legend()
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

# ====== 初始化股票查询助手服务 ======
def init_agent_service():
    """初始化股票查询助手服务"""
    llm_cfg = {
        'model': 'qwen-turbo',
        'timeout': 30,
        'retry_count': 3,
    }
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    functions = ['exc_sql',
                 {
                     "mcpServers": {
                         "tavily-mcp": {
                             "args": [
                                 "-y",
                                 "tavily-mcp@0.1.4"
                             ],
                             "autoApprove": [],
                             "command": "npx",
                             "env": {
                                 "TAVILY_API_KEY": tavily_api_key
                             }
                         }
                     }
                 }
             ]
    try:
        bot = Assistant(
            llm=llm_cfg,
            name='股票查询助手',
            description='股票行情查询与数据分析',
            system_message=system_prompt,
            function_list=functions,
            files=['faq.txt'],
        )
        print("股票查询助手初始化成功！")
        return bot
    except Exception as e:
        print(f"助手初始化失败: {str(e)}")
        raise

def app_tui():
    """终端交互模式"""
    try:
        bot = init_agent_service()
        messages = []
        while True:
            try:
                query = input('user question: ')
                file = input('file url (press enter if no file): ').strip()
                if not query:
                    print('user question cannot be empty！')
                    continue
                if not file:
                    messages.append({'role': 'user', 'content': query})
                else:
                    messages.append({'role': 'user', 'content': [{'text': query}, {'file': file}]})
                print("正在处理您的请求...")
                response = []
                for response in bot.run(messages):
                    print('bot response:', response)
                messages.extend(response)
            except Exception as e:
                print(f"处理请求时出错: {str(e)}")
    except Exception as e:
        print(f"启动终端模式失败: {str(e)}")


def app_gui():
    """图形界面模式，提供 Web 图形界面"""
    try:
        print("正在启动 Web 界面...")
        bot = init_agent_service()
        chatbot_config = {
            'prompt.suggestions': [
                '查询贵州茅台最近一个月的股价走势',
                '查询2024年全年贵州茅台的收盘价走势',
                '对比2024年中芯国际和贵州茅台的涨跌幅',
                '获取贵州茅台最近新闻',
                '使用ARIMA模型预测贵州茅台未来7天的价格',
                '预测600519.SH股票未来5天的收盘价',
            ]
        }
        print("Web 界面准备就绪，正在启动服务...")
        WebUI(
            bot,
            chatbot_config=chatbot_config
        ).run()
    except Exception as e:
        print(f"启动 Web 界面失败: {str(e)}")
        print("请检查网络连接和 API Key 配置")


if __name__ == '__main__':
    app_gui()
