# 架构文档

## 系统概览

访谈视频处理器基于分离的渲染后端架构，支持两种视觉效果生成方式：
- **Browser Backend**: HTML/CSS/Anime.js + Playwright 浏览器自动化（推荐）
- **PIL Backend**: Python PIL 纯 Python 实现（备选方案）

典型的数据流如下：
```
视频文件 + 字幕文件
    ↓
内容分析器（提取建议）
    ↓
用户审批配置
    ↓
渲染引擎（生成帧序列）
    ├→ Browser: HTML → Playwright → 截图
    └→ PIL: Python → PIL 绘制
    ↓
视频合成器（MoviePy）
    ↓
输出视频
```

## 核心模块

### 1. video_processor.py
主入口和协调器，负责：
- 命令行参数解析
- 配置文件加载验证
- 渲染器选择（自动或手动指定）
- 多种组件类型的分发处理
- 视频合成和导出

关键函数：
- `process_video()`: 主处理流程
- `_generate_clips_browser()`: 使用浏览器渲染器生成图层
- `_generate_clips_pil()`: 使用 PIL 渲染器生成图层

### 2. browser_renderer.py
Playwright 浏览器自动化渲染器，负责：
- Playwright 浏览器实例管理
- HTML 模板加载与渲染
- 动画状态管理（通过 seek 控制当前帧）
- 截图捕获和图像输出

关键类和方法：
- `BrowserRenderer`: 主类，生命周期管理
- `render_fancy_text_frames()`: 花字渲染
- `render_term_card_frames()`: 名词卡片渲染
- `render_lower_third_frames()`: 人物条渲染
- 以及其他 8 个组件的渲染方法

工作原理：
```
加载 HTML 模板
    ↓
注入配置参数（JSON）
    ↓
调用 JavaScript initAnimation()
    ↓
循环：
  - 计算当前帧时间
  - 调用 JavaScript seek(t)
  - Playwright 截图
  - 保存为 PNG
```

### 3. content_analyzer.py
内容分析引擎，负责：
- 从字幕文件提取信息
- 分析内容，识别：
  - 嘉宾信息（人物条）
  - 话题切换点（章节标题）
  - 关键观点（花字短语）
  - 专业术语（名词卡片）
  - 精彩言论（金句卡片）
  - 数字数据（数据动画）
  - 核心要点（要点列表）
  - 社交媒体信息（社交条）

包含多个 Dataclass 定义建议类型：
- `LowerThirdSuggestion`
- `ChapterTitleSuggestion`
- `FancyTextSuggestion`
- `TermCardSuggestion`
- `QuoteCalloutSuggestion`
- `AnimatedStatsSuggestion`
- `BulletPointsSuggestion`
- `SocialBarSuggestion`

### 4. fancy_text.py（PIL 备选方案）
纯 Python PIL 实现的花字生成器：
- PIL 文字渲染与描边
- 阴影效果实现
- 旋转和缩放变换
- Spring 动画应用

### 5. term_card.py（PIL 备选方案）
纯 Python PIL 实现的名词卡片生成器：
- 圆角矩形绘制
- 渐变边框（Pillow 模拟）
- 文字布局和自动换行
- 动画效果（滑入、淡出）

### 6. animations.py
动画工具函数库（用于 PIL 后端）：
- `spring()`: Spring 物理引擎实现
  - 参数：frame, fps, from_value, to_value, damping, stiffness
  - 模拟 Remotion 风格弹性动画
- `interpolate()`: 线性插值函数
  - 支持任意输入/输出范围映射
  - 支持超出范围处理（clamp/extend/wrap）

## 模板系统

9 个 HTML 模板位于 `templates/` 目录，每个对应一种组件：

| 模板 | 组件类型 | 用途 |
|------|---------|------|
| fancy-text.html | 花字 | 概括观点短语 |
| term-card.html | 名词卡片 | 解释专业术语 |
| lower-third.html | 人物条 | 显示嘉宾信息 |
| chapter-title.html | 章节标题 | 话题切换标题 |
| quote-callout.html | 金句卡片 | 突出精彩言论 |
| animated-stats.html | 数据动画 | 展示数字数据 |
| bullet-points.html | 要点列表 | 总结核心要点 |
| social-bar.html | 社交条 | 社交媒体引导 |
| video-config.json.template | 配置模板 | JSON 配置示例 |

### 模板特点：
- 独立的 HTML 结构，可单独测试
- JavaScript `initAnimation(config)` 函数接收配置
- `seek(timeMs)` 方法用于帧控制（Playwright 调用）
- CSS 变量支持主题切换
- Anime.js 动画库支持

## 主题系统

CSS 主题在 `static/css/` 目录：

| 主题 | 文件 | 特点 | 场景 |
|------|------|------|------|
| notion | theme-notion.css | 温暖知识风，柔和渐变 | 教育、知识分享 |
| cyberpunk | theme-cyberpunk.css | 霓虹未来感，鲜艳对比 | 科技、前沿话题 |
| apple | theme-apple.css | 极简优雅，中性色系 | 商务、专业访谈 |
| aurora | theme-aurora.css | 渐变流光，炫彩效果 | 创意、艺术内容 |

每个主题通过 CSS 变量定义：
```css
:root[data-theme="notion"] {
  --primary-color: #f5b041;
  --secondary-color: #3498db;
  --accent-color: #e74c3c;
  /* ... */
}
```

模板通过 `data-theme` 属性激活主题。

## 动画引擎

### Anime.js 集成
- 用于浏览器后端的帧动画
- 支持 Spring 物理、缓动曲线等高级效果
- 通过 `seek()` 方法实现帧级控制

