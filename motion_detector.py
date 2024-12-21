import asyncio
import os
import threading
import cv2
import time
import logging
from datetime import datetime

from telegram.ext import Application

# 设置 Bot Token
TOKEN = 'Your Bot Token'
NOTICE_CHAT_ID = -1001642336803

# 设置代理
PROXY = None
# PROXY = "http://127.0.0.1:7890"

# RTSP视频流地址
rtsp_url = 'rtsp://192.168.10.38:8080/h264_ulaw.sdp'

# 运动检测的阈值，默认值为25000
motion_threshold = 2500

# 视频录制时长
video_duration = 10  # 录制30秒

# 用于存储上一帧图像
previous_frame = None
frame_sequence = 0

# 状态管理
is_running = False  # 是否正在运行检测
is_recording = False  # 是否正在录制

# 创建一个固定大小的日志缓存，最多保存 100 条日志
log_buffer = []

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 发送通知
def send_file_to_telegram(file_path, caption):
    application = Application.builder().token(TOKEN).proxy(PROXY).build()
    bot = application.bot
    asyncio.run(bot.send_document(chat_id=NOTICE_CHAT_ID, document=file_path, caption=caption))


def log_message(message):
    """自定义日志记录方法，保持最多50条日志"""
    current_time = datetime.now().strftime('%m-%d %H:%M:%S')
    log_buffer.append(f"{current_time} {message}")
    if len(log_buffer) > 100:
        log_buffer.pop(50)  # 如果超过50条，删除旧的
    logging.info(message)  # 记录到标准日志系统


def record_video(filename, cap, frame):
    """录像功能"""
    global is_recording

    is_recording = True
    # 获取第一帧并保存为 JPG
    cv2.imwrite(filename.replace(".mp4", ".jpg"), frame)

    # 创建视频写入对象
    fourcc = cv2.VideoWriter.fourcc(*'avc1')
    # 如果报错 换成下方的
    # fourcc = cv2.VideoWriter.fourcc(*'x264')
    # fourcc = cv2.VideoWriter.fourcc(*'mp4v')
    # fourcc = cv2.VideoWriter.fourcc(*'mjpg')
    frame_height, frame_width = frame.shape[:2]
    fps = cap.get(cv2.CAP_PROP_FPS)
    video_writer = cv2.VideoWriter(filename, fourcc, fps, (frame_width, frame_height))

    # 启动录像并写入帧
    start_time = time.time()
    while time.time() - start_time < video_duration:
        ret, frame = cap.read()
        if not ret:
            break
        video_writer.write(frame)  # 写入视频帧

    # 停止录像
    video_writer.release()
    is_recording = False
    return True


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

        cap_folder = 'static/cap'

        # 获取 cap 目录下所有 mp4 文件
        if not os.path.exists(cap_folder):
            os.makedirs(cap_folder)

        while is_running:
            ret, frame = cap.read()
            if not ret:
                break
            frame_sequence += 1

            if frame_sequence % 20 == 0:
                total_area, contours_count = detect_motion(frame)

                if total_area > motion_threshold:
                    # 录像
                    log_message(f"检测到运动，变化区块：{contours_count}，变化量：{total_area} > {motion_threshold}")
                    log_message(f"开始录像...")

                    current_time = datetime.now().strftime('%m-%d_%H-%M-%S')
                    filename = f"static/cap/{current_time}_{int(contours_count)}_{int(total_area)}.mp4"

                    record_video(filename, cap, frame)
                    log_message(f"录像完成，文件保存为: {filename}，持续检测中...")

                    # 通知
                    caption = f"{current_time} 检测到运动，变化区块：{contours_count}，变化量：{total_area} > {motion_threshold}"
                    threading.Thread(target=send_file_to_telegram, args=(filename, caption,)).start()
                    # asyncio.run(send_file_to_group_2(filename))
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


if __name__ == '__main__':
    start_detection()