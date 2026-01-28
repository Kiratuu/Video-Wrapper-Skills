#!/usr/bin/env python3
"""
Interview video processor - Main script
Adds fancy text and term definition cards to interview videos

Supports two rendering backends:
- browser: HTML/CSS/Anime.js via Playwright (default, better visual quality)
- pil: Python PIL (fallback, no additional dependencies)
"""
import json
import sys
import os
import argparse
import shutil
import tempfile

# Add src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moviepy import VideoFileClip, CompositeVideoClip


def check_browser_renderer_available():
    """Check if browser renderer (Playwright) is available"""
    try:
        from browser_renderer import check_playwright_installed
        return check_playwright_installed()
    except ImportError:
        return False


def process_video(video_path, subtitle_path, config_path, output_path, renderer='auto'):
    """
    主处理函数

    参数:
        video_path: 输入视频路径
        subtitle_path: 字幕文件路径（目前未使用，保留用于将来扩展）
        config_path: 配置文件路径
        output_path: 输出视频路径
        renderer: 渲染器类型 ('browser', 'pil', 'auto')
    """
    print(f"🎬 正在处理视频: {video_path}")

    # 验证输入文件存在
    if not os.path.exists(video_path):
        print(f"❌ 错误: 视频文件不存在: {video_path}")
        sys.exit(1)

    if not os.path.exists(config_path):
        print(f"❌ 错误: 配置文件不存在: {config_path}")
        sys.exit(1)

    # 确定渲染器
    if renderer == 'auto':
        if check_browser_renderer_available():
            renderer = 'browser'
            print("🌐 使用浏览器渲染器 (HTML/CSS/Anime.js)")
        else:
            renderer = 'pil'
            print("🎨 使用 PIL 渲染器 (Playwright 不可用)")
    elif renderer == 'browser':
        if not check_browser_renderer_available():
            print("❌ 错误: 浏览器渲染器不可用")
            print("请运行以下命令安装:")
            print("  pip install playwright")
            print("  playwright install chromium")
            sys.exit(1)
        print("🌐 使用浏览器渲染器 (HTML/CSS/Anime.js)")
    else:
        print("🎨 使用 PIL 渲染器")

    # 1. 加载配置
    print("📋 加载配置文件...")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 2. 加载原始视频
    print("📹 加载原始视频...")
    video = VideoFileClip(video_path)
    print(f"   - 分辨率: {video.w}x{video.h}")
    print(f"   - 帧率: {video.fps} fps")
    print(f"   - 时长: {video.duration:.2f} 秒")

    # Track temp directories for cleanup
    temp_dirs = []

    try:
        if renderer == 'browser':
            text_clips, card_clips = _generate_clips_browser(
                config, video.w, video.h, video.fps, temp_dirs
            )
        else:
            text_clips, card_clips = _generate_clips_pil(
                config, video.w, video.h, video.fps
            )

        # 5. 合成所有图层
        print("🎨 合成视频图层...")
        all_clips = [video] + text_clips + card_clips
        final_video = CompositeVideoClip(all_clips, size=(video.w, video.h))

        # 6. 导出最终视频
        print(f"💾 导出最终视频到: {output_path}")
        print("   (这可能需要几分钟，请耐心等待...)")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=video.fps,
            preset='medium',
            threads=4,
            logger='bar'  # 显示进度条
        )

        # 清理
        video.close()
        final_video.close()

    finally:
        # Clean up temp directories
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    print("✅ 处理完成！")
    print(f"📁 输出文件: {output_path}")


