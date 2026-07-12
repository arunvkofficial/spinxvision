import unittest
import numpy as np
from pathlib import Path

from video import get_video_info, extract_frames


class TestVideoUtils(unittest.TestCase):
    def test_extract_frames_nonexistent_raises(self):
        with self.assertRaises(RuntimeError):
            extract_frames(Path("/nonexistent.mp4"), [])


if __name__ == "__main__":
    unittest.main()
