from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


StyleType = Literal["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
ALL_STYLES: list[StyleType] = ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]


@dataclass(frozen=True)
class Paths:
    input_dir: Path = Path("/input")
    output_dir: Path = Path("/output")
    temp_dir: Path = Path("/temp")

    tasks_file: Path = field(init=False)
    results_file: Path = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "tasks_file", self.input_dir / "tasks.json")
        object.__setattr__(self, "results_file", self.output_dir / "results.json")


@dataclass(frozen=True)
class ModelConfig:
    model_id: str = "google/gemma-4-12B-it"
    torch_dtype: str = "bfloat16"
    device_map: str = "auto"
    max_new_tokens: int = 128
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    do_sample: bool = True
    load_in_8bit: bool = False
    load_in_4bit: bool = False


@dataclass(frozen=True)
class VideoConfig:
    target_fps: float = 1.0
    max_frames_per_video: int = 30
    scene_threshold: float = 27.0
    min_scene_len: float = 0.5
    frame_width: int = 224
    frame_height: int = 224
    download_timeout: int = 60
    download_retries: int = 2
    download_retry_delay: int = 3


@dataclass(frozen=True)
class AppConfig:
    paths: Paths = field(default_factory=Paths)
    model: ModelConfig = field(default_factory=ModelConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    max_workers: int = 4
    device: str = "auto"


CONFIG = AppConfig()
