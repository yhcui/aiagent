# -*- coding: utf-8 -*-
import os
import json
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
from statsmodels.tsa.arima.model import ARIMA

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), 'resource')

load_dotenv()
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')
dashscope.timeout = 30

# ====== 股票查询助手 system prompt ======
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
6. 使用 arima_stock 工具可以对股票收盘价进行 ARIMA(5,1,5) 时间序列预测
7. 使用 boll_detection 工具可以使用布林带(Bollinger Bands)检测股票的超买和超卖点

工具 arima_stock 说明：
- ts_code（必填）：股票代码，如 600519.SH
- n（可选）：预测未来天数，默认5天
- 数据来源：本地 MySQL 数据库 stock_data
- 数据范围：截止到今天的前一年历史收盘价
- 模型：ARIMA(5,1,5)
- 输出：预测结果表格 + 历史/预测价格对比图

工具 boll_detection 说明：
- ts_code（必填）：股票代码，如 600519.SH
- start_date（可选）：起始日期，格式 YYYYMMDD，默认前1年
- end_date（可选）：结束日期，格式 YYYYMMDD，默认最新交易日
- 算法：布林带 Bollinger Bands，20日移动平均线 + 2倍标准差
- 超买（overbought）：收盘价突破上轨（> MA20 + 2*std）
- 超卖（oversold）：收盘价跌破下轨（< MA20 - 2*std）
- 数据来源：本地 MySQL 数据库 stock_data
- 输出：超买/超卖日期表格 + 布林带图表

我将回答用户关于股票行情相关的问题

每当工具返回 markdown 表格和图片时，你必须原样输出工具返回的全部内容（包括图片 markdown），不要只总结表格，也不要省略图片。
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
    {
        "name": "arima_stock",
        "description": "使用ARIMA(5,1,5)模型预测股票未来N天的收盘价",
        "parameters": {
            "type": "object",
            "properties": {
                "ts_code": {"type": "string", "description": "股票代码，如 600519.SH"},
                "n": {"type": "integer", "description": "预测未来天数，默认5天"},
            },
            "required": ["ts_code"],
        },
    },
    {
        "name": "boll_detection",
        "description": "使用布林带(Bollinger Bands)检测股票的超买和超卖点，20日周期+2倍标准差",
        "parameters": {
            "type": "object",
            "properties": {
                "ts_code": {"type": "string", "description": "股票代码，如 600519.SH，必填"},
                "start_date": {"type": "string", "description": "起始日期，格式 YYYYMMDD，可选"},
                "end_date": {"type": "string", "description": "结束日期，格式 YYYYMMDD，可选"},
            },
            "required": ["ts_code"],
        },
    },
]

_last_df_dict = {}

def get_session_id(kwargs):
    messages = kwargs.get('messages')
    if messages is not None:
        return id(messages)
    return None

