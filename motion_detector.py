import cv2
import time
import subprocess
from datetime import datetime
import logging

# 创建一个固定大小的日志缓存，最多保存 100 条日志
log_buffer = []

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# RTSP视频流地址
rtsp_url = 'rtsp://192.168.10.38:8080/h264_ulaw.sdp'

# 运动检测的阈值，默认值为25000
motion_threshold = 2500

# 用于存储上一帧图像
previous_frame = None
frame_sequence = 0

# 状态管理
is_running = False  # 是否正在运行检测
is_recording = False  # 是否正在录制
recording_video_file = ""  # 当前正在录制的视频文件名


def log_message(message):
    """自定义日志记录方法，保持最多50条日志"""
    current_time = datetime.now().strftime('%m-%d %H:%M:%S')
    log_buffer.append(f"{current_time} {message}")
    if len(log_buffer) > 40:
        log_buffer.pop(20)  # 如果超过50条，删除最旧的一条
    logging.info(message)  # 记录到标准日志系统


def record_video(contours_count, total_area):
    """录像功能"""
    global is_recording, recording_video_file

    is_recording = True
    current_time = datetime.now().strftime('%m-%d_%H-%M-%S')
    filename = f"cap/{current_time}_{int(contours_count)}_{int(total_area)}"
    recording_video_file = filename  # 保存当前录像文件名

    # 使用 FFmpeg 录制视频
    command = [
        'ffmpeg',
        '-i', rtsp_url,
        '-c:v', "copy",
        '-t', '00:00:30',
        filename + ".mp4"
    ]
    process = subprocess.Popen(command, stderr=subprocess.DEVNULL)
    # process = subprocess.Popen(command)

    process.wait()
    is_recording = False
    recording_video_file = ""
    return filename


def detect_motion(frame):
    """检测运动"""
    global previous_frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if previous_frame is None:
        previous_frame = gray
        return 0, 0

    frame_diff = cv2.absdiff(previous_frame, gray)
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    total_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:
            total_area += area

    previous_frame = gray
    return total_area, len(contours)


def start_detection():
    """启动监控检测"""
    global is_running, previous_frame, frame_sequence
    is_running = True

    while is_running:
        frame_sequence = 0  # 重置帧序列
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            log_message(f"视频流打开失败：{rtsp_url}")
            time.sleep(10)
            return

        log_message(f"启动运动检测：{rtsp_url}")

        while is_running:
            ret, frame = cap.read()
            if not ret:
                break
            frame_sequence += 1

            if frame_sequence % 20 == 0:
                total_area, contours_count = detect_motion(frame)

                if total_area > motion_threshold:
                    log_message(f"检测到运动，变化区块：{contours_count}，变化量：{total_area} > {motion_threshold}")
                    log_message(f"开始录像...")
                    filename = record_video(contours_count, total_area)

                    # 获取第一帧并保存为 JPG
                    cv2.imwrite(filename + ".jpg", frame)  # 保存第一帧为 JPG
                    log_message(f"录像完成，持续检测中...")
                    previous_frame = None
                elif total_area > 1:
                    log_message(f"变化区块：{contours_count}，变化量：{total_area} < {motion_threshold}")

        cap.release()
        log_message(f"检测出错，重新启动...")
        time.sleep(2)


def get_motion_status():
    return is_running, is_recording, motion_threshold


def set_motion_threshold(motion_threshold_new):
    global motion_threshold
    motion_threshold = motion_threshold_new


def stop_detection():
    """暂停监控检测"""
    global is_running
    is_running = False
