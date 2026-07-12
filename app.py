import sys
import time
from typing import Any

from config import ALL_STYLES, CONFIG, StyleType
from logger import logger
from utils import load_json, save_json, ensure_dir


def validate_tasks(tasks_data: Any) -> list[dict[str, Any]]:
    if not isinstance(tasks_data, list):
        raise ValueError("tasks.json must be a JSON array")

    if len(tasks_data) == 0:
        raise ValueError("tasks array must not be empty")

    validated: list[dict[str, Any]] = []
    for i, task in enumerate(tasks_data):
        if not isinstance(task, dict):
            raise ValueError(f"Task {i} is not a dictionary")
        if "task_id" not in task:
            raise ValueError(f"Task {i} missing 'task_id'")
        if "video_url" not in task:
            raise ValueError(f"Task {i} missing 'video_url'")

        styles = task.get("styles", ALL_STYLES)
        if not isinstance(styles, list) or len(styles) == 0:
            styles = ALL_STYLES

        validated.append({
            "task_id": str(task["task_id"]),
            "video_url": str(task["video_url"]),
            "styles": [s for s in styles if s in ALL_STYLES],
        })

    logger.info("Validated %d tasks", len(validated))
    return validated


def process_single_task(task: dict[str, Any]) -> dict[str, Any]:
    from video import safe_download_video, cleanup_video
    from frame_selector import select_best_frames
    from caption import process_video_task

    task_id = task["task_id"]
    video_url = task["video_url"]
    styles: list[StyleType] = task.get("styles", ALL_STYLES)
    video_path = CONFIG.paths.temp_dir / f"{task_id}.mp4"

    logger.info("Processing task %s: %s", task_id, video_url)

    safe_download_video(video_url, video_path)

    try:
        frames = select_best_frames(video_path)
        if not frames:
            raise RuntimeError("No frames extracted from video")

        result = process_video_task(task_id, frames, styles)
        return result
    finally:
        cleanup_video(video_path)


def run_pipeline() -> None:
    ensure_dir(CONFIG.paths.temp_dir)
    ensure_dir(CONFIG.paths.output_dir)

    logger.info("=" * 60)
    logger.info("Video Captioning Agent - Starting")
    logger.info("=" * 60)

    tasks_data = load_json(CONFIG.paths.tasks_file)
    tasks = validate_tasks(tasks_data)
    logger.info("Loaded %d tasks from %s", len(tasks), CONFIG.paths.tasks_file)

    from model import get_model
    logger.info("Pre-loading model before processing tasks...")
    model = get_model()
    model.load()

    results: list[dict[str, Any]] = []
    failures = 0

    for task in tasks:
        start = time.time()
        try:
            result = process_single_task(task)
            results.append(result)
            logger.info(
                "Task %s completed in %.2fs",
                task["task_id"], time.time() - start,
            )
        except Exception as e:
            failures += 1
            logger.error("Task %s failed: %s", task["task_id"], e)
            entry: dict[str, Any] = {
                "task_id": task["task_id"],
                "captions": {},
            }
            for style in task.get("styles", ALL_STYLES):
                entry["captions"][style] = "Caption generation failed."
            results.append(entry)

    save_json(CONFIG.paths.results_file, results)
    logger.info(
        "Pipeline complete: %d/%d succeeded, %d failed",
        len(results) - failures, len(tasks), failures,
    )


def main() -> None:
    try:
        run_pipeline()
        logger.info("Exiting with code 0")
        sys.exit(0)
    except Exception as e:
        logger.critical("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
