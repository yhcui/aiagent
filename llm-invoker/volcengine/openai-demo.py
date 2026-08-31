"""
OpenAI 兼容方式接入火山引擎 Ark 示例
======================================
通过设置 base_url，让标准 OpenAI 客户端可以调用火山引擎大模型
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from openai import OpenAI
from openai import APIError

_ = load_dotenv()

# 使用 OpenAI 兼容方式初始化客户端
# 关键：base_url 指向火山引擎 API 地址（注意路径是 /api/v3）
client = OpenAI(
    base_url=os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    api_key=os.environ.get("ARK_API_KEY")
)

# ==================== 非流式调用 ====================
print("=" * 60)
print("【非流式调用示例】")
print("=" * 60)

try:
    completion = client.chat.completions.create(
        model="doubao-seed-2-1-turbo-260628",  
        messages=[
            {"role": "system", "content": "你是一个英语翻译专家"},
            {"role": "user", "content": "请把'你好，世界！'翻译成英文"}
        ]
    )
    print(f"回复: {completion.choices[0].message.content}")
    print(f"模型: {completion.model}")
    if completion.usage:
        print(f"耗时: {completion.usage.completion_tokens} tokens")

except APIError as e:
    print(f"API 错误: {e.code} - {e.message}")


# ==================== 流式调用 ====================
print("\n" + "=" * 60)
print("【流式调用示例】")
print("=" * 60)

try:
    stream = client.chat.completions.create(
        model="doubao-seed-2-1-turbo-260628",  # 替换为你的模型 ID
        messages=[
            {"role": "system", "content": "你是一个幽默的助手"},
            {"role": "user", "content": "给我讲一个笑话"}
        ],
        stream=True
    )
    
    print("回复: ", end="")
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()

except APIError as e:
    print(f"API 错误: {e.code} - {e.message}")


# ==================== Function Calling 示例 ====================
print("\n" + "=" * 60)
print("【Function Calling 示例】")
print("=" * 60)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

try:
    completion = client.chat.completions.create(
        model="doubao-seed-2-1-turbo-260628",
        messages=[
            {"role": "user", "content": "北京今天天气怎么样？"}
        ],
        tools=tools  # pyright: ignore[reportArgumentType]
    )
    
    response_message = completion.choices[0].message
    print(f"回复: {response_message.content}")
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            func = tool_call.function  # pyright: ignore[reportAttributeAccessIssue]
            print(f"调用函数: {func.name}")  # pyright: ignore[reportUnknownMemberType]
            print(f"参数: {func.arguments}")  # pyright: ignore[reportUnknownMemberType]

except APIError as e:
    print(f"API 错误: {e.code} - {e.message}")
