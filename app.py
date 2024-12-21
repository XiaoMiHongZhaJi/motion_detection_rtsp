from flask import Flask, render_template, request, jsonify
import threading
import os
from motion_detector import start_detection, stop_detection, get_motion_status, log_buffer, set_motion_threshold

app = Flask(__name__)


@app.route('/')
def index():
    """首页，显示控制面板"""
    video_files = get_video_files()  # 获取 cap 目录下的视频文件
    is_running, is_recording, motion_threshold = get_motion_status()
    return render_template('index.html', threshold=motion_threshold, video_files=video_files[-6:],
                           video_count=len(video_files))


@app.route('/get_all_videos', methods=['GET'])
def get_all_videos():
    """返回所有的视频文件"""
    video_files = get_video_files()  # 获取 cap 目录下的视频文件
    return jsonify({"videos": video_files})


@app.route('/start', methods=['POST'])
def start():
    """启动监控检测"""
    is_running, is_recording, recording_video_file = get_motion_status()
    if not is_running:
        threading.Thread(target=start_detection, daemon=True).start()  # 启动后台线程
        return jsonify({"status": "started"}), 200
    return jsonify({"status": "already started"}), 200


@app.route('/stop', methods=['POST'])
def stop():
    """暂停监控检测"""
    is_running, is_recording, recording_video_file = get_motion_status()
    if is_running:
        stop_detection()
        return jsonify({"status": "stopped"}), 200
    return jsonify({"status": "already stopped"}), 200


@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    """设置运动检测的灵敏度（阈值）"""
    try:
        motion_threshold = int(request.form['threshold'])
        set_motion_threshold(motion_threshold)
        return jsonify({"status": "threshold updated", "threshold": motion_threshold}), 200
    except ValueError:
        return jsonify({"error": "Invalid threshold value"}), 400


@app.route('/get_status', methods=['GET'])
def get_status():
    """获取当前状态"""
    is_running, is_recording, recording_video_file = get_motion_status()
    if is_running:
        if is_recording:
            status = {"status": "录像中", "light": "yellow"}
        else:
            status = {"status": "检测中", "light": "green"}
    else:
        status = {"status": "已停止", "light": "red"}

    return jsonify(status)


@app.route('/get_logs', methods=['GET'])
def get_logs():
    """获取最新的日志内容"""
    return jsonify({"logs": log_buffer[-20:]})  # 返回最近100条日志


def get_video_files():
    """获取 cap 目录下的视频文件和缩略图"""
    video_files = []
    cap_folder = 'static/cap'

    # 获取 cap 目录下所有 mp4 文件
    if not os.path.exists(cap_folder):
        os.makedirs(cap_folder)

    listdir = os.listdir(cap_folder)
    for filename in listdir:
        if filename.endswith('.mp4'):
            video_file = {
                'filename': filename,
                'thumbnail': ''
            }
            jpg_filename = filename.replace('.mp4', '.jpg')
            if jpg_filename in listdir:
                video_file['thumbnail'] = jpg_filename
            video_files.append(video_file)
    video_files.sort(key=lambda x: x['filename'], reverse=True)
    return video_files


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)
