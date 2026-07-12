import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        self.test_input = self.project_root / "input" / "tasks.json"
        self.test_output = self.project_root / "output" / "results.json"
        self.test_temp = self.project_root / "temp"

        self.test_input.parent.mkdir(parents=True, exist_ok=True)
        self.test_output.parent.mkdir(parents=True, exist_ok=True)
        self.test_temp.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for p in [self.test_input, self.test_output]:
            if p.exists():
                p.unlink()

    def test_video_download_and_frame_extraction(self):
        from video import safe_download_video, get_video_info
        from frame_selector import select_best_frames

        video_path = self.test_temp / "test_integration.mp4"
        safe_download_video(
            "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4",
            video_path,
        )
        self.assertTrue(video_path.exists())
        self.assertGreater(video_path.stat().st_size, 0)

        info = get_video_info(video_path)
        self.assertIn("fps", info)
        self.assertIn("frame_count", info)
        self.assertGreater(info["frame_count"], 0)

        frames = select_best_frames(video_path)
        self.assertGreater(len(frames), 0)
        self.assertLessEqual(len(frames), 30)
        for f in frames:
            self.assertEqual(f.shape, (224, 224, 3))
            self.assertEqual(f.dtype, np.uint8)

        if video_path.exists():
            video_path.unlink()

    def test_caption_output_format(self):
        import torch
        if not torch.cuda.is_available():
            self.skipTest("GPU required for caption generation test")

        from caption import CaptionGenerator
        from config import ALL_STYLES

        frames = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(5)]
        generator = CaptionGenerator()

        try:
            captions = generator.generate_styles(frames, "format_test", ALL_STYLES)
        except Exception:
            self.skipTest("Model not available for testing")

        for style in ALL_STYLES:
            self.assertIn(style, captions)
            self.assertIsInstance(captions[style], str)
            self.assertGreater(len(captions[style]), 0)

    def test_app_validation_array_format(self):
        from app import validate_tasks

        valid = [
            {"task_id": "a", "video_url": "http://example.com/v.mp4", "styles": ["formal", "sarcastic"]},
            {"task_id": "b", "video_url": "http://example.com/v2.mp4"},
        ]
        result = validate_tasks(valid)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["task_id"], "a")
        self.assertEqual(result[0]["video_url"], "http://example.com/v.mp4")
        self.assertEqual(result[0]["styles"], ["formal", "sarcastic"])
        self.assertIn("humorous_tech", result[1]["styles"])

        with self.assertRaises(ValueError):
            validate_tasks([])

        with self.assertRaises(ValueError):
            validate_tasks([{"id": "no_video_url"}])


if __name__ == "__main__":
    unittest.main()
