#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腿部露出检测可视化界面 — CustomTkinter 现代化版本
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, END, DISABLED, NORMAL
import threading
import os
import sys
from pathlib import Path
import json
import subprocess
import sys
import datetime
import time
import glob

import site
_torch_lib = os.path.join(site.getsitepackages()[0] if hasattr(site, 'getsitepackages') else os.path.join(sys.prefix, 'Lib', 'site-packages'), 'torch', 'lib')
if os.path.exists(_torch_lib):
    os.environ.setdefault("PATH", "")
    os.environ["PATH"] = _torch_lib + os.pathsep + os.environ["PATH"]

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
CORNER = 8

COLOR_PRIMARY = "#3B82F6"
COLOR_SUCCESS = "#22C55E"
COLOR_DANGER = "#EF4444"
COLOR_TEXT_MUTED = "#9CA3AF"
COLOR_CARD_BG = "#1F2937"


class LegDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("腿部露出检测工具")
        self.root.geometry("900x620")
        self.root.minsize(800, 500)

        self.video_path = ctk.StringVar()
        self.output_dir = ctk.StringVar(value="output/leg_output")
        self.model_path = ctk.StringVar(value="models/yolov8m-pose.pt")
        self.min_duration = ctk.DoubleVar(value=2.0)
        self.sample_interval = ctk.IntVar(value=3)
        self.conf_thres = ctk.DoubleVar(value=0.5)
        self.device = ctk.StringVar(value="cuda")
        self.is_processing = False
        self.stop_requested = False
        self.generate_compilation = ctk.BooleanVar(value=False)
        self.time_reference = self._load_time_reference()
        
        self.auto_watch_dir = ctk.StringVar()
        self.auto_trigger_hour = ctk.IntVar(value=22)
        self.auto_trigger_minute = ctk.IntVar(value=0)
        self.auto_enabled = False
        self.auto_timer_id = None
        self.auto_processed_files = set()
        self._load_auto_config()

        self._create_widgets()
        self._setup_layout()
        self._detect_and_set_best_device()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._auto_start_default()

    def _detect_and_set_best_device(self):
        try:
            import torch
            cuda_available = False
            mps_available = False
            try:
                cuda_available = torch.cuda.is_available()
            except Exception:
                cuda_available = False
            try:
                mps_available = torch.backends.mps.is_available()
            except Exception:
                mps_available = False
            if cuda_available:
                try:
                    gpu_name = torch.cuda.get_device_name(0)
                    self.device.set("cuda")
                    print(f"✅ 检测到 CUDA GPU: {gpu_name}")
                except Exception:
                    self.device.set("cpu")
            elif mps_available:
                self.device.set("mps")
                print(f"✅ 检测到 Apple Silicon MPS")
            else:
                self.device.set("cpu")
        except ImportError:
            self.device.set("cpu")

    def _format_time(self, seconds):
        total_seconds = int(seconds)
        if total_seconds <= 60:
            return f"{total_seconds}s"
        elif total_seconds <= 3600:
            minutes = total_seconds // 60
            secs = total_seconds % 60
            if secs == 0:
                return f"{minutes}m"
            return f"{minutes}m{secs}s"
        else:
            total_minutes = total_seconds // 60
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes == 0:
                return f"{hours}h"
            return f"{hours}h{minutes}m"

    def _load_time_reference(self):
        ref_path = Path("config/time_reference.json")
        if ref_path.exists():
            try:
                with open(ref_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"cuda": {"speed": 30.0, "count": 0, "total_time": 0.0}, "mps": {"speed": 22.0, "count": 0, "total_time": 0.0}, "cpu": {"speed": 1.5, "count": 0, "total_time": 0.0}}

    def _save_time_reference(self):
        ref_path = Path("config/time_reference.json")
        try:
            with open(ref_path, "w", encoding="utf-8") as f:
                json.dump(self.time_reference, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"⚠️ 保存时间参考数据失败: {str(e)}")

    def _update_time_reference(self, device, actual_time, sample_count):
        if device in self.time_reference and actual_time > 0:
            actual_speed = sample_count / actual_time
            ref = self.time_reference[device]
            ref["count"] += 1
            ref["total_time"] += actual_time
            ref["speed"] = ref["speed"] * 0.7 + actual_speed * 0.3
            self._save_time_reference()

    def _load_auto_config(self):
        config_path = Path("config/auto_detect_config.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.auto_watch_dir.set(config.get("watch_dir", ""))
                    self.auto_trigger_hour.set(config.get("trigger_hour", 22))
                    self.auto_trigger_minute.set(config.get("trigger_minute", 0))
                    self.auto_processed_files = set(config.get("processed_files", []))
            except Exception:
                pass

    def _save_auto_config(self):
        config_path = Path("config/auto_detect_config.json")
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {"watch_dir": self.auto_watch_dir.get(), "trigger_hour": self.auto_trigger_hour.get(), "trigger_minute": self.auto_trigger_minute.get(), "processed_files": list(self.auto_processed_files)}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"⚠️ 保存自动检测配置失败: {str(e)}")

    def _create_widgets(self):
        self.top_card = ctk.CTkFrame(self.root, corner_radius=CORNER)
        self.video_path_label = ctk.CTkLabel(self.top_card, text="视频路径", font=("Microsoft YaHei", 12))
        self.video_entry = ctk.CTkEntry(self.top_card, textvariable=self.video_path, placeholder_text="选择或输入视频文件路径...", corner_radius=CORNER)
        self.browse_video_btn = ctk.CTkButton(self.top_card, text="浏览", command=self._browse_video, width=80, corner_radius=CORNER, font=("Microsoft YaHei", 11))
        self.start_btn = ctk.CTkButton(self.top_card, text="开始检测", command=self._start_detection, width=140, corner_radius=CORNER, font=("Microsoft YaHei", 12, "bold"), fg_color=COLOR_SUCCESS, hover_color="#16A34A")
        self.stop_btn = ctk.CTkButton(self.top_card, text="停止检测", command=self._stop_detection, width=140, corner_radius=CORNER, font=("Microsoft YaHei", 12), state=DISABLED, fg_color=COLOR_DANGER, hover_color="#DC2626")
        self.open_output_btn = ctk.CTkButton(self.top_card, text="打开输出目录", command=self._open_output_dir, width=140, corner_radius=CORNER, font=("Microsoft YaHei", 12))
        # ... (see full file for complete widget setup)
        print("Widgets created")

    def _setup_layout(self):
        self.top_card.pack(fill="x", padx=15, pady=(15, 6))
        print("Layout setup")

    def _update_conf_label(self, value):
        pass

    def _clear_log(self):
        pass

    def _update_estimate(self, *args):
        pass

    def _browse_video(self):
        file_path = filedialog.askopenfilename(title="选择视频文件", filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.ts *.wmv")])
        if file_path:
            self.video_path.set(file_path)

    def _browse_output(self):
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir.set(dir_path)

    def _toggle_auto_card(self):
        pass

    def _browse_auto_dir(self):
        pass

    def _start_auto_detect(self):
        pass

    def _stop_auto_detect(self):
        pass

    def _auto_start_default(self):
        pass

    def _schedule_auto_check(self):
        pass

    def _auto_check_timer(self):
        pass

    def _check_and_process_latest_video(self):
        pass

    def _open_output_dir(self):
        output_dir = self.output_dir.get()
        target_dir = Path(output_dir)
        if target_dir.exists():
            os.startfile(str(target_dir))

    def _log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def _init_log_file(self, output_dir):
        pass

    def _start_detection(self):
        if self.is_processing:
            return
        video_path = self.video_path.get()
        if not video_path or not os.path.exists(video_path):
            return
        self.is_processing = True
        self.stop_requested = False
        thread = threading.Thread(target=self._process_video)
        thread.daemon = True
        thread.start()

    def _stop_detection(self):
        if not self.is_processing:
            return
        self.stop_requested = True

    def _process_video(self):
        try:
            video_path = self.video_path.get()
            output_dir = self.output_dir.get()
            model = self.model_path.get()
            min_dur = self.min_duration.get()
            interval = self.sample_interval.get()
            conf = self.conf_thres.get()
            device = self.device.get()
            self._log(f"开始处理: {Path(video_path).name}")
            self._run_detection(video_path, output_dir, model, min_dur, interval, conf, device)
        except Exception as e:
            self._log(f"❌ 错误: {str(e)}")
        finally:
            self.is_processing = False

    def _detect_device(self):
        return self.device.get()

    def _run_detection(self, video_path, output_dir, model, min_dur, interval, conf, device):
        print(f"Running detection on {video_path}")

    def _on_finish(self):
        pass

    def _write_merge_scripts(self, output_dir):
        pass

    def _cleanup_gpu_resources(self):
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _on_close(self):
        if self.is_processing:
            self.stop_requested = True
        self._cleanup_gpu_resources()
        self.root.destroy()


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    app = LegDetectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
