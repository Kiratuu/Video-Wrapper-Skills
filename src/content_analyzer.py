"""
Content analyzer for interview videos
Analyzes subtitles and suggests visual effects components
"""
import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from pathlib import Path


@dataclass
class LowerThirdSuggestion:
    """人物条建议"""
    component: str = "lower_third"
    name: str = ""
    role: str = ""
    company: str = ""
    startMs: int = 0
    durationMs: int = 5000


@dataclass
class ChapterTitleSuggestion:
    """章节标题建议"""
    component: str = "chapter_title"
    number: str = ""
    title: str = ""
    subtitle: str = ""
    startMs: int = 0
    durationMs: int = 4000


@dataclass
class FancyTextSuggestion:
    """
    花字建议

    注意：text 必须是短语形式，概括说话人当时的观点
    - ✅ 正确："AI发展是平滑曲线"、"智能增长类似摩尔定律"
    - ❌ 错误："人工智能"、"摩尔定律"（单词应该用名词卡片）
    """
    component: str = "fancy_text"
    text: str = ""  # 短语观点概括，非单词
    style: str = "emphasis"  # emphasis, term, number
    startMs: int = 0
    endMs: int = 0
    reason: str = ""  # 为什么建议这个


@dataclass
class TermCardSuggestion:
    """名词卡片建议"""
    component: str = "term_card"
    chinese: str = ""
    english: str = ""
    description: str = ""
    firstAppearanceMs: int = 0
    displayDurationSeconds: int = 6


@dataclass
class QuoteCalloutSuggestion:
    """金句卡片建议"""
    component: str = "quote_callout"
    text: str = ""
    author: str = ""
    startMs: int = 0
    durationMs: int = 5000
    reason: str = ""


@dataclass
class AnimatedStatsSuggestion:
    """数据动画建议"""
    component: str = "animated_stats"
    prefix: str = ""
    number: int = 0
    unit: str = ""
    label: str = ""
    startMs: int = 0
    durationMs: int = 4000


@dataclass
class BulletPointsSuggestion:
    """要点列表建议"""
    component: str = "bullet_points"
    title: str = ""
    points: List[str] = field(default_factory=list)
    startMs: int = 0
    durationMs: int = 6000


@dataclass
class SocialBarSuggestion:
    """社交媒体条建议"""
    component: str = "social_bar"
    platform: str = "twitter"  # twitter, weibo, youtube
    label: str = "关注"
    handle: str = ""
    startMs: int = 0
    durationMs: int = 8000  # Default 8 seconds for better visibility


@dataclass
class EffectsSuggestion:
    """完整的特效建议"""
    theme: str = "notion"
    speaker: Optional[LowerThirdSuggestion] = None
    chapters: List[ChapterTitleSuggestion] = field(default_factory=list)
    fancyTexts: List[FancyTextSuggestion] = field(default_factory=list)
    termCards: List[TermCardSuggestion] = field(default_factory=list)
    quotes: List[QuoteCalloutSuggestion] = field(default_factory=list)
    stats: List[AnimatedStatsSuggestion] = field(default_factory=list)
    bulletPoints: List[BulletPointsSuggestion] = field(default_factory=list)
    socialBars: List[SocialBarSuggestion] = field(default_factory=list)


def parse_srt(srt_path: str) -> List[dict]:
    """
    解析 SRT 字幕文件

    返回:
        List of {index, start_ms, end_ms, text}
    """
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # SRT pattern: index, timestamp, text
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.*(?:\n|$))*?)(?=\n\d+\n|\Z)'
    matches = re.findall(pattern, content, re.MULTILINE)

    subtitles = []
    for match in matches:
        index = int(match[0])
        start_time = match[1]
        end_time = match[2]
        text = match[3].strip()

        # Convert timestamp to milliseconds
        start_ms = timestamp_to_ms(start_time)
        end_ms = timestamp_to_ms(end_time)

        subtitles.append({
            'index': index,
            'start_ms': start_ms,
            'end_ms': end_ms,
            'text': text
        })

    return subtitles


def timestamp_to_ms(timestamp: str) -> int:
    """Convert SRT timestamp to milliseconds"""
    # Format: HH:MM:SS,mmm
    parts = timestamp.replace(',', ':').split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    ms = int(parts[3])
    return hours * 3600000 + minutes * 60000 + seconds * 1000 + ms


def get_full_text(subtitles: List[dict]) -> str:
    """获取完整文本用于分析"""
    return '\n'.join([s['text'] for s in subtitles])


