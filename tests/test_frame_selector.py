import unittest
import numpy as np
from pathlib import Path

from frame_selector import select_key_frames, rank_frames


class TestSelectKeyFrames(unittest.TestCase):
    def test_no_scenes(self):
        result = select_key_frames([], 100)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 30)

    def test_single_scene(self):
        scenes = [(0, 199)]
        result = select_key_frames(scenes, 200)
        self.assertGreater(len(result), 0)
        self.assertLessEqual(len(result), 30)

    def test_empty_total_frames(self):
        result = select_key_frames([], 0)
        self.assertEqual(result, [])

    def test_max_frames_limit(self):
        scenes = [(i * 100, i * 100 + 99) for i in range(50)]
        result = select_key_frames(scenes, 5000)
        self.assertLessEqual(len(result), 30)


class TestRankFrames(unittest.TestCase):
    def setUp(self):
        self.blank = np.zeros((100, 100, 3), dtype=np.uint8)
        self.sharp = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    def test_ranks_sharp_higher(self):
        frames = [self.blank, self.sharp, self.blank]
        ranked = rank_frames(frames)
        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0], 1)

    def test_empty_list(self):
        self.assertEqual(rank_frames([]), [])

    def test_single_frame(self):
        self.assertEqual(rank_frames([self.blank]), [0])


if __name__ == "__main__":
    unittest.main()
