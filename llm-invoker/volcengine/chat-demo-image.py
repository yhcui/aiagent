import os
from dotenv import load_dotenv
from typing import cast
from collections.abc import Iterator 
from volcenginesdkarkruntime._client import Ark
from volcenginesdkarkruntime.resources.responses.responses import ArkAPIError
from volcenginesdkarkruntime.types.chat import ChatCompletion, ChatCompletionChunk

load_dotenv()

client = Ark(
    base_url=os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    api_key=os.environ.get("ARK_API_KEY")
)

try:

    resp = cast(ChatCompletion,
    client.chat.completions.create(
        model="doubao-seed-2-1-turbo-260628",
        messages=[{"content":[{"image_url":{"url":"https://ark-project.tos-cn-beijing.volces.com/images/view.jpeg"},"type":"image_url"},{"text":"图片主要讲了什么?","type":"text"}],"role":"user"}],
    ))
    print(resp.choices[0].message.content)
   
except ArkAPIError as e :
    print(f"错误码: {e.code}")
    print(f"错误信息: {e.message}")