def find_subtitle_at_time(subtitles: List[dict], time_ms: int) -> Optional[dict]:
    """找到指定时间点的字幕"""
    for s in subtitles:
        if s['start_ms'] <= time_ms <= s['end_ms']:
            return s
    return None


def suggestion_to_config(suggestion: EffectsSuggestion) -> dict:
    """
    将建议转换为视频处理配置格式

    Args:
        suggestion: EffectsSuggestion 对象

    Returns:
        可直接用于 video_processor 的配置字典
    """
    config = {
        'theme': suggestion.theme,
        'keyPhrases': [],
        'termDefinitions': [],
        'lowerThirds': [],
        'chapterTitles': [],
        'quotes': [],
        'stats': [],
        'bulletPoints': [],
        'socialBars': []
    }

    # 转换花字
    for ft in suggestion.fancyTexts:
        config['keyPhrases'].append({
            'text': ft.text,
            'style': ft.style,
            'startMs': ft.startMs,
            'endMs': ft.endMs
        })

    # 转换名词卡片
    for tc in suggestion.termCards:
        config['termDefinitions'].append({
            'chinese': tc.chinese,
            'english': tc.english,
            'description': tc.description,
            'firstAppearanceMs': tc.firstAppearanceMs,
            'displayDurationSeconds': tc.displayDurationSeconds
        })

    # 转换人物条
    if suggestion.speaker:
        config['lowerThirds'].append({
            'name': suggestion.speaker.name,
            'role': suggestion.speaker.role,
            'company': suggestion.speaker.company,
            'startMs': suggestion.speaker.startMs,
            'durationMs': suggestion.speaker.durationMs
        })

    # 转换章节标题
    for ch in suggestion.chapters:
        config['chapterTitles'].append({
            'number': ch.number,
            'title': ch.title,
            'subtitle': ch.subtitle,
            'startMs': ch.startMs,
            'durationMs': ch.durationMs
        })

    # 转换金句
    for q in suggestion.quotes:
        config['quotes'].append({
            'text': q.text,
            'author': q.author,
            'startMs': q.startMs,
            'durationMs': q.durationMs
        })

    # 转换数据动画
    for s in suggestion.stats:
        config['stats'].append({
            'prefix': s.prefix,
            'number': s.number,
            'unit': s.unit,
            'label': s.label,
            'startMs': s.startMs,
            'durationMs': s.durationMs
        })

    # 转换要点列表
    for bp in suggestion.bulletPoints:
        config['bulletPoints'].append({
            'title': bp.title,
            'points': bp.points,
            'startMs': bp.startMs,
            'durationMs': bp.durationMs
        })

    # 转换社交媒体条
    for sb in suggestion.socialBars:
        config['socialBars'].append({
            'platform': sb.platform,
            'label': sb.label,
            'handle': sb.handle,
            'startMs': sb.startMs,
            'durationMs': sb.durationMs
        })

    return config


