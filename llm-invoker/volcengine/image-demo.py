import os
from dotenv import load_dotenv
# Install SDK:  pip install 'volcengine-python-sdk[ark]' .
from volcenginesdkarkruntime._client import Ark  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]

load_dotenv()

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # Get API Key：https://console.volcengine.com/ark/region:cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'),
)

imagesResponse = client.images.generate(
    # Replace with Model ID
    model="doubao-seedream-5-0-260128",
    prompt="充满活力的特写编辑肖像，模特眼神犀利，头戴雕塑感帽子，色彩拼接丰富，眼部焦点锐利，景深较浅，具有Vogue杂志封面的美学风格，采用中画幅拍摄，工作室灯光效果强烈。",
    size="2K",
    output_format="png",
    response_format="url",
    watermark=False
)

print(imagesResponse.data[0].url)