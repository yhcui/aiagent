# -*- coding: utf-8 -*-
from http import HTTPStatus
from dashscope import VideoSynthesis
from dotenv import load_dotenv
import dashscope
import os
import time
import base64

load_dotenv()
# 正确：使用 /api/v1 路径
dashscope.base_http_api_url = 'https://llm-tgs20vajm1ikqveg.cn-beijing.maas.aliyuncs.com/api/v1'

api_key = os.getenv("DASHSCOPE_API_KEY")

# 参考图片列表（最多9张）
# ref_images = [
#     {
#         "type": "reference_image",
#         "url": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250925/wpimhv/rap.png"
#     }
# ]
def load_image_base64(image_path):
    """将本地图片转为 Base64 格式"""
    with open(image_path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    ext = os.path.splitext(image_path)[1][1:]
    mime_type = f'image/{ext}' if ext != 'jpg' else 'image/jpeg'
    return f'data:{mime_type};base64,{data}'

 # 本地图片路径
local_image = 'E:/1.jpg'

ref_images = [
    {
        "type": "reference_image",
        "url": load_image_base64(local_image)
    }
]

def sample_async_call():
    """异步调用参考生视频 API"""
    print('----creating task...----')

    # 异步创建任务
    rsp = VideoSynthesis.async_call(
        api_key=api_key,
        model="happyhorse-1.1-r2v",
        prompt="[Image 1]中的人物打羽毛球，飞起来进行扣杀相关的动作。",
        media=ref_images,
        resolution="720P",
        ratio="16:9",
        duration=5,
        watermark=True
    )

    if rsp.status_code != HTTPStatus.OK:
        print(f'Failed: {rsp.code}, {rsp.message}')
        return

    task_id = rsp.output.task_id
    print(f'Task created: {task_id}')
    print('Waiting...')

    # 轮询等待结果
    while True:
        time.sleep(10)
        rsp = VideoSynthesis.wait(task=rsp, api_key=api_key)

        if rsp.status_code != HTTPStatus.OK:
            print(f'Query failed: {rsp.code}')
            return

        status = rsp.output.task_status
        print(f'Status: {status}')

        if status == 'SUCCEEDED':
            print('Video URL:', rsp.output.video_url)
            return
        elif status in ['FAILED', 'CANCELED', 'UNKNOWN']:
            print('Task failed')
            return

if __name__ == '__main__':
    sample_async_call()