def format_suggestions_for_review(suggestion: EffectsSuggestion) -> str:
    """
    将建议格式化为可读的审核格式

    Returns:
        Markdown 格式的建议列表
    """
    lines = []
    lines.append(f"## 视觉特效建议\n")
    lines.append(f"**主题**: {suggestion.theme}\n")

    # 人物条
    if suggestion.speaker:
        lines.append("### 1. 人物条 (Lower Third)")
        lines.append(f"- **姓名**: {suggestion.speaker.name}")
        lines.append(f"- **职位**: {suggestion.speaker.role}")
        lines.append(f"- **公司**: {suggestion.speaker.company}")
        lines.append(f"- **出现时间**: {suggestion.speaker.startMs}ms")
        lines.append("")

    # 章节标题
    if suggestion.chapters:
        lines.append("### 2. 章节标题 (Chapter Titles)")
        for i, ch in enumerate(suggestion.chapters, 1):
            lines.append(f"**{i}. {ch.number} {ch.title}**")
            if ch.subtitle:
                lines.append(f"   副标题: {ch.subtitle}")
            lines.append(f"   时间: {ch.startMs}ms")
        lines.append("")

    # 花字
    if suggestion.fancyTexts:
        lines.append("### 3. 花字高亮 (Fancy Text)")
        for i, ft in enumerate(suggestion.fancyTexts, 1):
            lines.append(f"{i}. **{ft.text}** ({ft.style})")
            lines.append(f"   时间: {ft.startMs}ms - {ft.endMs}ms")
            if ft.reason:
                lines.append(f"   原因: {ft.reason}")
        lines.append("")

    # 名词卡片
    if suggestion.termCards:
        lines.append("### 4. 名词解释卡片 (Term Cards)")
        for i, tc in enumerate(suggestion.termCards, 1):
            lines.append(f"{i}. **{tc.chinese}** ({tc.english})")
            lines.append(f"   {tc.description}")
            lines.append(f"   时间: {tc.firstAppearanceMs}ms")
        lines.append("")

    # 金句
    if suggestion.quotes:
        lines.append("### 5. 金句卡片 (Quote Callouts)")
        for i, q in enumerate(suggestion.quotes, 1):
            lines.append(f'{i}. "{q.text}"')
            if q.author:
                lines.append(f"   — {q.author}")
            lines.append(f"   时间: {q.startMs}ms")
            if q.reason:
                lines.append(f"   原因: {q.reason}")
        lines.append("")

    # 数据动画
    if suggestion.stats:
        lines.append("### 6. 数据动画 (Animated Stats)")
        for i, s in enumerate(suggestion.stats, 1):
            lines.append(f"{i}. {s.prefix}{s.number}{s.unit}")
            if s.label:
                lines.append(f"   {s.label}")
            lines.append(f"   时间: {s.startMs}ms")
        lines.append("")

    # 要点列表
    if suggestion.bulletPoints:
        lines.append("### 7. 要点列表 (Bullet Points)")
        for i, bp in enumerate(suggestion.bulletPoints, 1):
            lines.append(f"{i}. **{bp.title}**")
            for point in bp.points:
                lines.append(f"   - {point}")
            lines.append(f"   时间: {bp.startMs}ms")
        lines.append("")

    # 社交媒体条
    if suggestion.socialBars:
        lines.append("### 8. 社交媒体条 (Social Bar)")
        for i, sb in enumerate(suggestion.socialBars, 1):
            lines.append(f"{i}. **{sb.platform}**: {sb.handle}")
            lines.append(f"   标签: {sb.label}")
            lines.append(f"   时间: {sb.startMs}ms，时长: {sb.durationMs}ms")
        lines.append("")

    return '\n'.join(lines)


# For Claude to use when analyzing content
ANALYSIS_PROMPT = """
请分析以下访谈字幕内容，并建议适合的视觉特效组件。

## 可用组件类型

1. **人物条 (lower_third)**: 显示嘉宾姓名、职位、公司
   - 通常在视频开头出现

2. **章节标题 (chapter_title)**: 话题切换时的大标题
   - 当话题明显转换时使用

3. **花字 (fancy_text)**: 用短语概括当前观点
   - style: emphasis(强调)、term(术语)、number(数字)
   - ⚠️ 重要规范：
     - 必须是短语形式，概括说话人当时的观点（如"AI发展是平滑曲线"）
     - 不能只是单词（如"人工智能"）
     - 不能与名词卡片的内容重复
     - 位置在字幕上方区域，不遮挡人脸

4. **名词卡片 (term_card)**: 解释专业术语
   - 用于解释专业名词的定义和含义
   - 与花字互补：花字概括观点，名词卡片解释术语

5. **金句卡片 (quote_callout)**: 突出精彩观点
   - 用于特别有洞察力或可引用的完整句子

6. **数据动画 (animated_stats)**: 展示统计数字
   - 当提到具体数字、百分比时使用

7. **要点列表 (bullet_points)**: 总结核心观点
   - 当内容可以概括为几个要点时使用

8. **社交媒体条 (social_bar)**: 关注引导
   - platform: twitter/weibo/youtube
   - 通常在视频结尾出现，时长建议 8-10 秒

## 字幕内容

{subtitle_content}

## 输出格式

请以 JSON 格式输出建议，包含以下字段:
- theme: 推荐主题 (notion/cyberpunk/apple/aurora)
- speaker: 人物条信息
- chapters: 章节标题列表
- fancyTexts: 花字列表（短语观点，非单词）
- termCards: 名词卡片列表（术语解释）
- quotes: 金句列表
- stats: 数据动画列表
- bulletPoints: 要点列表
- socialBars: 社交媒体条列表

每个组件都需要包含 startMs (开始时间毫秒) 字段。
"""


if __name__ == '__main__':
    # Test parsing
    import sys
    if len(sys.argv) > 1:
        srt_path = sys.argv[1]
        subtitles = parse_srt(srt_path)
        print(f"Parsed {len(subtitles)} subtitles")
        for s in subtitles[:5]:
            print(f"  [{s['start_ms']}ms] {s['text'][:50]}...")
