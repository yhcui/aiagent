import os
from http import HTTPStatus
from dashscope import VideoSynthesis
import dashscope
from dotenv import load_dotenv
import base64

load_dotenv()
# 以下为北京地域URL，各地域的URL不同，获取URL：https://help.aliyun.com/zh/model-studio/text-to-video-api-reference
dashscope.base_http_api_url = 'https://llm-tgs20vajm1ikqveg.cn-beijing.maas.aliyuncs.com/api/v1'
# 各地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
api_key = os.getenv("DASHSCOPE_API_KEY")

print('please wait...')
rsp = VideoSynthesis.call(api_key=api_key,
                          model='happyhorse-1.1-t2v',
                          prompt='''### 完整版正向提示词
                                日系动画电影画面，新海诚式细腻天空与通透光影，年轻动漫美女，长发随风飘动，精致五官，浅色连衣裙，在夕阳下的樱花岸边独自跳舞，缓慢旋转、抬手、转身、裙摆自然飘动，动作连贯优雅，海风轻轻吹起发丝和衣摆，樱花花瓣随风环绕，远处有柔和云层和金色夕阳，镜头从中景缓慢推进并轻微环绕，人物始终清晰，背景有景深，色彩明亮但柔和，蓝粉金渐变色调，细腻背景美术，高质量二维动画，电影级构图，稳定镜头，流畅动态，9:16 竖屏
                                负面提示词
                                脸部变形，五官漂移，肢体畸形，手指异常，身体比例错误，穿模，裙摆僵硬，动作突变，镜头剧烈晃动，画面闪烁，背景崩坏，物体融化，人物突然变脸，服装变化，水印，文字，logo，写实照片，3D 渲染，低清晰度''',
                          resolution="720P",
                          ratio="16:9",
                          duration=15,
                          watermark=True)
print(rsp)
if rsp.status_code == HTTPStatus.OK:
    print("video_url:", rsp.output.video_url)
else:
    print('Failed, status_code: %s, code: %s, message: %s' % (rsp.status_code, rsp.code, rsp.message))