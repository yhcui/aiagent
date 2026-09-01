import os
from  dotenv import  load_dotenv
from openai import OpenAI
load_dotenv()
client = OpenAI(
    api_key=os.environ.get("API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1",
)

response = client.responses.create(
    model="hy4-preview",
    instructions="You are a helpful assistant.",
    input="你好",
    stream=False,
)

print(response.output_text)