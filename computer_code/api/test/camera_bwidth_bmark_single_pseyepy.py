from pseyepy import Camera
import time
import numpy as np

def test_camera_config(camera_index, resolution, fps, duration=5):
    print(f"\nTesting camera {camera_index} with:")
    print(f"Resolution: {'640x480' if resolution == Camera.RES_LARGE else '320x240'}")
    print(f"Target FPS: {fps}")
    
    try:
        cam = Camera(camera_index, fps=fps, resolution=resolution)
        frames_received = 0
        frame_times = []
        failed_reads = 0
        last_frame_time = time.time()
        start_time = time.time()

        while (time.time() - start_time) < duration:
            frame, timestamp = cam.read()  # timestamp is in microseconds
            current_time = time.time()
            
            if frame is not None:
                frames_received += 1
                frame_times.append(current_time - last_frame_time)
            else:
                failed_reads += 1
            
            last_frame_time = current_time

        test_duration = time.time() - start_time
        actual_fps = frames_received / test_duration
        frame_time_std = np.std(frame_times) * 1000 if frame_times else 0
        
        print("\nResults:")
        print(f"Frames received: {frames_received}")
        print(f"Failed reads: {failed_reads}")
        print(f"Actual FPS: {actual_fps:.1f}")
        print(f"Frame time std: {frame_time_std:.1f}ms")
        
        # Calculate bandwidth
        if resolution == Camera.RES_LARGE:
            frame_size = 640 * 480
        else:
            frame_size = 320 * 240
        
        bandwidth_MBps = (frame_size * actual_fps) / (1024 * 1024)
        print(f"Estimated bandwidth: {bandwidth_MBps:.1f} MB/s")
        
        cam.end()
        return {
            'fps': actual_fps,
            'frame_time_std': frame_time_std,
            'failed_reads': failed_reads,
            'bandwidth': bandwidth_MBps
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def run_single_camera_tests(camera_index=0):
    print(f"=== Single Camera Benchmark (Camera {camera_index}) ===\n")
    
    configs = [
        (Camera.RES_SMALL, 30),
        (Camera.RES_SMALL, 60),
        (Camera.RES_SMALL, 90),
        (Camera.RES_SMALL, 120),
        (Camera.RES_LARGE, 30),
        (Camera.RES_LARGE, 60),
        (Camera.RES_LARGE, 75),  # Testing higher FPS at 640x480
        (Camera.RES_LARGE, 90)
    ]
    
    results = {}
    
    for resolution, fps in configs:
        key = f"{'640x480' if resolution == Camera.RES_LARGE else '320x240'}@{fps}"
        results[key] = test_camera_config(camera_index, resolution, fps)
        time.sleep(1)  # Pause between tests
    
    # Print summary
    print("\n=== Summary ===")
    print("\nConfiguration | Actual FPS | Frame Time Std | Failed Reads | Bandwidth")
    print("-" * 75)
    
    for config, result in results.items():
        if result:
            print(f"{config:12} | {result['fps']:9.1f} | {result['frame_time_std']:11.1f}ms | "
                  f"{result['failed_reads']:11d} | {result['bandwidth']:7.1f} MB/s")

if __name__ == "__main__":
    camera_index = 0  # Change this to test different cameras
    run_single_camera_tests(camera_index)