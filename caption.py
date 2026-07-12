from typing import Any

import numpy as np
from PIL import Image

from config import ALL_STYLES, CONFIG, StyleType
from logger import logger
from model import get_model
from prompts import build_vision_prompt


class CaptionGenerator:
    def __init__(self) -> None:
        self.model = get_model()

    def generate_styles(
        self, frames: list[np.ndarray], task_id: str, styles: list[StyleType] | None = None
    ) -> dict[StyleType, str]:
        if styles is None:
            styles = ALL_STYLES

        images = [Image.fromarray(f) for f in frames]
        scene_group = self._create_scene_group(images)
        num_images = min(len(scene_group), 5)
        selected_images = scene_group[:num_images]

        prompts = [build_vision_prompt(style, num_images) for style in styles]

        captions = self.model.generate_all_styles(
            selected_images, prompts, styles
        )

        for style in styles:
            if not captions.get(style):
                logger.warning(
                    "Missing %s caption for %s, using fallback", style, task_id
                )
                captions[style] = self._fallback_caption(style)
            else:
                logger.info("Generated %s caption for %s", style, task_id)

        return captions

    def _create_scene_group(self, images: list[Image.Image]) -> list[Image.Image]:
        max_images = CONFIG.video.max_frames_per_video
        if len(images) > max_images:
            step = len(images) // max_images
            return images[::step][:max_images]
        return images

    def _fallback_caption(self, style: StyleType) -> str:
        fallbacks: dict[StyleType, str] = {
            "formal": "The video depicts a scene with visible motion and activity.",
            "sarcastic": "Oh great, another video. Truly groundbreaking content here.",
            "humorous_tech": "This video compiles successfully, but there might be a few warnings.",
            "humorous_non_tech": "Well, that's a few seconds of my life I won't get back.",
        }
        return fallbacks.get(style, "Caption generation failed.")


def process_video_task(
    task_id: str,
    frames: list[np.ndarray],
    styles: list[StyleType] | None = None,
) -> dict[str, Any]:
    if styles is None:
        styles = ALL_STYLES

    generator = CaptionGenerator()
    captions = generator.generate_styles(frames, task_id, styles)

    result: dict[str, Any] = {
        "task_id": task_id,
        "captions": {},
    }
    for style in styles:
        result["captions"][style] = captions[style]

    logger.info("Completed task %s", task_id)
    return result
