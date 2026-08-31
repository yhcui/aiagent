import os
from dotenv import load_dotenv
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime._client import Ark

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
    prompt="保持模特姿势和液态服装的流动形状不变。将服装材质从银色金属改为完全透明的清水（或玻璃）。透过液态水流，可以看到模特的皮肤细节。光影从反射变为折射。",
    image="",
    size="2K",
    output_format="png",
    response_format="url",
    watermark=False
)

print(imagesResponse.data[0].url)