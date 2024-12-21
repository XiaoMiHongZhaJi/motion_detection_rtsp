import logging
from flask import Flask, render_template, request, jsonify
import threading
import os
from motion_detector import start_detection, stop_detection, get_motion_status, log_buffer, set_motion_threshold

app = Flask(__name__)
# 录像文件
cap_folder = 'static/cap/'


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
    """启动运动检测"""
    is_running, is_recording, recording_video_file = get_motion_status()
    if not is_running:
        threading.Thread(target=start_detection, daemon=True).start()  # 启动后台线程
        return jsonify({"status": "已启动运动检测"}), 200
    return jsonify({"status": "已启动，请勿重复操作"}), 200


@app.route('/stop', methods=['POST'])
def stop():
    """暂停运动检测"""
    is_running, is_recording, recording_video_file = get_motion_status()
    if is_running:
        stop_detection()
        return jsonify({"status": "已停止运动检测"}), 200
    return jsonify({"status": "已停止，请勿重复操作"}), 200


@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    """设置运动检测的灵敏度（阈值）"""
    threshold = request.form['threshold']
    try:
        motion_threshold = int(threshold)
        set_motion_threshold(motion_threshold)
        return jsonify({"status": "threshold updated", "threshold": f"{motion_threshold:,}"}), 200
    except ValueError:
        return jsonify({"error": f"错误的值：{threshold}"}), 400


@app.route('/delete_all_videos', methods=['POST'])
def delete_all_videos():
    """删除所有视频文件"""
    video_files = get_video_files()
    for video in video_files:
        try:
            os.remove(os.path.join(cap_folder, video['filename']))
            os.remove(os.path.join(cap_folder, video['thumbnail']))
        except Exception as e:
            logging.error(e)
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "已删除所有视频"}), 200


@app.route('/get_status_and_logs', methods=['GET'])
def get_status_and_logs():
    result = {"logs": log_buffer[-50:]}
    """获取当前状态"""
    is_running, is_recording, recording_video_file = get_motion_status()
    if is_running:
        if is_recording:
            result["status"] = "录像中"
        else:
            result["status"] = "检测中"
    else:
        result["status"] = "已停止"

    return jsonify(result)


def get_video_files():
    """获取 cap 目录下的视频文件和缩略图"""
    video_files = []

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
