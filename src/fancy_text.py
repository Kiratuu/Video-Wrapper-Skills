"""
Fancy text generator with pop art style effects
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from animations import spring, interpolate


class FancyTextGenerator:
    def __init__(self, width=1920, height=1080, fps=30):
        self.width = width
        self.height = height
        self.fps = fps

        # 字体配置
        self.font_paths = [
            "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS 中文字体（首选）
            "/System/Library/Fonts/STHeiti Light.ttc",   # macOS 中文字体（备选）
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS Unicode 字体
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux 文泉驿
            "C:\\Windows\\Fonts\\msyh.ttc",  # Windows 微软雅黑
            "C:\\Windows\\Fonts\\simhei.ttf",  # Windows 黑体
        ]
        self.font_size = 52

    def _get_font(self, size=None):
        """尝试加载可用字体"""
        if size is None:
            size = self.font_size

        for font_path in self.font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue

        # 如果都失败，使用默认字体
        return ImageFont.load_default()

    def create_text_frame(self, text, frame, start_frame, duration_frames, style='emphasis', position=(960, 300)):
        """
        创建单帧花字图片

        参数:
            text: 文字内容
            frame: 当前帧
            start_frame: 开始帧
            duration_frames: 总帧数
            style: 样式类型 ('emphasis', 'term', 'number')
            position: 位置 (x, y)

        返回:
            PIL Image 对象（RGBA格式）
        """
        relative_frame = frame - start_frame

        # 创建透明画布
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 加载字体
        font = self._get_font()

        # 计算spring动画
        scale = spring(
            relative_frame,
            self.fps,
            from_value=0.8,
            to_value=1.15,
            damping=12,
            stiffness=200
        )

        # 计算淡出
        fade_start = duration_frames - 10
        opacity = interpolate(
            relative_frame,
            [fade_start, duration_frames],
            [1.0, 0.0],
            extrapolate='clamp'
        )

        # 计算抖动
        wobble = np.sin(relative_frame * 0.2) * 3  # 度数

        # 根据样式选择颜色
        if style == 'emphasis':
            # 黄色主体 + 红色描边
            text_color = (255, 237, 78)  # 黄色
            stroke_color = (255, 23, 68)  # 红色
            stroke_width = 4
        elif style == 'term':
            # 青色主体 + 品红描边
            text_color = (0, 229, 255)  # 青色
            stroke_color = (233, 30, 99)  # 品红
            stroke_width = 4
        else:  # number
            # 橙色主体 + 深蓝描边
            text_color = (255, 109, 0)  # 橙色
            stroke_color = (26, 35, 126)  # 深蓝
            stroke_width = 4

        # 添加透明度
        text_color_with_alpha = (*text_color, int(255 * opacity))
        stroke_color_with_alpha = (*stroke_color, int(255 * opacity))

        # 获取文字边界
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 创建临时图像（足够大以容纳旋转后的文字）
        temp_size = int(max(text_width, text_height) * 2 * scale) + 100
        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)

        # 在临时图像中心绘制文字
        temp_center = temp_size // 2
        text_x = temp_center - text_width // 2
        text_y = temp_center - text_height // 2

        # 绘制描边（通过偏移绘制多次）
        for offset_x in range(-stroke_width, stroke_width + 1):
            for offset_y in range(-stroke_width, stroke_width + 1):
                if offset_x != 0 or offset_y != 0:
                    temp_draw.text(
                        (text_x + offset_x, text_y + offset_y),
                        text,
                        font=font,
                        fill=stroke_color_with_alpha
                    )

        # 绘制主文字
        temp_draw.text((text_x, text_y), text, font=font, fill=text_color_with_alpha)

        # 应用缩放和旋转
        scaled_size = (int(temp_size * scale), int(temp_size * scale))
        temp_img = temp_img.resize(scaled_size, Image.Resampling.LANCZOS)
        temp_img = temp_img.rotate(wobble, expand=True, resample=Image.Resampling.BICUBIC)

        # 添加阴影（drop shadow）
        shadow = temp_img.copy()
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))

        # 将临时图像粘贴到主画布
        paste_x = position[0] - temp_img.width // 2 + 6  # 阴影偏移
        paste_y = position[1] - temp_img.height // 2 + 6
        img.paste(shadow, (paste_x, paste_y), shadow)

        paste_x = position[0] - temp_img.width // 2
        paste_y = position[1] - temp_img.height // 2
        img.paste(temp_img, (paste_x, paste_y), temp_img)

        return img

    def generate_text_clip(self, keyword, index):
        """
        生成完整的花字视频片段

        参数:
            keyword: {text, startMs, endMs, style}
            index: 花字索引（用于定位）

        返回:
            MoviePy VideoClip
        """
        from moviepy import VideoClip

        start_time = keyword['startMs'] / 1000.0
        end_time = keyword['endMs'] / 1000.0
        duration = end_time - start_time

        start_frame = int(start_time * self.fps)
        duration_frames = int(duration * self.fps)

        # 计算位置（左右交替）
        x_offset = (index % 2) * 400
        y_offset = (index // 2) * 100
        position = (self.width // 2 - 300 + x_offset, 300 + y_offset)

        # 生成每一帧
        def make_frame(t):
            frame = int(t * self.fps)
            img = self.create_text_frame(
                keyword['text'],
                start_frame + frame,
                start_frame,
                duration_frames,
                keyword['style'],
                position
            )
            return np.array(img)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.with_start(start_time)

        return clip
