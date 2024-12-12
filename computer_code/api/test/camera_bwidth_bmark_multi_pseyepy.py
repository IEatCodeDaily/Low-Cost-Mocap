from pseyepy import Camera
import numpy as np
from datetime import datetime
import time

class CameraTest:
    def __init__(self, camera_indexes, resolution, fps):
        self.cameras = None
        self.camera_indexes = camera_indexes
        self.resolution = resolution
        self.fps = fps
        self.frame_counts = {i: 0 for i in camera_indexes}
        self.frame_times = {i: [] for i in camera_indexes}
        self.failed_reads = {i: 0 for i in camera_indexes}

    def run_test(self, duration=5):
        # Initialize cameras
        try:
            self.cameras = Camera(self.camera_indexes, fps=self.fps, resolution=self.resolution)
        except Exception as e:
            print(f"Failed to initialize cameras: {e}")
            return None

        start_time = time.time()
        last_frame_times = {i: start_time for i in self.camera_indexes}

        while (time.time() - start_time) < duration:
            # Read from all cameras
            frames, timestamps = self.cameras.read()
            
            current_time = time.time()
            
            # Process each camera's frame
            for idx, frame in enumerate(frames):
                cam_idx = self.camera_indexes[idx]
                if frame is not None:
                    self.frame_counts[cam_idx] += 1
                    frame_time = current_time - last_frame_times[cam_idx]
                    self.frame_times[cam_idx].append(frame_time)
                    last_frame_times[cam_idx] = current_time
                else:
                    self.failed_reads[cam_idx] += 1

        # Clean up
        if self.cameras:
            self.cameras.end()

        # Calculate statistics
        results = {}
        test_duration = time.time() - start_time
        
        for cam_idx in self.camera_indexes:
            fps = self.frame_counts[cam_idx] / test_duration if test_duration > 0 else 0
            frame_time_std = np.std(self.frame_times[cam_idx]) * 1000 if self.frame_times[cam_idx] else 0
            
            results[cam_idx] = {
                'fps': fps,
                'frames': self.frame_counts[cam_idx],
                'failed_reads': self.failed_reads[cam_idx],
                'frame_time_std_ms': frame_time_std
            }
            
        return results

def run_comprehensive_test(camera_indexes):
    # Test configurations
    configs = [
        # (resolution_mode, fps, description)
        (Camera.RES_SMALL, 30, "320x240@30"),
        (Camera.RES_SMALL, 60, "320x240@60"),
        (Camera.RES_SMALL, 90, "320x240@90"),
        (Camera.RES_SMALL, 120, "320x240@120"),
        (Camera.RES_LARGE, 30, "640x480@30"),
        (Camera.RES_LARGE, 60, "640x480@60"),
        (Camera.RES_LARGE, 75, "640x480@75"),
        (Camera.RES_LARGE, 100, "640x480@100"),
    ]
    
    results = {}
    
    print("\n=== PSEyePy Camera Test ===")
    print(f"Testing {len(camera_indexes)} cameras simultaneously")
    
    for resolution, fps, desc in configs:
        print(f"\nTesting configuration: {desc}")
        test = CameraTest(camera_indexes, resolution, fps)
        results[desc] = test.run_test(duration=7)
        time.sleep(2)  # Pause between tests
    
    # Print summary
    print("\n=== Test Results (PSEyePy) ===")
    print("\nConfiguration | Avg FPS | Working Cameras | Frame Time Std | Failed Reads")
    print("-" * 75)
    
    for config, test_results in results.items():
        if test_results:
            working_cameras = len([r for r in test_results.values() if r['fps'] > 1])
            avg_fps = np.mean([r['fps'] for r in test_results.values() if r['fps'] > 1]) if working_cameras else 0
            avg_std = np.mean([r['frame_time_std_ms'] for r in test_results.values() if r['fps'] > 1]) if working_cameras else 0
            total_fails = sum(r['failed_reads'] for r in test_results.values())
            
            print(f"{config:13} | {avg_fps:7.1f} | {working_cameras:2d}/{len(camera_indexes)}           | "
                  f"{avg_std:8.1f}ms    | {total_fails:5d}")
            
            # Print per-camera details
            print("  Per-camera FPS:", end=" ")
            for cam_idx, r in test_results.items():
                print(f"Cam{cam_idx}: {r['fps']:4.1f}", end=" ")
            print()
    
    # Find best configuration
    best_config = None
    best_fps = 0
    for config, test_results in results.items():
        if test_results:
            working_cameras = len([r for r in test_results.values() if r['fps'] > 1])
            if working_cameras == len(camera_indexes):
                avg_fps = np.mean([r['fps'] for r in test_results.values()])
                if avg_fps > best_fps:
                    best_fps = avg_fps
                    best_config = config
    
    if best_config:
        print(f"\nBest stable configuration: {best_config}")
        print(f"Average FPS across all cameras: {best_fps:.1f}")
    else:
        print("\nNo stable configuration found for all cameras")

if __name__ == "__main__":
    # Test with specific camera indexes
    # Get camera indexes from the PSEyePy camera test script
    camera_indexes = [0, 1, 2, 3]  # Adjust based on your setup
    run_comprehensive_test(camera_indexes)