#!/usr/bin/env python3
"""腿部露出检测工具 GUI - 启动脚本"""
import sys
from pathlib import Path
_src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(_src_dir))
from leg_detector_gui import main
if __name__ == "__main__":
    main()
