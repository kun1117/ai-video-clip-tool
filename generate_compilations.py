#!/usr/bin/env python3
"""批量生成腿部片段合集视频"""
import subprocess
import sys
import json
from pathlib import Path
LEG_OUTPUT_DIR = Path("output/leg_output")
def _run(cmd, capture=True):
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=False, creationflags=creationflags)
            stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
            stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
            return result.returncode, stdout, stderr
        else:
            result = subprocess.run(cmd, creationflags=creationflags)
            return result.returncode, "", ""
    except Exception as e:
        return -1, "", str(e)
def format_duration(seconds):
    total = int(seconds)
    if total <= 60:
        return f"{total}秒"
    elif total <= 3600:
        return f"{total // 60}分{total % 60}秒"
    else:
        return f"{total // 3600}小时{(total % 3600) // 60}分"
def get_video_duration(video_path):
    rc, out, _ = _run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(video_path)])
    if rc != 0:
        return 0.0
    try:
        data = json.loads(out)
        return float(data.get("format", {}).get("duration", 0))
    except Exception:
        return 0.0
def merge_with_concat_protocol(clip_files, output_path):
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        concat_file = Path(f.name)
        for clip in clip_files:
            f.write(f"file '{str(clip.resolve())}'\n")
    rc, _, _ = _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_path)])
    concat_file.unlink(missing_ok=True)
    return rc
def merge_with_filter_complex(clip_files, output_path):
    num_files = len(clip_files)
    inputs = []
    for clip in clip_files:
        inputs.extend(["-i", str(clip)])
    filter_parts = []
    for i in range(num_files):
        filter_parts.append(f"[{i}:v][{i}:a]")
    filter_str = f"{''.join(filter_parts)}concat=n={num_files}:v=1:a=1[outv][outa]"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filter_str, "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p", str(output_path)]
    rc, _, err = _run(cmd)
    return rc, err
def process_directory(dir_path):
    clip_files = sorted(dir_path.glob("leg_clip_*.mp4"))
    if not clip_files:
        return False
    existing = list(dir_path.glob("合集_*.mp4"))
    if existing:
        print(f"  ⏩ 跳过（已存在合成: {existing[0].name}）")
        return False
    dir_name = dir_path.name
    print(f"\n📁 {dir_name}")
    print(f"   找到 {len(clip_files)} 个片段")
    output_path = dir_path / f"合集_{dir_name}.mp4"
    print(f"   尝试快速合并...")
    rc = merge_with_concat_protocol(clip_files, output_path)
    if rc == 0:
        duration = get_video_duration(output_path)
        print(f"   ✅ 合集已生成（快速模式）: {output_path.name}（{format_duration(duration)}）")
        return True
    output_path.unlink(missing_ok=True)
    print(f"   尝试重新编码合并...")
    rc2, _ = merge_with_filter_complex(clip_files, output_path)
    if rc2 == 0:
        duration = get_video_duration(output_path)
        print(f"   ✅ 合集已生成: {output_path.name}（{format_duration(duration)}）")
        return True
    output_path.unlink(missing_ok=True)
    print(f"   ❌ 合并失败（rc={rc2}）")
    return False
def main():
    print("=" * 60)
    print("  腿部片段合集批量生成工具")
    print("=" * 60)
    if not LEG_OUTPUT_DIR.exists():
        print(f"❌ 目录不存在: {LEG_OUTPUT_DIR}")
        sys.exit(1)
    subdirs = sorted([d for d in LEG_OUTPUT_DIR.iterdir() if d.is_dir()])
    if not subdirs:
        print(f"⚠️  {LEG_OUTPUT_DIR} 下没有子目录")
        return
    print(f"\n找到 {len(subdirs)} 个子目录\n")
    success_count = 0
    skip_count = 0
    for subdir in subdirs:
        if process_directory(subdir):
            success_count += 1
        elif list(subdir.glob("合集_*.mp4")):
            skip_count += 1
    print("\n" + "=" * 60)
    print(f"处理完成! 生成 {success_count} 个合集, {skip_count} 个已存在")
    print("=" * 60)
if __name__ == "__main__":
    main()
