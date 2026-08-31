import os
from dotenv import load_dotenv
from typing import cast
from volcenginesdkarkruntime._client import Ark
from volcenginesdkarkruntime.resources.responses.responses import ArkAPIError
from volcenginesdkarkruntime.types.chat import ChatCompletion

load_dotenv()

client = Ark(
    base_url=os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    api_key=os.environ.get("ARK_API_KEY")
)

try:

    completion = cast(
        ChatCompletion,
        client.chat.completions.create(
            model="doubao-seed-2-1-turbo-260628",
            messages=[
                {"role": "system", "content": "你是一个英语翻译的专家"},
                {"role": "user", "content": "你好，请帮我翻译你好"}
            ]
        )
    )
    print(completion)
    print("*"*80)
    print(completion.choices[0].message)
    print("*"*80)
    print(completion.choices[0].message.content)
except ArkAPIError as e :
    print(f"错误码: {e.code}")
    print(f"错误信息: {e.message}")

