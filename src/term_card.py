"""
Term definition card generator
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from animations import spring, interpolate


class TermCardGenerator:
    def __init__(self, width=1920, height=1080, fps=30):
        self.width = width
        self.height = height
        self.fps = fps

        # 卡片配置
        self.card_width = 400
        self.card_height = 250
        self.position = (self.width - 50 - self.card_width, 50)  # 右上角

        # 字体路径
        self.font_paths_zh = [
            "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS 华文黑体（首选）
            "/System/Library/Fonts/STHeiti Light.ttc",   # macOS 华文黑体细体
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS Unicode
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux 文泉驿
            "C:\\Windows\\Fonts\\msyh.ttc",  # Windows 微软雅黑
            "C:\\Windows\\Fonts\\simhei.ttf",  # Windows 黑体
        ]
        self.font_paths_en = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]

    def _get_font(self, font_paths, size):
        """尝试加载可用字体"""
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    def create_card_frame(self, term, frame, start_frame, duration_frames):
        """
        创建单帧卡片图片

        参数:
            term: {chinese, english, description, displayDurationSeconds}
            frame: 当前帧
            start_frame: 开始帧
            duration_frames: 总帧数

        返回:
            PIL Image 对象（RGBA格式）
        """
        relative_frame = frame - start_frame

        # 创建透明画布
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))

        # Spring 滑入动画
        slide_progress = spring(
            relative_frame,
            self.fps,
            from_value=0,
            to_value=1,
            damping=15,
            stiffness=180
        )

        translate_x = interpolate(
            slide_progress,
            [0, 1],
            [100, 0],
            extrapolate='clamp'
        )

        scale = interpolate(
            slide_progress,
            [0, 1],
            [0.8, 1.0],
            extrapolate='clamp'
        )

        # 淡出动画
        exit_start = duration_frames - int(0.5 * self.fps)
        opacity = interpolate(
            relative_frame,
            [exit_start, duration_frames],
            [1.0, 0.0],
            extrapolate='clamp'
        )

        # 呼吸效果
        breathe = np.sin(relative_frame * 0.1) * 2

        # 创建卡片图像
        card_width = int(self.card_width * scale)
        card_height = int(self.card_height * scale)
        card_img = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_img)

        # 绘制卡片背景（圆角矩形）
        bg_color = (0, 0, 0, int(217 * opacity))  # rgba(0,0,0,0.85) * opacity
        card_draw.rounded_rectangle(
            [(0, 0), (card_width, card_height)],
            radius=16,
            fill=bg_color
        )

        # 绘制渐变边框（简化版，使用多层矩形模拟）
        for i in range(2):
            border_alpha = int(255 * opacity * (1 - i * 0.5))
            border_colors = [
                (255, 215, 0, border_alpha),   # 金色
                (78, 205, 196, border_alpha),  # 青色
                (255, 107, 107, border_alpha)  # 红色
            ]
            color_index = (int(relative_frame * 0.02) + i) % len(border_colors)
            card_draw.rounded_rectangle(
                [(i, i), (card_width - i, card_height - i)],
                radius=16,
                outline=border_colors[color_index],
                width=2
            )

        # 加载字体
        title_font = self._get_font(self.font_paths_zh, 32)
        subtitle_font = self._get_font(self.font_paths_en, 16)
        desc_font = self._get_font(self.font_paths_zh, 16)

        # 标题（中文术语）
        title_color = (255, 215, 0, int(255 * opacity))  # 金色
        card_draw.text((24, 24), term['chinese'], font=title_font, fill=title_color)

        # 副标题（英文）
        subtitle_color = (176, 176, 176, int(255 * opacity))  # 灰色
        card_draw.text((24, 64), term['english'], font=subtitle_font, fill=subtitle_color)

        # 描述
        desc_color = (224, 224, 224, int(255 * opacity))  # 浅灰

        # 简单的文字换行
        description = term['description']
        max_width = card_width - 48
        lines = []
        words = description
        # 简化版：每30个字符一行
        for i in range(0, len(words), 30):
            lines.append(words[i:i+30])

        y_pos = 100
        for line in lines[:4]:  # 最多4行
            card_draw.text((24, y_pos), line, font=desc_font, fill=desc_color)
            y_pos += 24

        # 计算最终位置
        final_x = self.position[0] + translate_x + breathe
        final_y = self.position[1]

        # 粘贴卡片到主画布
        img.paste(card_img, (int(final_x), int(final_y)), card_img)

        return img

    def generate_card_clip(self, term):
        """
        生成完整的卡片视频片段
        """
        from moviepy import VideoClip

        start_time = term['firstAppearanceMs'] / 1000.0
        duration = term.get('displayDurationSeconds', 6)

        start_frame = int(start_time * self.fps)
        duration_frames = int(duration * self.fps)

        def make_frame(t):
            frame = int(t * self.fps)
            img = self.create_card_frame(
                term,
                start_frame + frame,
                start_frame,
                duration_frames
            )
            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.with_start(start_time)

        return clip
