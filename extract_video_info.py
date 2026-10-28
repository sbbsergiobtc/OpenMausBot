import cv2, os, sys

video_path = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\Almacenamiento\Record_2026-10-27-00-23-17_1c337646f29875672b5a61192b9010f9.mp4"
output_dir = r"C:\Users\Sergio\.gemini\antigravity\brain\04f2d2d7-9d10-464c-84fc-546dff59a7f6\video_frames"
os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error opening video")
    sys.exit(1)

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps if fps > 0 else 0
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Resolution: {width}x{height}")
print(f"FPS: {fps}")
print(f"Total Frames: {total_frames}")
print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

# We want to sample frames at regular intervals across the entire video
# If duration is e.g. 60 seconds, extract every 4 seconds.
# Let's extract around 15-20 representative frames.
num_samples = 16
interval = max(1, total_frames // num_samples)

saved_frames = []
for i in range(num_samples):
    frame_idx = min(i * interval, total_frames - 1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        timestamp_sec = frame_idx / fps
        fname = f"frame_{i:02d}_{int(timestamp_sec)}s.png"
        fpath = os.path.join(output_dir, fname)
        cv2.imwrite(fpath, frame)
        saved_frames.append((timestamp_sec, fpath))
        print(f"Saved frame {i} at {timestamp_sec:.1f}s -> {fname}")

cap.release()
print(f"Extraction complete! {len(saved_frames)} frames saved.")
