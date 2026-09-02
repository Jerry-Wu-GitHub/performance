"""
配置
"""

from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 静态资源目录
STATIC_DIR = BASE_DIR / "static"
HTML_DIR = STATIC_DIR / "html"
INDEX_PATH = HTML_DIR / "index.html"

# 服务监听配置
HOST = "0.0.0.0"
PORT = 7860

# 对需要耗时采集的数据的采样时长（单位：秒）
MEASUREMENT_INTERVAL: float = 1.0
