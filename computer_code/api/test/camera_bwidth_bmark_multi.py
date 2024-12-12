import cv2
import time
import threading
import numpy as np
from datetime import datetime

class CameraThread:
    def __init__(self, device_id, width, height, fps):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.frames = 0
        self.failed_reads = 0
        self.running = True
        self.frame_times = []
        self.last_frame_time = None

    def capture_frames(self, duration):
        cap = cv2.VideoCapture(self.device_id)
        if not cap.isOpened():
            return
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
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

    def get_stats(self, duration):
        fps = self.frames / duration if duration > 0 else 0
        frame_time_std = np.std(self.frame_times) * 1000 if self.frame_times else 0
        return {
            'device_id': self.device_id,
            'fps': fps,
            'frames': self.frames,
            'failed_reads': self.failed_reads,
            'frame_time_std_ms': frame_time_std
        }

def test_configuration(camera_ids, width, height, fps, duration=5):
    print(f"\nTesting {len(camera_ids)} cameras simultaneously:")
    print(f"Resolution: {width}x{height}")
    print(f"Target FPS: {fps}")
    
    cameras = []
    threads = []
    
    # Start all cameras simultaneously
    for device_id in camera_ids:
        camera = CameraThread(device_id, width, height, fps)
        thread = threading.Thread(target=camera.capture_frames, args=(duration,))
        cameras.append(camera)
        threads.append(thread)
        thread.start()
        time.sleep(0.5)  # Small delay between camera starts
    
    # Monitor progress
    start_time = time.time()
    while time.time() - start_time < duration:
        time.sleep(1)
        print(".", end="", flush=True)
    
    # Stop all cameras
    for camera in cameras:
        camera.running = False
    
    for thread in threads:
        thread.join()
    
    # Collect results
    results = []
    for camera in cameras:
        stats = camera.get_stats(duration)
        results.append(stats)
        
    return results

def run_comprehensive_test(camera_ids):
    configs = [
        (320, 240, 30),
        (320, 240, 60),
        (320, 240, 90),
        (320, 240, 120),
        (640, 480, 30),
        (640, 480, 60),
        (800, 600, 30),
    ]
    
    results = {}
    
    for width, height, fps in configs:
        key = f"{width}x{height}@{fps}"
        results[key] = test_configuration(camera_ids, width, height, fps, duration=7)
        time.sleep(2)  # Pause between tests
    
    # Print summary
    print("\n\n=== Test Results (Simultaneous Operation) ===")
    print("\nConfiguration | Avg FPS | Working Cameras | Frame Time Std | Failed Reads")
    print("-" * 75)
    
    for config, test_results in results.items():
        working_cameras = len([r for r in test_results if r['fps'] > 1])
        avg_fps = np.mean([r['fps'] for r in test_results if r['fps'] > 1]) if working_cameras else 0
        avg_std = np.mean([r['frame_time_std_ms'] for r in test_results if r['fps'] > 1]) if working_cameras else 0
        total_fails = sum(r['failed_reads'] for r in test_results)
        
        print(f"{config:13} | {avg_fps:7.1f} | {working_cameras:2d}/{len(camera_ids)}           | "
              f"{avg_std:8.1f}ms    | {total_fails:5d}")
        
        # Print per-camera details
        print("  Per-camera FPS:", end=" ")
        for r in test_results:
            print(f"Cam{r['device_id']}: {r['fps']:4.1f}", end=" ")
        print()
    
    # Find best stable configuration
    best_config = None
    best_fps = 0
    for config, test_results in results.items():
        working_cameras = len([r for r in test_results if r['fps'] > 1])
        if working_cameras == len(camera_ids):
            avg_fps = np.mean([r['fps'] for r in test_results])
            if avg_fps > best_fps:
                best_fps = avg_fps
                best_config = config
    
    if best_config:
        print(f"\nBest stable configuration: {best_config}")
        print(f"Average FPS across all cameras: {best_fps:.1f}")
    else:
        print("\nNo configuration found that works reliably for all cameras simultaneously")

if __name__ == "__main__":
    camera_ids = [2, 3]
    run_comprehensive_test(camera_ids)