#!/usr/bin/env python
"""dance-video-toolkit 启动脚本"""
import sys
from pathlib import Path
_src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(_src_dir))
from dance_toolkit import main
if __name__ == "__main__":
    main()
