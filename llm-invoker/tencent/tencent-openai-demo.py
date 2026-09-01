import os
from  dotenv import  load_dotenv
from openai import OpenAI
load_dotenv()
client = OpenAI(
    api_key=os.environ.get("API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1",
)

response = client.chat.completions.create(
    model="hy4-preview",
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己"},
    ],
)
print(response.choices[0].message.content)
