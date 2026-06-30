# 腿部露出检测指南

## 检测逻辑

基于 YOLOv8-Pose 关键点分析：
- 膝盖（索引 13-14）
- 脚踝（索引 15-16）

当膝盖或脚踝关键点在画面中可见且置信度超过阈值时，判定为腿部露出。

## 推荐参数

| 参数 | 推荐值 |
|------|--------|
| 模型 | yolov8m-pose.pt |
| 置信度 | 0.4-0.6 |
| 最小时长 | 2-5秒 |
| 采样间隔 | 1-3秒 |

## 命令行使用

```bash
python leg_detector.py video.mp4 --model models/yolov8l-pose.pt --min-duration 2.0 --sample-interval 1 --conf-thres 0.4
```

## 局限

- 基于关键点可见性，不能区分"被衣物遮挡"和"不在画面中"
- 对低分辨率、高遮挡视频效果较差
