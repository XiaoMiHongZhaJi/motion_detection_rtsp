import cv2

try:
    fourcc = cv2.VideoWriter.fourcc(*'avc1')  # 测试 avc1
    out = cv2.VideoWriter('test.mp4', fourcc, 30.0, (640, 480))
    if not out.isOpened():
        print("测试 avc1 失败")
    else:
        print("VideoWriter successfully initialized.")
        print("测试 avc1 成功")
except Exception as e:
    print(f"Error occurred: {e}")
    print("测试 avc1 失败")
print("-" * 20)

try:
    fourcc = cv2.VideoWriter.fourcc(*'H264')  # 测试 H264
    out = cv2.VideoWriter('test.mp4', fourcc, 30.0, (640, 480))
    if not out.isOpened():
        print("测试 H264 失败")
    else:
        print("VideoWriter successfully initialized.")
        print("测试 H264 成功")
except Exception as e:
    print(f"Error occurred: {e}")
    print("测试 H264 失败")
print("-" * 20)

try:
    fourcc = cv2.VideoWriter.fourcc(*'X264')  # 测试 X264
    out = cv2.VideoWriter('test.mp4', fourcc, 30.0, (640, 480))
    if not out.isOpened():
        print("测试 X264 失败")
    else:
        print("VideoWriter successfully initialized.")
        print("测试 X264 成功")
except Exception as e:
    print(f"Error occurred: {e}")
    print("测试 X264 失败")
print("-" * 20)

try:
    fourcc = cv2.VideoWriter.fourcc(*'mp4v')  # 测试 mp4v
    out = cv2.VideoWriter('test.mp4', fourcc, 30.0, (640, 480))
    if not out.isOpened():
        print("测试 mp4v 失败")
    else:
        print("VideoWriter successfully initialized.")
        print("测试 mp4v 成功")
except Exception as e:
    print(f"Error occurred: {e}")
    print("测试 mp4v 失败")
print("-" * 20)

try:
    fourcc = cv2.VideoWriter.fourcc(*'DIVX')  # 测试 DIVX
    out = cv2.VideoWriter('test.avi', fourcc, 30.0, (640, 480))
    if not out.isOpened():
        print("测试 DIVX 失败")
    else:
        print("VideoWriter successfully initialized.")
        print("测试 DIVX 成功")
except Exception as e:
    print(f"Error occurred: {e}")
    print("测试 DIVX 失败")
print("-" * 20)

try:
    fourcc = cv2.VideoWriter.fourcc(*'XVID')  # 测试 XVID
    out = cv2.VideoWriter('test.avi', fourcc, 30.0, (640, 480))
    if not out.isOpened():
        print("测试 XVID 失败")
    else:
        print("VideoWriter successfully initialized.")
        print("测试 XVID 成功")
except Exception as e:
    print(f"Error occurred: {e}")
    print("测试 XVID 失败")
print("-" * 20)

try:
    fourcc = cv2.VideoWriter.fourcc(*'MJPG')  # 测试 MJPG
    out = cv2.VideoWriter('test.avi', fourcc, 30.0, (640, 480))
    if not out.isOpened():
        print("测试 MJPG 失败")
    else:
        print("VideoWriter successfully initialized.")
        print("测试 MJPG 成功")
except Exception as e:
    print(f"Error occurred: {e}")
    print("测试 MJPG 失败")
print("-" * 20)

try:
    fourcc = cv2.VideoWriter.fourcc(*'VP80')  # 测试 VP80
    out = cv2.VideoWriter('test.mkv', fourcc, 30.0, (640, 480))
    if not out.isOpened():
        print("测试 VP80 失败")
    else:
        print("VideoWriter successfully initialized.")
        print("测试 VP80 成功")
except Exception as e:
    print(f"Error occurred: {e}")
    print("测试 VP80 失败")
print("-" * 20)

