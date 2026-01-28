# Video Wrapper

为访谈视频添加综艺风格视觉特效的 Claude Skill。AI 分析字幕内容生成建议，用户审批后自动渲染，支持 4 种视觉主题。

## 功能特性

- 8 种视觉组件：花字、人物条、章节标题、名词卡片、金句、数据动画、要点列表、社交条
- 4 种主题风格：Notion 知识风、Cyberpunk 科技风、Apple 极简风、Aurora 渐变风
- 智能工作流：分析字幕 → 生成建议 → 用户审批 → 自动渲染
- 双渲染引擎：Playwright 浏览器渲染（推荐） + PIL 纯 Python 备选

## 快速开始

### 1. 安装 Skill

**方式一：npx 一键安装（推荐）**

```bash
npx skills add https://github.com/op7418/Video-Wrapper-Skills
```

**方式二：手动安装**

```bash
cd ~/.claude/skills/video-wrapper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. 使用 Claude Skill

```bash
# 在 Claude Code 中直接调用
/video-wrapper video.mp4 subtitles.srt
```

Claude 会分析字幕，生成特效建议供审批，确认后自动渲染视频。

### 3. 命令行使用

```bash
# 有现成配置时
python src/video_processor.py video.mp4 subs.srt config.json output.mp4

# 指定渲染器
python src/video_processor.py video.mp4 subs.srt config.json -r browser
python src/video_processor.py video.mp4 subs.srt config.json -r pil
```

## 主题系统

| 主题 | 风格 | 适用场景 |
|------|------|----------|
| `notion` | 温暖知识风 | 教育、知识分享 |
| `cyberpunk` | 霓虹未来感 | 科技、前沿话题 |
| `apple` | 极简优雅 | 商务、专业访谈 |
| `aurora` | 渐变流光 | 创意、艺术内容 |

## 组件列表

| 组件 | 类型 | 用途 |
|------|------|------|
| 人物条 | lower_third | 显示嘉宾姓名、职位、公司 |
| 章节标题 | chapter_title | 话题切换时的标题 |
| 花字 | fancy_text | 短语概括当前观点 |
| 名词卡片 | term_card | 解释专业术语 |
| 金句卡片 | quote_callout | 突出精彩言论 |
| 数据动画 | animated_stats | 展示数字数据 |
| 要点列表 | bullet_points | 总结核心要点 |
| 社交条 | social_bar | 社交媒体关注引导 |

## 配置文件格式

```json
{
  "theme": "notion",
  "lowerThirds": [
    {
      "name": "Dario Amodei",
      "role": "CEO",
      "company": "Anthropic",
      "startMs": 1000,
      "durationMs": 5000
    }
  ],
  "chapterTitles": [
    {
      "number": "Part 1",
      "title": "指数增长的本质",
      "subtitle": "The Nature of Exponential Growth",
      "startMs": 0,
      "durationMs": 4000
    }
  ],
  "keyPhrases": [
    {
      "text": "AI发展是平滑曲线",
      "style": "emphasis",
      "startMs": 2630,
      "endMs": 5500
    }
  ],
  "termDefinitions": [
    {
      "chinese": "摩尔定律",
      "english": "Moore's Law",
      "description": "集成电路晶体管数量每18-24个月翻一番",
      "firstAppearanceMs": 37550,
      "displayDurationSeconds": 6
    }
  ],
  "quotes": [
    {
      "text": "AI 的发展是一个非常平滑的指数曲线",
      "author": "— Dario Amodei",
      "startMs": 30000,
      "durationMs": 5000
    }
  ],
  "stats": [
    {
      "prefix": "增长率 ",
      "number": 240,
      "unit": "%",
      "label": "计算能力年增长",
      "startMs": 45000,
      "durationMs": 4000
    }
  ],
  "bulletPoints": [
    {
      "title": "核心观点",
      "points": [
        "AI 发展是平滑的指数曲线",
        "类似摩尔定律的智能增长",
        "没有突然的奇点时刻"
      ],
      "startMs": 50000,
      "durationMs": 6000
    }
  ],
  "socialBars": [
    {
      "platform": "twitter",
      "label": "关注",
      "handle": "@anthropic",
      "startMs": 52000,
      "durationMs": 8000
    }
  ]
}
```

## 文件结构

```
~/.claude/skills/video-wrapper/
├── SKILL.md                    # Skill 定义
├── README.md                   # 使用文档
├── ARCHITECTURE.md             # 架构文档
├── requirements.txt            # Python 依赖
├── src/
│   ├── video_processor.py      # 主处理脚本
│   ├── browser_renderer.py     # Playwright 渲染器
│   ├── content_analyzer.py     # 内容分析器
│   ├── fancy_text.py           # PIL 花字（备用）
│   ├── term_card.py            # PIL 卡片（备用）
│   └── animations.py           # 动画函数
├── templates/
│   ├── fancy-text.html         # 花字模板
│   ├── term-card.html          # 名词卡片模板
│   ├── lower-third.html        # 人物条模板
│   ├── chapter-title.html      # 章节标题模板
│   ├── quote-callout.html      # 金句卡片模板
│   ├── animated-stats.html     # 数据动画模板
│   ├── bullet-points.html      # 要点列表模板
│   ├── social-bar.html         # 社交条模板
│   └── video-config.json.template
└── static/
    ├── css/
    │   ├── effects.css         # 基础效果
    │   ├── theme-notion.css
    │   ├── theme-cyberpunk.css
    │   ├── theme-apple.css
    │   └── theme-aurora.css
    └── js/
        └── anime.min.js        # Anime.js 动画库
```

## 常见问题

### Q: Playwright 安装失败？

```bash
# 确保 Python 版本 >= 3.8
pip install playwright
playwright install chromium

# macOS 可能需要
xattr -r -d com.apple.quarantine ~/.cache/ms-playwright
```

### Q: 处理速度慢？

- 使用 PIL 渲染器：`-r pil`（效果略简单但更快）
- 降低视频分辨率
- 分段处理长视频

### Q: 内存不足？

- 处理时关闭其他应用
- 分段处理长视频
- 使用更低的分辨率

### Q: 字体显示异常？

确保系统有中文字体。macOS 自带 PingFang，Linux 需要安装：
```bash
sudo apt-get install fonts-noto-cjk
```

## 技术实现

- **视觉渲染**: HTML + CSS + Anime.js (通过 Playwright 截图)
- **视频合成**: MoviePy
- **动画引擎**: Anime.js Spring 物理动画
- **备用渲染**: Python PIL

详细架构请参考 [ARCHITECTURE.md](./ARCHITECTURE.md)。

## 许可证

MIT License
