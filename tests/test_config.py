import unittest
from pathlib import Path

from config import CONFIG, AppConfig, Paths, ModelConfig, VideoConfig, ALL_STYLES


class TestConfig(unittest.TestCase):
    def test_default_paths(self):
        p = Paths()
        self.assertEqual(p.input_dir, Path("/input"))
        self.assertEqual(p.output_dir, Path("/output"))
        self.assertEqual(p.temp_dir, Path("/temp"))
        self.assertEqual(p.tasks_file, Path("/input/tasks.json"))
        self.assertEqual(p.results_file, Path("/output/results.json"))

    def test_model_config_defaults(self):
        m = ModelConfig()
        self.assertEqual(m.model_id, "google/gemma-4-12B-it")
        self.assertEqual(m.torch_dtype, "bfloat16")

    def test_video_config_defaults(self):
        v = VideoConfig()
        self.assertGreater(v.target_fps, 0)
        self.assertGreater(v.max_frames_per_video, 0)

    def test_all_styles(self):
        self.assertEqual(len(ALL_STYLES), 4)
        self.assertIn("formal", ALL_STYLES)
        self.assertIn("sarcastic", ALL_STYLES)
        self.assertIn("humorous_tech", ALL_STYLES)
        self.assertIn("humorous_non_tech", ALL_STYLES)

    def test_config_is_frozen(self):
        with self.assertRaises(Exception):
            CONFIG.paths = Paths()  # type: ignore


if __name__ == "__main__":
    unittest.main()