### Spring 动画原理
```python
x(t) = to_value - (to_value - from_value) * exp(-damping*t) * cos(stiffness*t)
```
通过调整 `damping` 和 `stiffness` 参数实现不同的弹性效果。

## 配置文件格式

JSON 配置包含以下顶级字段：

```json
{
  "theme": "notion",           # 选择主题
  "lowerThirds": [...],        # 人物条数组
  "chapterTitles": [...],      # 章节标题数组
  "keyPhrases": [...],         # 花字数组
  "termDefinitions": [...],    # 名词卡片数组
  "quotes": [...],             # 金句卡片数组
  "stats": [...],              # 数据动画数组
  "bulletPoints": [...],       # 要点列表数组
  "socialBars": [...]          # 社交条数组
}
```

## 数据流详解

### 1. 配置阶段
```
用户提供视频 + 字幕
    ↓
ContentAnalyzer.analyze_subtitle() 读取 .srt
    ↓
返回 8 种类型的建议对象列表
    ↓
用户编辑或确认建议
    ↓
生成或修改 config.json
```

### 2. 渲染阶段（Browser 后端）
```
video_processor 加载配置
    ↓
对每个组件：
  - 确定时间范围
  - 创建 BrowserRenderer 实例
  - 加载对应 HTML 模板
  - 通过 JavaScript 注入配置
  - 循环渲染帧：
    * 计算当前时间
    * 调用 seek(timeMs)
    * Playwright 截图
    * 保存 PNG 序列
  - 使用 MoviePy ImageClip 构建视频层
    ↓
合并所有层（原视频 + 效果层）
    ↓
导出最终视频
```

### 3. 渲染阶段（PIL 后端）
```
video_processor 加载配置
    ↓
对每个组件：
  - 确定时间范围和帧数
  - 循环渲染帧：
    * 调用 fancy_text.py / term_card.py
    * 应用 animations.py 动画函数
    * 使用 PIL 绘制到内存
    * 保存 PNG 序列
  - 使用 MoviePy ImageClip 构建视频层
    ↓
合并所有层（原视频 + 效果层）
    ↓
导出最终视频
```

## 文件依赖关系

```
video_processor.py （主）
├── browser_renderer.py
│   ├── templates/*.html
│   └── static/css/*.css
│       ├── effects.css
│       └── theme-*.css
├── fancy_text.py （PIL 备选）
│   └── animations.py
├── term_card.py （PIL 备选）
│   └── animations.py
├── content_analyzer.py
├── moviepy
│   ├── VideoFileClip
│   ├── CompositeVideoClip
│   └── ImageClip
└── 配置文件
    └── config.json
```

## 扩展指南

### 添加新组件

#### 1. 创建 HTML 模板
在 `templates/` 目录创建 `your-component.html`，包含：
```html
<script>
function initAnimation(config) {
  // 初始化：使用 config 参数设置 DOM 元素
  // 返回 totalMs：动画总时长
}

function seek(timeMs) {
  // 关键帧：根据 timeMs 设置动画状态
  // 由 Playwright 调用
}
</script>
```

#### 2. 添加渲染方法
在 `BrowserRenderer` 类中添加：
```python
def render_your_component_frames(self, config, output_dir=None):
    # 类似 render_fancy_text_frames 的实现
    pass
```

#### 3. 在 video_processor.py 中注册
在 `_generate_clips_browser()` 中添加分支处理新组件。

#### 4. 更新 content_analyzer.py
添加对应的 Suggestion dataclass。

#### 5. 添加配置验证
在配置加载时验证新组件的必需字段。

### 添加新主题

#### 1. 创建 CSS 文件
在 `static/css/` 目录创建 `theme-yourtheme.css`：
```css
:root[data-theme="yourtheme"] {
  --primary-color: #...;
  --secondary-color: #...;
  --accent-color: #...;
  --bg-color: #...;
  /* ... */
}
```

#### 2. 在模板中引用
```html
<link rel="stylesheet" href="../static/css/theme-yourtheme.css">
```

#### 3. 更新文档
在 SKILL.md 中列出新主题。

## 性能考虑

### Browser 后端性能
- 优点：高质量输出，支持复杂 CSS/动画
- 缺点：需要 Chromium，较慢（但可控）
- 优化：
  - 使用 `--headless` 模式
  - 预热浏览器实例
  - 批量渲染多组件时复用实例

### PIL 后端性能
- 优点：快速，无额外依赖
- 缺点：效果有限，不支持复杂动画
- 优化：
  - 预计算变换矩阵
  - 使用 NumPy 加速计算

## 依赖分析

### 核心依赖
- `moviepy>=1.0.3`: 视频合成
- `pillow>=10.0.0`: 图像处理（两个后端都需要）
- `numpy>=1.24.0`: 数值计算
- `pysrt>=1.1.2`: SRT 字幕解析
- `playwright>=1.40.0`: 浏览器自动化（可选）

### 依赖大小
- 总计：约 100-150MB（包括 Playwright + Chromium）
- 仅 PIL 后端：约 50-80MB

## 故障排除

### Playwright/Chromium 问题
```bash
# 手动安装
pip install playwright
playwright install chromium

# 验证
playwright codegen --browser chromium
```

### MoviePy 依赖问题
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg

# 验证
moviepy-script --version
```

### 内存问题
- 长视频：分段处理或降低分辨率
- 多组件：批量处理时控制并发

## 测试策略

### 单元测试
- 动画函数：spring(), interpolate()
- 配置解析和验证
- 渲染器初始化

### 集成测试
- 完整工作流：输入 → 渲染 → 输出
- 两个后端对比（视觉一致性）
- 不同主题的渲染

### 性能测试
- 帧渲染速度
- 内存使用
- 长视频处理

