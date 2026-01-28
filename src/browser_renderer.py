"""
Browser-based renderer using Playwright
Renders HTML/CSS/Anime.js effects to image sequences for video composition
"""
import os
import json
import tempfile
from pathlib import Path


class BrowserRenderer:
    """
    Playwright-based renderer for HTML/CSS/Anime.js effects.
    Captures frames at specified times for video composition.
    """

    def __init__(self, width=1920, height=1080, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self._browser = None
        self._playwright = None

        # Get paths relative to this file
        self.base_dir = Path(__file__).parent.parent
        self.templates_dir = self.base_dir / 'templates'
        self.static_dir = self.base_dir / 'static'

    def _ensure_browser(self):
        """Lazily initialize browser"""
        if self._browser is None:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
        return self._browser

    def close(self):
        """Clean up browser resources"""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def render_fancy_text_frames(self, config, output_dir=None):
        """
        Render fancy text effect to image sequence.

        Args:
            config: {
                'text': str,
                'style': 'emphasis' | 'term' | 'number',
                'position': {'x': int, 'y': int},
                'startMs': int,
                'endMs': int
            }
            output_dir: Directory to save frames (uses temp dir if None)

        Returns:
            List of frame file paths
        """
        browser = self._ensure_browser()
        page = browser.new_page(viewport={'width': self.width, 'height': self.height})

        # Load template
        template_path = self.templates_dir / 'fancy-text.html'
        page.goto(f'file://{template_path}')

        # Calculate timing
        duration_ms = config['endMs'] - config['startMs']
        total_frames = int(duration_ms / 1000 * self.fps)

        # Prepare config for JavaScript
        js_config = {
            'text': config['text'],
            'style': config.get('style', 'emphasis'),
            'theme': config.get('theme', 'notion'),
            'position': config.get('position', {'x': self.width // 2, 'y': 300}),
            'durationMs': duration_ms
        }

        # Initialize animation with config
        page.evaluate(f'initAnimation({json.dumps(js_config)})')

        # Create output directory
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='fancy_text_')
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Capture frames
        frame_paths = []
        for frame_idx in range(total_frames):
            time_ms = frame_idx / self.fps * 1000

            # Seek animation to current time
            page.evaluate(f'seekTo({time_ms})')

            # Capture frame with transparent background
            frame_path = output_dir / f'frame_{frame_idx:05d}.png'
            page.screenshot(path=str(frame_path), omit_background=True)
            frame_paths.append(str(frame_path))

        page.close()
        return frame_paths

    def render_term_card_frames(self, config, output_dir=None):
        """
        Render term definition card to image sequence.

        Args:
            config: {
                'chinese': str,
                'english': str,
                'description': str,
                'firstAppearanceMs': int,
                'displayDurationSeconds': float
            }
            output_dir: Directory to save frames (uses temp dir if None)

        Returns:
            List of frame file paths
        """
        browser = self._ensure_browser()
        page = browser.new_page(viewport={'width': self.width, 'height': self.height})

        # Load template
        template_path = self.templates_dir / 'term-card.html'
        page.goto(f'file://{template_path}')

        # Calculate timing
        duration_seconds = config.get('displayDurationSeconds', 6)
        duration_ms = int(duration_seconds * 1000)
        total_frames = int(duration_seconds * self.fps)

        # Default position: top-right corner
        position = config.get('position', {
            'x': self.width - 50 - 400,  # 50px margin, 400px card width
            'y': 50
        })

        # Prepare config for JavaScript
        js_config = {
            'chinese': config['chinese'],
            'english': config['english'],
            'description': config['description'],
            'theme': config.get('theme', 'notion'),
            'position': position,
            'durationMs': duration_ms
        }

        # Initialize animation with config
        page.evaluate(f'initAnimation({json.dumps(js_config)})')

        # Create output directory
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='term_card_')
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Capture frames
        frame_paths = []
        for frame_idx in range(total_frames):
            time_ms = frame_idx / self.fps * 1000

            # Seek animation to current time
            page.evaluate(f'seekTo({time_ms})')

            # Capture frame with transparent background
            frame_path = output_dir / f'frame_{frame_idx:05d}.png'
            page.screenshot(path=str(frame_path), omit_background=True)
            frame_paths.append(str(frame_path))

        page.close()
        return frame_paths

    def generate_fancy_text_clip(self, keyword, index):
        """
        Generate MoviePy clip from fancy text effect.

        Args:
            keyword: {text, startMs, endMs, style}
            index: Effect index for positioning

        Returns:
            MoviePy ImageSequenceClip
        """
        from moviepy import ImageSequenceClip
        import shutil

        # Calculate position (alternating left/right)
        x_offset = (index % 2) * 400
        y_offset = (index // 2) * 100
        position = {
            'x': self.width // 2 - 300 + x_offset,
            'y': 300 + y_offset
        }

        config = {
            'text': keyword['text'],
            'style': keyword.get('style', 'emphasis'),
            'position': position,
            'startMs': keyword['startMs'],
            'endMs': keyword['endMs']
        }

        # Render frames
        temp_dir = tempfile.mkdtemp(prefix='fancy_text_clip_')
        try:
            frame_paths = self.render_fancy_text_frames(config, temp_dir)

            # Create clip from image sequence
            clip = ImageSequenceClip(frame_paths, fps=self.fps)

            # Set start time
            start_time = keyword['startMs'] / 1000.0
            clip = clip.with_start(start_time)

            return clip
        finally:
            # Clean up temp directory after clip is created
            # Note: MoviePy reads frames lazily, so we need to keep files
            # The caller is responsible for cleanup after video export
            pass

    def generate_term_card_clip(self, term):
        """
        Generate MoviePy clip from term card effect.

        Args:
            term: {chinese, english, description, firstAppearanceMs, displayDurationSeconds}

        Returns:
            MoviePy ImageSequenceClip
        """
        from moviepy import ImageSequenceClip

        config = {
            'chinese': term['chinese'],
            'english': term['english'],
            'description': term['description'],
            'displayDurationSeconds': term.get('displayDurationSeconds', 6)
        }

        # Render frames
        temp_dir = tempfile.mkdtemp(prefix='term_card_clip_')
        frame_paths = self.render_term_card_frames(config, temp_dir)

        # Create clip from image sequence
        clip = ImageSequenceClip(frame_paths, fps=self.fps)

        # Set start time
        start_time = term['firstAppearanceMs'] / 1000.0
        clip = clip.with_start(start_time)

        return clip

    def _render_generic_template(self, template_name, config, output_dir=None):
        """
        Generic renderer for any template.

        Args:
            template_name: Name of the template file (without .html)
            config: Configuration dict including 'durationMs' or 'displayDurationSeconds'
            output_dir: Directory to save frames

        Returns:
            List of frame file paths
        """
        browser = self._ensure_browser()
        page = browser.new_page(viewport={'width': self.width, 'height': self.height})

        # Load template
        template_path = self.templates_dir / f'{template_name}.html'
        page.goto(f'file://{template_path}')

        # Calculate timing
        if 'durationMs' in config:
            duration_ms = config['durationMs']
        elif 'displayDurationSeconds' in config:
            duration_ms = int(config['displayDurationSeconds'] * 1000)
        else:
            duration_ms = 5000  # default 5 seconds

        total_frames = int(duration_ms / 1000 * self.fps)

        # Initialize animation with config
        page.evaluate(f'initAnimation({json.dumps(config)})')

        # Create output directory
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix=f'{template_name}_')
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Capture frames
        frame_paths = []
        for frame_idx in range(total_frames):
            time_ms = frame_idx / self.fps * 1000
            page.evaluate(f'seekTo({time_ms})')
            frame_path = output_dir / f'frame_{frame_idx:05d}.png'
            page.screenshot(path=str(frame_path), omit_background=True)
            frame_paths.append(str(frame_path))

        page.close()
        return frame_paths

    def render_lower_third_frames(self, config, output_dir=None):
        """
        Render lower third (人物条) to image sequence.

        Args:
            config: {
                'name': str,
                'role': str,
                'company': str,
                'theme': str,
                'durationMs': int
            }
        """
        return self._render_generic_template('lower-third', config, output_dir)

    def render_chapter_title_frames(self, config, output_dir=None):
        """
        Render chapter title (章节标题) to image sequence.

        Args:
            config: {
                'number': str (optional, e.g., "Part 1"),
                'title': str,
                'subtitle': str (optional),
                'theme': str,
                'durationMs': int
            }
        """
        return self._render_generic_template('chapter-title', config, output_dir)

    def render_quote_callout_frames(self, config, output_dir=None):
        """
        Render quote callout (金句卡片) to image sequence.

        Args:
            config: {
                'text': str,
                'author': str (optional),
                'theme': str,
                'position': {'x': int, 'y': int},
                'durationMs': int
            }
        """
        # Set default position if not provided
        if 'position' not in config:
            config['position'] = {'x': self.width // 2, 'y': self.height // 2}
        return self._render_generic_template('quote-callout', config, output_dir)

    def render_animated_stats_frames(self, config, output_dir=None):
        """
        Render animated stats (数据动画) to image sequence.

        Args:
            config: {
                'prefix': str (optional),
                'number': int,
                'unit': str (e.g., '%', 'x'),
                'label': str (optional),
                'theme': str,
                'position': {'x': int, 'y': int},
                'durationMs': int
            }
        """
        if 'position' not in config:
            config['position'] = {'x': self.width // 2, 'y': self.height // 2}
        return self._render_generic_template('animated-stats', config, output_dir)

    def render_bullet_points_frames(self, config, output_dir=None):
        """
        Render bullet points (要点列表) to image sequence.

        Args:
            config: {
                'title': str (optional),
                'points': list[str],
                'theme': str,
                'position': {'x': int, 'y': int},
                'durationMs': int
            }
        """
        if 'position' not in config:
            config['position'] = {'x': 100, 'y': 300}
        return self._render_generic_template('bullet-points', config, output_dir)

    def render_social_bar_frames(self, config, output_dir=None):
        """
        Render social media bar (社交媒体条) to image sequence.

        Args:
            config: {
                'platform': 'twitter' | 'weibo' | 'youtube',
                'label': str,
                'handle': str,
                'theme': str,
                'position': {'x': int, 'y': int},
                'durationMs': int
            }
        """
        if 'position' not in config:
            config['position'] = {'x': self.width - 320, 'y': self.height - 130}
        return self._render_generic_template('social-bar', config, output_dir)


def check_playwright_installed():
    """Check if Playwright is installed and chromium is available"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception as e:
        print(f"Playwright check failed: {e}")
        print("To install Playwright and Chromium, run:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return False


if __name__ == '__main__':
    # Test the renderer
    print("Testing BrowserRenderer...")

    if not check_playwright_installed():
        print("Playwright not available, skipping test")
        exit(1)

    with BrowserRenderer(width=1920, height=1080, fps=30) as renderer:
        # Test fancy text
        test_config = {
            'text': '测试花字',
            'style': 'emphasis',
            'startMs': 0,
            'endMs': 2000
        }

        print("Rendering test fancy text frames...")
        frames = renderer.render_fancy_text_frames(test_config)
        print(f"Generated {len(frames)} frames")
        print(f"First frame: {frames[0]}")

        # Test term card
        test_term = {
            'chinese': '人工智能',
            'english': 'Artificial Intelligence',
            'description': '人工智能是计算机科学的一个分支。',
            'firstAppearanceMs': 0,
            'displayDurationSeconds': 3
        }

        print("\nRendering test term card frames...")
        frames = renderer.render_term_card_frames(test_term)
        print(f"Generated {len(frames)} frames")
        print(f"First frame: {frames[0]}")

    print("\nTest complete!")
