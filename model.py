import os
from typing import Any

import torch
from PIL import Image
from transformers import (
    Gemma4UnifiedForConditionalGeneration,
    Gemma4UnifiedProcessor,
    BitsAndBytesConfig,
)

from config import CONFIG, StyleType
from logger import logger


HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN") or None


class GemmaVisionModel:
    def __init__(self) -> None:
        self.device: str = "cpu"
        self.model: Any = None
        self.processor: Any = None
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return

        logger.info("Loading model: %s", CONFIG.model.model_id)

        dtype = self._resolve_dtype()
        self.device = self._resolve_device()

        quantization_config = None
        if CONFIG.model.load_in_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=dtype,
            )
        elif CONFIG.model.load_in_8bit:
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)

        token_kwargs: dict[str, Any] = {}
        if HF_TOKEN:
            token_kwargs["token"] = HF_TOKEN

        try:
            logger.info("Downloading model (this may take a while)...")
            self.model = Gemma4UnifiedForConditionalGeneration.from_pretrained(
                CONFIG.model.model_id,
                torch_dtype=dtype,
                device_map=self.device if self.device != "cpu" else None,
                quantization_config=quantization_config,
                **token_kwargs,
            )
            self.processor = Gemma4UnifiedProcessor.from_pretrained(
                CONFIG.model.model_id,
                **token_kwargs,
            )

            if self.device == "cpu":
                self.model = self.model.to("cpu")

            self.model.eval()
            self._loaded = True
            logger.info("Model loaded on %s with dtype %s", self.device, dtype)

        except Exception as e:
            logger.error("Failed to load model: %s", e)
            raise

    def _resolve_dtype(self) -> torch.dtype:
        dtype_map = {
            "bfloat16": torch.bfloat16,
            "float16": torch.float16,
            "float32": torch.float32,
        }
        return dtype_map.get(CONFIG.model.torch_dtype, torch.bfloat16)

    def _resolve_device(self) -> str:
        if CONFIG.device != "auto":
            return CONFIG.device
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            logger.info("GPU detected: %s (%d devices)", device_name, device_count)
            return "cuda"
        logger.info("No GPU detected, using CPU")
        return "cpu"

    def generate_caption(
        self,
        images: list[Image.Image],
        messages: list[dict],
    ) -> str:
        if not self._loaded:
            self.load()

        text = self.processor.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )

        inputs = self.processor(
            images=images,
            text=text,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=CONFIG.model.max_new_tokens,
                temperature=CONFIG.model.temperature,
                top_p=CONFIG.model.top_p,
                top_k=CONFIG.model.top_k,
                do_sample=CONFIG.model.do_sample,
            )

        generated_ids = generated_ids[:, inputs["input_ids"].shape[1] :]
        caption = self.processor.decode(
            generated_ids[0], skip_special_tokens=True
        ).strip()

        return caption

    def generate_all_styles(
        self,
        images: list[Image.Image],
        prompts: list[list[dict]],
        styles: list[StyleType],
    ) -> dict[StyleType, str]:
        if not self._loaded:
            self.load()

        logger.info("Generating %d style captions", len(styles))

        results: dict[StyleType, str] = {}
        for messages, style in zip(prompts, styles):
            try:
                caption = self.generate_caption(images, messages)
                results[style] = caption
            except Exception as e:
                logger.error("Failed to generate %s caption: %s", style, e)
                results[style] = ""

        return results

    def unload(self) -> None:
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self._loaded = False
        logger.info("Model unloaded")


_gemma_model: GemmaVisionModel | None = None


def get_model() -> GemmaVisionModel:
    global _gemma_model
    if _gemma_model is None:
        _gemma_model = GemmaVisionModel()
    return _gemma_model
