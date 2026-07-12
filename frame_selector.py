from pathlib import Path

import cv2
import numpy as np

from config import CONFIG
from logger import logger


def detect_scenes(path: Path) -> list[tuple[int, int]]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    threshold = CONFIG.video.scene_threshold
    min_scene_frames = max(1, int(CONFIG.video.min_scene_len * fps))

    scenes: list[tuple[int, int]] = []
    prev_frame: np.ndarray | None = None
    scene_start = 0

    for frame_idx in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            diff = cv2.absdiff(gray, prev_frame)
            mean_diff = float(np.mean(diff))

            if mean_diff > threshold:
                scene_end = frame_idx - 1
                if scene_end - scene_start >= min_scene_frames:
                    scenes.append((scene_start, scene_end))
                scene_start = frame_idx

        prev_frame = gray

        if frame_idx % 500 == 0 and frame_idx > 0:
            logger.debug("Scene detection progress: %d/%d frames", frame_idx, total_frames)

    if total_frames - scene_start >= min_scene_frames:
        scenes.append((scene_start, total_frames - 1))

    cap.release()
    logger.info("Detected %d scenes in %d frames", len(scenes), total_frames)
    return scenes


def select_key_frames(scenes: list[tuple[int, int]], total_frames: int) -> list[int]:
    max_frames = CONFIG.video.max_frames_per_video
    if not scenes:
        if total_frames == 0:
            return []
        step = max(1, total_frames // max_frames)
        return list(range(0, total_frames, step))[:max_frames]

    frames_per_scene = max(1, max_frames // len(scenes))
    selected: list[int] = []

    for start, end in scenes:
        scene_len = end - start
        if scene_len <= 0:
            continue
        step = max(1, scene_len // frames_per_scene)
        for offset in range(0, scene_len, step):
            if len(selected) >= max_frames:
                break
            midpoint = start + min(offset, scene_len - 1)
            selected.append(midpoint)
        if len(selected) >= max_frames:
            break

    if len(selected) < max_frames and total_frames > 0:
        step = max(1, total_frames // (max_frames - len(selected)))
        for i in range(0, total_frames, step):
            if len(selected) >= max_frames:
                break
            if i not in selected:
                selected.append(i)

    selected = sorted(set(selected))[:max_frames]
    logger.info("Selected %d key frames from %d scenes", len(selected), len(scenes))
    return selected


def rank_frames(frames: list[np.ndarray]) -> list[int]:
    if not frames:
        return []

    scores: list[tuple[int, float]] = []
    for i, frame in enumerate(frames):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = float(np.var(laplacian))
        scores.append((i, variance))

    scores.sort(key=lambda x: x[1], reverse=True)
    ranked = [idx for idx, _ in scores]
    return ranked


def select_best_frames(path: Path) -> list[np.ndarray]:
    from video import extract_frames

    scenes = detect_scenes(path)

    cap = cv2.VideoCapture(str(path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    key_frame_indices = select_key_frames(scenes, total_frames)

    if not key_frame_indices:
        logger.warning("No key frames selected, using uniform sampling")
        step = max(1, total_frames // CONFIG.video.max_frames_per_video)
        key_frame_indices = list(range(0, total_frames, step))[:CONFIG.video.max_frames_per_video]

    frames = extract_frames(path, key_frame_indices)

    if len(frames) > CONFIG.video.max_frames_per_video:
        ranked = rank_frames(frames)
        ranked_indices = [key_frame_indices[r] for r in ranked[:CONFIG.video.max_frames_per_video]]
        ranked_indices.sort()
        frames = extract_frames(path, ranked_indices)

    resized = [cv2.resize(f, (CONFIG.video.frame_width, CONFIG.video.frame_height)) for f in frames]

    logger.info("Selected %d best frames from %s", len(resized), path.name)
    return resized