# ====== exc_sql 工具 ======
@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
    description = '对生成的SQL，进行MySQL数据库查询，并自动可视化'
    parameters = [{
        'name': 'sql_input',
        'type': 'string',
        'description': '生成的SQL语句',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
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

        save_dir = os.path.join(os.path.dirname(__file__), 'image_show')
        os.makedirs(save_dir, exist_ok=True)
        filename = f'stock_{int(time.time() * 1000)}.png'
        save_path = os.path.join(save_dir, filename)

        generate_chart_png(df, save_path)
        img_path = os.path.join('image_show', filename)
        img_md = f'![图表]({img_path})'
        return f"{md}\n\n{img_md}"

# ====== arima_stock 工具 ======
@register_tool('arima_stock')
class ArimaStockTool(BaseTool):
    """
    使用 ARIMA(5,1,5) 模型对股票收盘价进行时间序列预测。
    """
    description = '使用ARIMA(5,1,5)模型预测股票未来N天的收盘价'
    parameters = [
        {'name': 'ts_code', 'type': 'string', 'description': '股票代码，如 600519.SH，必填', 'required': True},
        {'name': 'n', 'type': 'integer', 'description': '预测未来天数，默认5天', 'required': False},
    ]

    def call(self, params: str, **kwargs) -> str:
        import datetime
        from sqlalchemy import text
        session_id = get_session_id(kwargs)
        args = json.loads(params)
        ts_code = args.get('ts_code')
        n = args.get('n', 5)

        if not ts_code:
            return '错误：ts_code 为必填参数，请提供股票代码（如 600519.SH）'

        print(f'arima_stock: ts_code={ts_code}, n={n}')

        engine = create_engine(
            'mysql+pymysql://root:root@127.0.0.1:3306/stock_data?charset=utf8mb4',
            connect_args={'connect_timeout': 10}
        )
        sql = text(
            "SELECT trade_date, close, stock_name "
            "FROM daily_kline "
            "WHERE ts_code = :ts_code "
            "ORDER BY trade_date DESC LIMIT 260"
        )
        df = pd.read_sql(sql, engine, params={'ts_code': ts_code})

        if df.empty:
            return f'错误：未找到股票 {ts_code} 的历史数据'

        stock_name = df.iloc[0]['stock_name']
        df = df.sort_values('trade_date').reset_index(drop=True)
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df = df.dropna(subset=['close'])

        if len(df) < 30:
            return f'错误：股票 {ts_code} 历史数据不足（仅 {len(df)} 条），无法进行ARIMA建模'

        print(f'arima_stock: {ts_code} ({stock_name}), using {len(df)} historical records')

        try:
            close_values = df['close'].astype(float).values
            model = ARIMA(close_values, order=(5, 1, 5))
            model_fit = model.fit()

            forecast = model_fit.forecast(steps=n)
            forecast_ci = model_fit.get_forecast(steps=n).conf_int()

            last_date = df['trade_date'].iloc[-1]
            last_dt = datetime.datetime.strptime(last_date, '%Y%m%d')

            pred_dates = []
            current_dt = last_dt
            while len(pred_dates) < n:
                current_dt = current_dt + datetime.timedelta(days=1)
                if current_dt.weekday() < 5:
                    pred_dates.append(current_dt.strftime('%Y%m%d'))

            pred_df = pd.DataFrame({
                'pred_date': pred_dates,
                'predicted_close': [round(float(v), 2) for v in forecast],
                'lower_bound': [round(float(forecast_ci[i, 0]), 2) for i in range(n)],
                'upper_bound': [round(float(forecast_ci[i, 1]), 2) for i in range(n)],
            })

            if session_id:
                _last_df_dict[session_id] = pred_df

            md_table = pred_df.to_markdown(index=False)
            model_summary = f'\n模型: ARIMA({model_fit.model.order})\n'
            model_summary += f'AIC: {model_fit.aic:.2f}\n'
            model_summary += f'BIC: {model_fit.bic:.2f}\n'
            model_summary += f'拟合日期范围: {df["trade_date"].iloc[0]} ~ {df["trade_date"].iloc[-1]}'
            model_summary += f'\n预测股票: {ts_code} ({stock_name})'
            model_summary += f'\n预测天数: {n} 天'

            save_dir = os.path.join(os.path.dirname(__file__), 'image_show')
            os.makedirs(save_dir, exist_ok=True)
            filename = f'arima_{ts_code}_{int(time.time() * 1000)}.png'
            save_path = os.path.join(save_dir, filename)

            fig, ax = plt.subplots(figsize=(14, 6))
            hist = df.tail(90)
            ax.plot(hist['trade_date'], hist['close'], color='#1f77b4', label=f'历史收盘价 (最近{len(hist)}天)', linewidth=1.5)
            ax.plot(pred_dates, pred_df['predicted_close'], color='#d62728', label='ARIMA预测', linewidth=2, marker='o', markersize=5)
            ax.fill_between(pred_dates, pred_df['lower_bound'], pred_df['upper_bound'],
                            alpha=0.2, color='#d62728', label='95%置信区间')

            plt.title(f'{stock_name} ({ts_code}) 股价预测 - ARIMA(5,1,5)', fontsize=14)
            plt.xlabel('交易日期', fontsize=12)
            plt.ylabel('收盘价 (元)', fontsize=12)
            plt.xticks(rotation=45)
            plt.legend(fontsize=10)
            plt.tight_layout()
            plt.savefig(save_path)
            plt.close()

            img_path = os.path.join('image_show', filename)
            img_md = f'![ARIMA预测图]({img_path})'

            return f"{md_table}\n\n{model_summary}\n\n{img_md}"

        except Exception as e:
            return f'ARIMA预测失败: {str(e)}'

# ====== boll_detection 工具 ======
@register_tool('boll_detection')
class BollDetectionTool(BaseTool):
    """
    使用布林带(Bollinger Bands)检测股票超买和超卖点。
    算法：20日移动平均线(MA) + 2倍标准差(2σ)
    - 上轨 = MA20 + 2*std20
    - 下轨 = MA20 - 2*std20
    - 超买(overbought): 收盘价 > 上轨
    - 超卖(oversold): 收盘价 < 下轨
    """
    description = '使用布林带(Bollinger Bands)检测股票的超买和超卖点，20日周期+2倍标准差'
    parameters = [
        {'name': 'ts_code', 'type': 'string', 'description': '股票代码，如 600519.SH，必填', 'required': True},
        {'name': 'start_date', 'type': 'string', 'description': '起始日期，格式 YYYYMMDD，可选，默认前1年', 'required': False},
        {'name': 'end_date', 'type': 'string', 'description': '结束日期，格式 YYYYMMDD，可选，默认最新交易日', 'required': False},
    ]

    def call(self, params: str, **kwargs) -> str:
        from sqlalchemy import text
        import warnings
        warnings.filterwarnings('ignore')

        session_id = get_session_id(kwargs)
        args = json.loads(params)
        ts_code = args.get('ts_code')
        start_date = args.get('start_date')
        end_date = args.get('end_date')

        if not ts_code:
            return '错误：ts_code 为必填参数，请提供股票代码（如 600519.SH）'

        print(f'boll_detection: ts_code={ts_code}, start={start_date}, end={end_date}')

        engine = create_engine(
            'mysql+pymysql://root:root@127.0.0.1:3306/stock_data?charset=utf8mb4',
            connect_args={'connect_timeout': 10}
        )

        # 构建查询SQL
        query_parts = ["SELECT trade_date, close, stock_name FROM daily_kline WHERE ts_code = :ts_code"]
        query_params = {'ts_code': ts_code}

        # 如果没有指定范围，取前1年(约260条)的数据
        if not start_date and not end_date:
            query_parts.append("ORDER BY trade_date DESC LIMIT 260")
        else:
            if start_date:
                query_parts.append("AND trade_date >= :start_date")
                query_params['start_date'] = start_date
            if end_date:
                query_parts.append("AND trade_date <= :end_date")
                query_params['end_date'] = end_date
            query_parts.append("ORDER BY trade_date ASC")

        sql = text(' '.join(query_parts))
        df = pd.read_sql(sql, engine, params=query_params)

        if df.empty:
            return f'错误：未找到股票 {ts_code} 的历史数据'

        stock_name = df.iloc[0]['stock_name']
        df = df.sort_values('trade_date').reset_index(drop=True)

        # 转为数值类型
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df = df.dropna(subset=['close'])

        # 计算布林带：20日MA + 2σ
        window = 20
        if len(df) < window:
            return f'错误：股票 {ts_code} 数据不足{window}条，无法计算布林带'

        df['ma'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        df['upper'] = df['ma'] + 2 * df['std']
        df['lower'] = df['ma'] - 2 * df['std']

        # 标记超买和超卖
        df['signal'] = ''
        df.loc[df['close'] > df['upper'], 'signal'] = '超买'
        df.loc[df['close'] < df['lower'], 'signal'] = '超卖'

        # 取有效数据（布林带计算从第20条开始）
        df_valid = df.dropna(subset=['ma', 'std', 'upper', 'lower']).copy()

        if df_valid.empty:
            return f'错误：布林带计算结果为空，请检查数据'

        # 提取异常点
        anomalies = df_valid[df_valid['signal'] != ''].copy()
        anomalies = anomalies[['trade_date', 'close', 'ma', 'upper', 'lower', 'signal']].copy()
        anomalies.columns = ['日期', '收盘价', '中轨(MA20)', '上轨', '下轨', '信号']
        for col in ['收盘价', '中轨(MA20)', '上轨', '下轨']:
            anomalies[col] = anomalies[col].apply(lambda x: round(float(x), 2))

        if session_id:
            _last_df_dict[session_id] = anomalies

        # 统计信息
        n_overbought = len(anomalies[anomalies['信号'] == '超买'])
        n_oversold = len(anomalies[anomalies['信号'] == '超卖'])
        range_start = df_valid['trade_date'].iloc[0]
        range_end = df_valid['trade_date'].iloc[-1]

        # 生成布林带图表
        save_dir = os.path.join(os.path.dirname(__file__), 'image_show')
        os.makedirs(save_dir, exist_ok=True)
        filename = f'boll_{ts_code}_{int(time.time() * 1000)}.png'
        save_path = os.path.join(save_dir, filename)

        fig, ax = plt.subplots(figsize=(14, 7))

        # 收盘价
        ax.plot(df_valid['trade_date'], df_valid['close'], color='#333333', linewidth=1.2, label='收盘价')

        # 布林带
        ax.plot(df_valid['trade_date'], df_valid['upper'], color='#e74c3c', linewidth=1, linestyle='--', label='上轨 (MA+2σ)')
        ax.plot(df_valid['trade_date'], df_valid['lower'], color='#2ecc71', linewidth=1, linestyle='--', label='下轨 (MA-2σ)')
        ax.plot(df_valid['trade_date'], df_valid['ma'], color='#3498db', linewidth=1.5, label='中轨 (MA20)')

        # 填充布林带区域
        ax.fill_between(df_valid['trade_date'], df_valid['lower'], df_valid['upper'],
                        alpha=0.08, color='#3498db')

        # 标记超买点（红色圆圈）
        if n_overbought > 0:
            ob = df_valid[df_valid['signal'] == '超买']
            ax.scatter(ob['trade_date'], ob['close'], color='#e74c3c', s=60, zorder=5,
                       label=f'超买点 ({n_overbought}个)', edgecolors='white', linewidth=0.5)

        # 标记超卖点（绿色圆圈）
        if n_oversold > 0:
            os_pts = df_valid[df_valid['signal'] == '超卖']
            ax.scatter(os_pts['trade_date'], os_pts['close'], color='#2ecc71', s=60, zorder=5,
                       label=f'超卖点 ({n_oversold}个)', edgecolors='white', linewidth=0.5)

        plt.title(f'{stock_name} ({ts_code}) 布林带分析 - 超买/超卖检测', fontsize=14)
        plt.xlabel('交易日期', fontsize=12)
        plt.ylabel('收盘价 (元)', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(fontsize=9, loc='upper left')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

        # 组装返回结果
        result_parts = []

        result_parts.append(f'**布林带分析结果 - {stock_name} ({ts_code})**')
        result_parts.append(f'')
        result_parts.append(f'- 分析周期: {window}日移动平均线 + 2倍标准差')
        result_parts.append(f'- 分析日期范围: {range_start} ~ {range_end}')
        result_parts.append(f'- 总检测天数: {len(df_valid)} 天')
        result_parts.append(f'- 超买点: {n_overbought} 个')
        result_parts.append(f'- 超卖点: {n_oversold} 个')

        if len(anomalies) > 0:
            md_table = anomalies.to_markdown(index=False)
            result_parts.append('')
            result_parts.append(md_table)
        else:
            result_parts.append('')
            result_parts.append('未检测到超买或超卖点。')

        img_path = os.path.join('image_show', filename)
        img_md = f'![布林带分析图]({img_path})'
        result_parts.append('')
        result_parts.append(img_md)

        return '\n'.join(result_parts)

# ========== 股票数据可视化函数 ==========
def generate_chart_png(df_sql, save_path):
    columns = df_sql.columns
    n = len(df_sql)

    if n == 0:
        return

    has_date = 'trade_date' in columns
    has_code = 'ts_code' in columns
    num_cols = df_sql.select_dtypes(include='number').columns.tolist()
    obj_cols = df_sql.select_dtypes(include='O').columns.tolist()

    if 'id' in num_cols:
        num_cols.remove('id')

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.tab10.colors

    if has_date and n > 0:
        df_sql = df_sql.sort_values('trade_date')

        if has_code and len(df_sql['ts_code'].unique()) > 1:
            for i, code in enumerate(df_sql['ts_code'].unique()):
                subset = df_sql[df_sql['ts_code'] == code].sort_values('trade_date')
                label = code
                if 'stock_name' in subset.columns:
                    name = subset['stock_name'].iloc[0]
                    label = f"{code} ({name})"
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
        x = np.arange(n)
        bottom = np.zeros(n)

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
    functions = ['exc_sql', 'arima_stock', 'boll_detection',
                 {
                     "mcpServers": {
                         "tavily-mcp": {
                             "args": ["-y", "tavily-mcp@0.1.4"],
                             "autoApprove": [],
                             "command": "npx",
                             "env": {"TAVILY_API_KEY": tavily_api_key}
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
    try:
        print("正在启动 Web 界面...")
        bot = init_agent_service()
        chatbot_config = {
            'prompt.suggestions': [
                '查询贵州茅台最近一个月的股价走势',
                '对比2024年中芯国际和贵州茅台的涨跌幅',
                '获取贵州茅台最近新闻',
                '使用ARIMA模型预测贵州茅台未来7天的价格',
                '使用布林带检测贵州茅台近1年的超买超卖点',
                '检测000858.SZ在2024年的超买和超卖信号',
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