def _generate_clips_browser(config, width, height, fps, temp_dirs):
    """Generate clips using browser renderer"""
    from browser_renderer import BrowserRenderer
    from moviepy import ImageSequenceClip

    all_effect_clips = []

    # Get theme from config (default: notion)
    theme = config.get('theme', 'notion')
    print(f"🎨 主题: {theme}")

    with BrowserRenderer(width=width, height=height, fps=fps) as renderer:

        # 1. 生成人物条片段
        lower_thirds = config.get('lowerThirds', [])
        if lower_thirds:
            print(f"👤 生成人物条 ({len(lower_thirds)} 个)...")
            for i, lt in enumerate(lower_thirds):
                print(f"   - 人物条: {lt['name']}")
                temp_dir = tempfile.mkdtemp(prefix=f'lower_third_{i}_')
                temp_dirs.append(temp_dir)

                lt_config = {
                    'name': lt['name'],
                    'role': lt.get('role', ''),
                    'company': lt.get('company', ''),
                    'theme': theme,
                    'durationMs': lt.get('durationMs', 5000)
                }
                frame_paths = renderer.render_lower_third_frames(lt_config, temp_dir)
                clip = ImageSequenceClip(frame_paths, fps=fps)
                clip = clip.with_start(lt['startMs'] / 1000.0)
                all_effect_clips.append(clip)

        # 2. 生成章节标题片段
        chapters = config.get('chapterTitles', [])
        if chapters:
            print(f"📑 生成章节标题 ({len(chapters)} 个)...")
            for i, ch in enumerate(chapters):
                print(f"   - 章节: {ch['title']}")
                temp_dir = tempfile.mkdtemp(prefix=f'chapter_{i}_')
                temp_dirs.append(temp_dir)

                ch_config = {
                    'number': ch.get('number', ''),
                    'title': ch['title'],
                    'subtitle': ch.get('subtitle', ''),
                    'theme': theme,
                    'durationMs': ch.get('durationMs', 4000)
                }
                frame_paths = renderer.render_chapter_title_frames(ch_config, temp_dir)
                clip = ImageSequenceClip(frame_paths, fps=fps)
                clip = clip.with_start(ch['startMs'] / 1000.0)
                all_effect_clips.append(clip)

        # 3. 生成花字片段
        key_phrases = config.get('keyPhrases', [])
        if key_phrases:
            print(f"✨ 生成花字动画 ({len(key_phrases)} 个)...")
            for i, phrase in enumerate(key_phrases):
                print(f"   - 花字 {i+1}: {phrase['text']}")
                temp_dir = tempfile.mkdtemp(prefix=f'fancy_text_{i}_')
                temp_dirs.append(temp_dir)

                # Calculate position: above subtitles area, alternating left/right
                # Subtitles typically at bottom 15-20% of screen, so place fancy text at top 15-25%
                x_offset = (i % 2) * 300  # Slight horizontal offset for variety
                position = phrase.get('position', {
                    'x': width // 2 - 150 + x_offset,
                    'y': 120 + (i % 3) * 40  # Top area: 120-200px from top
                })

                frame_config = {
                    'text': phrase['text'],
                    'style': phrase.get('style', 'emphasis'),
                    'theme': theme,
                    'position': position,
                    'startMs': phrase['startMs'],
                    'endMs': phrase['endMs']
                }
                frame_paths = renderer.render_fancy_text_frames(frame_config, temp_dir)
                clip = ImageSequenceClip(frame_paths, fps=fps)
                clip = clip.with_start(phrase['startMs'] / 1000.0)
                all_effect_clips.append(clip)

        # 4. 生成名词卡片片段
        term_defs = config.get('termDefinitions', [])
        if term_defs:
            print(f"📋 生成名词卡片 ({len(term_defs)} 个)...")
            for i, term in enumerate(term_defs):
                print(f"   - 卡片: {term['chinese']}")
                temp_dir = tempfile.mkdtemp(prefix=f'term_card_{i}_')
                temp_dirs.append(temp_dir)

                card_config = {
                    'chinese': term['chinese'],
                    'english': term['english'],
                    'description': term['description'],
                    'theme': theme,
                    'displayDurationSeconds': term.get('displayDurationSeconds', 6)
                }
                frame_paths = renderer.render_term_card_frames(card_config, temp_dir)
                clip = ImageSequenceClip(frame_paths, fps=fps)
                clip = clip.with_start(term['firstAppearanceMs'] / 1000.0)
                all_effect_clips.append(clip)

        # 5. 生成金句卡片片段
        quotes = config.get('quotes', [])
        if quotes:
            print(f"💬 生成金句卡片 ({len(quotes)} 个)...")
            for i, quote in enumerate(quotes):
                print(f"   - 金句: {quote['text'][:20]}...")
                temp_dir = tempfile.mkdtemp(prefix=f'quote_{i}_')
                temp_dirs.append(temp_dir)

                quote_config = {
                    'text': quote['text'],
                    'author': quote.get('author', ''),
                    'theme': theme,
                    'position': quote.get('position', {'x': width // 2, 'y': height // 2}),
                    'durationMs': quote.get('durationMs', 5000)
                }
                frame_paths = renderer.render_quote_callout_frames(quote_config, temp_dir)
                clip = ImageSequenceClip(frame_paths, fps=fps)
                clip = clip.with_start(quote['startMs'] / 1000.0)
                all_effect_clips.append(clip)

        # 6. 生成数据动画片段
        stats = config.get('stats', [])
        if stats:
            print(f"📊 生成数据动画 ({len(stats)} 个)...")
            for i, stat in enumerate(stats):
                print(f"   - 数据: {stat.get('prefix', '')}{stat['number']}{stat.get('unit', '')}")
                temp_dir = tempfile.mkdtemp(prefix=f'stats_{i}_')
                temp_dirs.append(temp_dir)

                stat_config = {
                    'prefix': stat.get('prefix', ''),
                    'number': stat['number'],
                    'unit': stat.get('unit', ''),
                    'label': stat.get('label', ''),
                    'theme': theme,
                    'position': stat.get('position', {'x': width // 2, 'y': height // 2}),
                    'durationMs': stat.get('durationMs', 4000)
                }
                frame_paths = renderer.render_animated_stats_frames(stat_config, temp_dir)
                clip = ImageSequenceClip(frame_paths, fps=fps)
                clip = clip.with_start(stat['startMs'] / 1000.0)
                all_effect_clips.append(clip)

        # 7. 生成要点列表片段
        bullet_points = config.get('bulletPoints', [])
        if bullet_points:
            print(f"📝 生成要点列表 ({len(bullet_points)} 个)...")
            for i, bp in enumerate(bullet_points):
                print(f"   - 要点: {bp.get('title', '要点列表')}")
                temp_dir = tempfile.mkdtemp(prefix=f'bullets_{i}_')
                temp_dirs.append(temp_dir)

                bp_config = {
                    'title': bp.get('title', ''),
                    'points': bp['points'],
                    'theme': theme,
                    'position': bp.get('position', {'x': 100, 'y': 300}),
                    'durationMs': bp.get('durationMs', 6000)
                }
                frame_paths = renderer.render_bullet_points_frames(bp_config, temp_dir)
                clip = ImageSequenceClip(frame_paths, fps=fps)
                clip = clip.with_start(bp['startMs'] / 1000.0)
                all_effect_clips.append(clip)

        # 8. 生成社交媒体条片段
        social_bars = config.get('socialBars', [])
        if social_bars:
            print(f"📱 生成社交媒体条 ({len(social_bars)} 个)...")
            for i, sb in enumerate(social_bars):
                print(f"   - 社交: {sb['handle']}")
                temp_dir = tempfile.mkdtemp(prefix=f'social_{i}_')
                temp_dirs.append(temp_dir)

                sb_config = {
                    'platform': sb.get('platform', 'twitter'),
                    'label': sb.get('label', '关注'),
                    'handle': sb['handle'],
                    'theme': theme,
                    'position': sb.get('position', {'x': width - 320, 'y': height - 130}),
                    'durationMs': sb.get('durationMs', 8000)  # Default 8 seconds for social bar
                }
                frame_paths = renderer.render_social_bar_frames(sb_config, temp_dir)
                clip = ImageSequenceClip(frame_paths, fps=fps)
                clip = clip.with_start(sb['startMs'] / 1000.0)
                all_effect_clips.append(clip)

    # Return all clips (split into two lists for compatibility)
    return all_effect_clips, []


def _generate_clips_pil(config, width, height, fps):
    """Generate clips using PIL renderer (legacy)"""
    from fancy_text import FancyTextGenerator
    from term_card import TermCardGenerator

    # 3. 生成花字片段
    print(f"✨ 生成花字动画 ({len(config.get('keyPhrases', []))} 个)...")
    text_gen = FancyTextGenerator(width=width, height=height, fps=fps)
    text_clips = []
    for i, phrase in enumerate(config.get('keyPhrases', [])):
        print(f"   - 花字 {i+1}: {phrase['text']}")
        clip = text_gen.generate_text_clip(phrase, i)
        text_clips.append(clip)

    # 4. 生成卡片片段
    print(f"📋 生成名词卡片 ({len(config.get('termDefinitions', []))} 个)...")
    card_gen = TermCardGenerator(width=width, height=height, fps=fps)
    card_clips = []
    for term in config.get('termDefinitions', []):
        print(f"   - 卡片: {term['chinese']}")
        clip = card_gen.generate_card_clip(term)
        card_clips.append(clip)

    return text_clips, card_clips


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='为访谈视频添加花字和名词解释卡片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python video_processor.py video.mp4 subs.srt config.json output.mp4
  python video_processor.py video.mp4 subs.srt config.json -r pil  # 使用 PIL 渲染器
  python video_processor.py video.mp4 subs.srt config.json -r browser  # 使用浏览器渲染器
        """
    )

    parser.add_argument('video', help='输入视频文件路径')
    parser.add_argument('subtitles', help='字幕文件路径 (.srt)')
    parser.add_argument('config', help='配置文件路径 (.json)')
    parser.add_argument('output', nargs='?', default=None, help='输出视频路径 (默认: output.mp4)')
    parser.add_argument(
        '-r', '--renderer',
        choices=['auto', 'browser', 'pil'],
        default='auto',
        help='渲染器类型: auto (自动选择), browser (HTML/CSS), pil (Python PIL)'
    )

    args = parser.parse_args()

    # 获取调用脚本时的工作目录（保存在环境变量中）
    original_cwd = os.environ.get('ORIGINAL_CWD', os.getcwd())

    # 默认输出路径为原始工作目录下的 output.mp4
    if args.output:
        output_path = args.output
        # 如果是相对路径，相对于原始工作目录
        if not os.path.isabs(output_path):
            output_path = os.path.join(original_cwd, output_path)
    else:
        output_path = os.path.join(original_cwd, 'output.mp4')

    try:
        process_video(
            args.video,
            args.subtitles,
            args.config,
            output_path,
            renderer=args.renderer
        )
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
