"""
海报生成服务 - 基于Pillow
"""
import os
import io
import json
import requests
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from app.config import settings
from loguru import logger


class PosterService:
    """海报生成服务"""

    def __init__(self):
        self.static_dir = settings.STATIC_DIR
        self.font_dir = os.path.join(self.static_dir, "fonts")
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保目录存在"""
        os.makedirs(self.static_dir, exist_ok=True)
        os.makedirs(self.font_dir, exist_ok=True)
        os.makedirs(os.path.join(self.static_dir, "posters"), exist_ok=True)

    def _load_font(self, font_size: int, font_path: str = None) -> ImageFont.FreeTypeFont:
        """加载字体"""
        # 优先使用系统字体
        system_fonts = [
            "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
            "C:/Windows/Fonts/simsun.ttc",  # Windows 宋体
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            "/System/Library/Fonts/PingFang.ttc",  # macOS
        ]

        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, font_size)

        for font_file in system_fonts:
            if os.path.exists(font_file):
                try:
                    return ImageFont.truetype(font_file, font_size)
                except:
                    continue

        # 默认字体
        return ImageFont.load_default()

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """下载远程图片"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
        except Exception as e:
            logger.error(f"下载图片失败: {url}, {e}")
        return None

    def _create_qr_code(self, url: str, size: int = 200) -> Optional[Image.Image]:
        """生成二维码（简化版，实际应使用qrcode库）"""
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            return img.resize((size, size))
        except Exception as e:
            logger.error(f"生成二维码失败: {e}")
            return None

    async def generate_role_poster(
        self,
        role_name: str,
        role_image_url: str,
        role_description: str,
        match_score: float,
        user_nickname: str,
        mini_program_path: str,
        qr_code_url: str = None,
    ) -> Optional[str]:
        """
        生成角色测算海报

        参数:
            role_name: 角色名称
            role_image_url: 角色图片URL
            role_description: 角色描述
            match_score: 匹配度
            user_nickname: 用户昵称
            mini_program_path: 小程序路径
            qr_code_url: 二维码内容URL
        """
        try:
            # 海报尺寸（适配微信分享图片）
            width, height = 600, 900
            bg_color = (255, 255, 255)

            # 创建画布
            img = Image.new("RGB", (width, height), bg_color)
            draw = ImageDraw.Draw(img)

            # 加载字体
            title_font = self._load_font(40)
            name_font = self._load_font(36)
            desc_font = self._load_font(24)
            small_font = self._load_font(20)

            # 1. 顶部装饰条
            draw.rectangle([(0, 0), (width, 8)], fill=(255, 200, 100))

            # 2. 标题
            title = "我的角色是..."
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text(((width - title_width) // 2, 30), title, fill=(80, 80, 80), font=title_font)

            # 3. 角色图片
            role_img_y = 90
            if role_image_url:
                role_img = self._download_image(role_image_url)
                if role_img:
                    # 居中显示
                    img_width = min(400, role_img.width)
                    img_height = int(img_width * role_img.height / role_img.width)
                    role_img = role_img.resize((img_width, img_height))
                    x = (width - img_width) // 2
                    img.paste(role_img, (x, role_img_y))

            # 4. 角色名称
            name_y = role_img_y + 320
            name_bbox = draw.textbbox((0, 0), role_name, font=name_font)
            name_width = name_bbox[2] - name_bbox[0]
            draw.text(((width - name_width) // 2, name_y), role_name, fill=(220, 160, 60), font=name_font)

            # 5. 匹配度
            score_y = name_y + 55
            score_text = f"匹配度 {match_score:.1f}%"
            score_bbox = draw.textbbox((0, 0), score_text, font=desc_font)
            score_width = score_bbox[2] - score_bbox[0]
            draw.text(((width - score_width) // 2, score_y), score_text, fill=(200, 100, 100), font=desc_font)

            # 6. 角色描述（限制2行）
            desc_y = score_y + 50
            # 简化处理，实际应考虑换行
            desc_text = role_description[:40] + "..." if len(role_description) > 40 else role_description
            lines = self._wrap_text(desc_text, desc_font, width - 80)
            for i, line in enumerate(lines[:2]):
                line_bbox = draw.textbbox((0, 0), line, font=desc_font)
                line_width = line_bbox[2] - line_bbox[0]
                draw.text(((width - line_width) // 2, desc_y + i * 35), line, fill=(100, 100, 100), font=desc_font)

            # 7. 用户昵称
            nickname_y = desc_y + 100
            nickname_text = f"— {user_nickname}"
            nickname_bbox = draw.textbbox((0, 0), nickname_text, font=small_font)
            nickname_width = nickname_bbox[2] - nickname_bbox[0]
            draw.text(((width - nickname_width) // 2, nickname_y), nickname_text, fill=(150, 150, 150), font=small_font)

            # 8. 二维码
            qr_y = height - 180
            if qr_code_url:
                qr_img = self._create_qr_code(qr_code_url, size=150)
                if qr_img:
                    qr_x = (width - 150) // 2
                    img.paste(qr_img, (qr_x, qr_y))

            # 9. 底部提示
            tip_text = "长按识别 查看详情"
            tip_bbox = draw.textbbox((0, 0), tip_text, font=small_font)
            tip_width = tip_bbox[2] - tip_bbox[0]
            draw.text(((width - tip_width) // 2, height - 30), tip_text, fill=(180, 180, 180), font=small_font)

            # 保存图片
            filename = f"poster_{int(time.time())}_{hash(role_name) % 10000}.png"
            filepath = os.path.join(self.static_dir, "posters", filename)
            img.save(filepath, "PNG")

            logger.info(f"海报生成成功: {filepath}")
            return f"/static/posters/{filename}"

        except Exception as e:
            logger.error(f"生成海报异常: {e}")
            return None

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """文字换行处理（简化版）"""
        lines = []
        current_line = ""
        for char in text:
            test_line = current_line + char
            bbox = self._load_font(24).getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
        return lines if lines else [""]


# 全局海报服务实例
poster_service = PosterService()

# 需要time模块
import time
