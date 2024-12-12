import cv2
import time
import threading
import numpy as np
from datetime import datetime

class CameraTest:
    def __init__(self, device_id):
        self.device_id = device_id
        self.frames = 0
        self.failed_reads = 0
        self.running = True
        self.current_fps = 0
        self.last_frame_time = None
        self.frame_times = []

    def run_test(self, width, height, target_fps, duration=5):
        cap = cv2.VideoCapture(self.device_id)
        if not cap.isOpened():
            return {
                'success': False,
                'error': 'Failed to open camera'
            }

        # Set properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, target_fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Verify settings
        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = cap.get(cv2.CAP_PROP_FPS)

        start_time = time.time()
        self.frames = 0
        self.failed_reads = 0
        self.frame_times = []

        while (time.time() - start_time) < duration:
            ret, frame = cap.read()
            current_time = time.time()
            
            if ret:
                self.frames += 1
                if self.last_frame_time is not None:
                    self.frame_times.append(current_time - self.last_frame_time)
                self.last_frame_time = current_time
            else:
                self.failed_reads += 1

        cap.release()
        test_duration = time.time() - start_time

        # Calculate statistics
        achieved_fps = self.frames / test_duration if test_duration > 0 else 0
        frame_time_std = np.std(self.frame_times) * 1000 if self.frame_times else 0
        
        return {
            'success': True,
            'resolution': f"{actual_width}x{actual_height}",
            'target_fps': target_fps,
            'actual_fps': achieved_fps,
            'frames': self.frames,
            'failed_reads': self.failed_reads,
            'frame_time_std_ms': frame_time_std
        }

def test_configuration(camera_ids, width, height, fps, duration=5):
    print(f"\nTesting {len(camera_ids)} cameras at {width}x{height} @ {fps}fps...")
    
    cameras = []
    threads = []
    results = []

    for device_id in camera_ids:
        camera = CameraTest(device_id)
        cameras.append(camera)
        
        # Run test directly (no threading to avoid interference)
        result = camera.run_test(width, height, fps, duration)
        results.append(result)
        
    return results

def run_comprehensive_test(camera_ids):
    # Test configurations
    configs = [
        # (width, height, fps)
        (320, 240, 30),
        (320, 240, 60),
        (320, 240, 120),
        (640, 480, 30),
        (640, 480, 60),
        (800, 600, 30),
    ]
    
    results = {}
    
    for width, height, fps in configs:
        key = f"{width}x{height}@{fps}"
        results[key] = test_configuration(camera_ids, width, height, fps)
        time.sleep(1)  # Pause between tests
        
    # Print summary
    print("\n=== Test Results ===")
    print("\nConfiguration | Average FPS | Success Rate | Frame Time Std")
    print("-" * 65)
    
    for config, test_results in results.items():
        successful_cameras = len([r for r in test_results if r['success'] and r['actual_fps'] > 1])
        avg_fps = np.mean([r['actual_fps'] for r in test_results if r['success']]) if successful_cameras else 0
        avg_std = np.mean([r['frame_time_std_ms'] for r in test_results if r['success']]) if successful_cameras else 0
        
        print(f"{config:13} | {avg_fps:10.1f} | {successful_cameras:2d}/{len(camera_ids)}        | {avg_std:8.1f}ms")
    
    # Find best configuration
    best_config = None
    best_fps = 0
    for config, test_results in results.items():
        successful_cameras = len([r for r in test_results if r['success'] and r['actual_fps'] > 1])
        if successful_cameras == len(camera_ids):  # All cameras working
            avg_fps = np.mean([r['actual_fps'] for r in test_results if r['success']])
            if avg_fps > best_fps:
                best_fps = avg_fps
                best_config = config
    
    if best_config:
        print(f"\nRecommended configuration: {best_config}")
        print(f"Average FPS: {best_fps:.1f}")
    else:
        print("\nNo stable configuration found for all cameras")

if __name__ == "__main__":
    camera_ids = [0, 1, 2, 3]
    run_comprehensive_test(camera_ids)