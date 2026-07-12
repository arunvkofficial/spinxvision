import subprocess
from pathlib import Path

import cv2
import numpy as np

from config import CONFIG
from logger import logger
from utils import retry


def download_video(url: str, output_path: Path, timeout: int | None = None) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    timeout = timeout or CONFIG.video.download_timeout

    logger.info("Downloading video: %s -> %s", url, output_path)

    result = subprocess.run(
        ["ffmpeg", "-y", "-user_agent", "Mozilla/5.0", "-i", url, "-c", "copy", str(output_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg download failed (code {result.returncode}): {result.stderr[:500]}"
        )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Downloaded file is empty or missing: {output_path}")

    logger.info("Downloaded %s (%.1f MB)", output_path, output_path.stat().st_size / 1e6)
    return output_path


@retry(max_attempts=CONFIG.video.download_retries, delay=CONFIG.video.download_retry_delay)
def safe_download_video(url: str, output_path: Path) -> Path:
    return download_video(url, output_path)


def get_video_info(path: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {path}")

    info = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        if cap.get(cv2.CAP_PROP_FPS) > 0
        else 0,
    }
    cap.release()
    return info


def extract_frames(path: Path, frame_indices: list[int]) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {path}")

    frames: list[np.ndarray] = []
    idx_set = sorted(set(frame_indices))
    current = 0

    for target in idx_set:
        if target < current:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        ret, frame = cap.read()
        if ret:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            current = target + 1

    cap.release()
    logger.debug("Extracted %d/%d requested frames", len(frames), len(idx_set))
    return frames


def cleanup_video(path: Path) -> None:
    if path.exists():
        path.unlink()
        logger.debug("Cleaned up: %s", path)
