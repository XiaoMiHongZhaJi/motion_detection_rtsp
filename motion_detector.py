import asyncio
import os
import threading
import cv2
import time
import logging
from datetime import datetime
from telegram.ext import Application
import yaml

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
with open(THIS_DIR + "/config.yaml", encoding='utf-8') as file:
    config = yaml.safe_load(file)

# 设置 Bot Token
TOKEN = config.get("bot_token")
NOTICE_CHAT_ID = config.get("notice_chat_id")

# 设置代理
PROXY = config.get("proxy_url")

# RTSP视频流地址
rtsp_url = config.get("rtsp_url")

# 运动检测的阈值，默认值为 25000
motion_threshold = config.get("motion_threshold")

# 检测到运动时录制时长（秒）
video_duration = config.get("video_duration")

# 显示的日志条数
log_count = config.get("log_count")

# 录像文件格式
fourcc_type = config.get("fourcc_type")

# 区块最小触发变化量
min_contour_area = config.get("min_contour_area")

# 录像文件夹
cap_folder = config.get("cap_folder")

# 用于存储上一帧图像
previous_frame = None
frame_sequence = 0

# 状态管理
is_running = False  # 是否正在运行检测
is_recording = False  # 是否正在录制

# 创建一个固定大小的日志缓存
log_buffer = []

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 发送通知
def send_file_to_telegram(file_path, caption):
    try:
        application = Application.builder().token(TOKEN).proxy(PROXY).build()
        bot = application.bot
        asyncio.run(bot.send_document(chat_id=NOTICE_CHAT_ID, document=file_path, caption=caption))
        log_message(f"发送通知成功：{file_path}")
    except Exception as e:
        log_message(f"发送通知失败：{e}", "error")


# 发送通知（同步）
def send_file_to_telegram_sync(file_path, caption):
    try:
        application = Application.builder().token(TOKEN).proxy(PROXY).build()
        bot = application.bot

        # 获取现有的事件循环
        loop = asyncio.get_event_loop()

        # 如果当前事件循环已关闭，则创建一个新的事件循环
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # 使用现有的事件循环运行异步任务
        loop.run_until_complete(bot.send_document(chat_id=NOTICE_CHAT_ID, document=file_path, caption=caption))
        log_message(f"发送通知成功：{file_path}")
    except Exception as e:
        log_message(f"发送通知失败：{e}", "error")


def log_message(message, level="info"):
    """自定义日志记录方法"""
    current_time = datetime.now().strftime('%m-%d %H:%M:%S')
    log_buffer.append(f"{current_time} {message}")
    if len(log_buffer) > log_count * 2:
        log_buffer.pop(log_count)
    if level == "error":
        logging.error(message)
    else:
        logging.info(message)


def record_video(filename, cap, frame):
    """录像功能"""
    global is_recording

    is_recording = True
    # 获取第一帧并保存为 JPG
    cv2.imwrite(filename + ".jpg", frame)
    # 视频格式判断
    if fourcc_type in ["avc1", "H264", "X264", "mp4v", "vp09"]:
        filename = filename + ".mp4"
    elif fourcc_type in ["DIVX", "XVID", "MJPG"]:
        filename = filename + ".avi"
    elif fourcc_type in ["VP80", "VP90"]:
        filename = filename + ".mkv"
    else:
        log_message(f"录像出错，fourcc_type 格式错误：{fourcc_type}", "error")
        is_recording = False
        return None

    # 创建视频写入对象
    try:
        fourcc = cv2.VideoWriter.fourcc(*fourcc_type)
        frame_height, frame_width = frame.shape[:2]
        fps = cap.get(cv2.CAP_PROP_FPS)
        video_writer = cv2.VideoWriter(filename, fourcc, fps, (frame_width, frame_height))
    except Exception as e:
        log_message(f"录像出错，当前fourcc_type[{fourcc_type}]出错，请尝试其他格式。报错信息：{e}", "error")
        is_recording = False
        return None

    if not video_writer.isOpened():
        log_message(f"录像出错，当前fourcc_type[{fourcc_type}]出错，请尝试其他格式", "error")
        is_recording = False
        return None

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

    if not os.path.exists(filename):
        log_message(f"录像出错，当前fourcc_type[{fourcc_type}]出错，请尝试其他格式", "error")
        is_recording = False
        return None

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
        if area > min_contour_area:
            total_area += area

    previous_frame = gray
    return total_area, len(contours)


def start_detection():
    """启动运动检测"""
    global is_running, previous_frame, frame_sequence
    is_running = True
    log_message(f"准备启动运动检测：{rtsp_url}")

    while is_running:
        frame_sequence = 0  # 重置帧序列
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            log_message(f"视频流打开失败：{rtsp_url}", "error")
            time.sleep(10)
            return

        log_message(f"已启动运动检测")

        # 创建录像文件夹
        if not os.path.exists(cap_folder):
            os.makedirs(cap_folder)

        while is_running:
            ret, frame = cap.read()
            if not ret:
                break
            frame_sequence += 1

            if frame_sequence % 20 == 0:
                total_area, contours_count = detect_motion(frame)

                fmt_total_area = f"{total_area:,}"
                fmt_contours_count = f"{contours_count:,}"
                fmt_motion_threshold = f"{motion_threshold:,}"

                if total_area > motion_threshold:
                    # 录像
                    log_message(f"检测到运动，变化区块：{fmt_contours_count}，变化量：{fmt_total_area} > {fmt_motion_threshold}")
                    log_message(f"开始录像...")

                    current_time = datetime.now().strftime('%m/%d %H:%M:%S')
                    filename = f"static/cap/{datetime.now().strftime('%m-%d_%H-%M-%S')}_{int(contours_count)}_{int(total_area)}"

                    filename = record_video(filename, cap, frame)
                    if filename is not None:
                        log_message(f"录像完成，文件保存为: {filename}，持续检测中...")
                        # 通知
                        caption = f"{current_time} 检测到运动\n变化区块：{fmt_contours_count}，变化量：{fmt_total_area} > {fmt_motion_threshold}"
                        # 异步操作（如果报错，则改为同步）
                        threading.Thread(target=send_file_to_telegram, args=(filename, caption)).start()
                        # 同步操作
                        # send_file_to_telegram_sync(filename, caption)
                    previous_frame = None
                elif total_area > 1:
                    log_message(f"变化区块：{fmt_contours_count}，变化量：{fmt_total_area} < {fmt_motion_threshold}")

        cap.release()
        log_message(f"cap已释放：{rtsp_url}")


def get_motion_status():
    return is_running, is_recording, motion_threshold


def set_motion_threshold(motion_threshold_new):
    global motion_threshold
    motion_threshold = motion_threshold_new


def stop_detection():
    """停止运动检测"""
    global is_running
    is_running = False
    log_message(f"运动检测已停止：{rtsp_url}")


if __name__ == '__main__':
    start_detection()