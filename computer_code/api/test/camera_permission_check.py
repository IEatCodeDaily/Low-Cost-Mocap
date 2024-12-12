import cv2
import os
import fcntl
import v4l2
import sys

def check_device_permissions(device_path):
    try:
        stats = os.stat(device_path)
        print(f"\n{device_path} permissions:")
        print(f"Owner: {stats.st_uid}")
        print(f"Group: {stats.st_gid}")
        print(f"Mode: {oct(stats.st_mode)}")
        print(f"Current user ID: {os.getuid()}")
        print(f"Current group IDs: {os.getgroups()}")
        return os.access(device_path, os.R_OK | os.W_OK)
    except OSError as e:
        print(f"Error checking {device_path}: {e}")
        return False

def try_v4l2_open(device_path):
    try:
        fd = os.open(device_path, os.O_RDWR | os.O_NONBLOCK)
        cp = v4l2.v4l2_capability()
        fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCAP, cp)
        print(f"\nV4L2 device info for {device_path}:")
        print(f"Driver: {cp.driver.decode()}")
        print(f"Card: {cp.card.decode()}")
        print(f"Bus info: {cp.bus_info.decode()}")
        print(f"Capabilities: {hex(cp.capabilities)}")
        os.close(fd)
        return True
    except Exception as e:
        print(f"Error opening {device_path} with V4L2: {e}")
        return False

def try_opencv_open(device_path):
    try:
        # Try opening with direct device path
        cap = cv2.VideoCapture(device_path)
        if cap.isOpened():
            print(f"\nOpenCV successfully opened {device_path}")
            print(f"Backend: {cap.getBackendName()}")
            ret, frame = cap.read()
            if ret:
                print("Successfully read a frame")
            else:
                print("Could not read a frame")
            cap.release()
            return True
        else:
            print(f"\nOpenCV failed to open {device_path}")
            return False
    except Exception as e:
        print(f"Error with OpenCV for {device_path}: {e}")
        return False

def main():
    # Check OpenCV version and build info
    print(f"OpenCV version: {cv2.__version__}")
    print(f"OpenCV build info:\n{cv2.getBuildInformation()}")

    # Check each video device
    for i in range(10):
        device_path = f"/dev/video{i}"
        if os.path.exists(device_path):
            print(f"\n{'='*50}")
            print(f"Testing device: {device_path}")
            print(f"{'='*50}")
            
            if check_device_permissions(device_path):
                print("Permission check: PASSED")
                try_v4l2_open(device_path)
                try_opencv_open(device_path)
            else:
                print("Permission check: FAILED")

if __name__ == "__main__":
    main()