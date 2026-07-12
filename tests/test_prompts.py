import unittest

from prompts import build_vision_prompt, STYLE_INSTRUCTIONS
from config import ALL_STYLES


class TestPrompts(unittest.TestCase):
    def test_all_styles_have_instructions(self):
        for style in ALL_STYLES:
            self.assertIn(style, STYLE_INSTRUCTIONS)
            self.assertGreater(len(STYLE_INSTRUCTIONS[style]), 10)

    def test_build_vision_prompt(self):
        for style in ALL_STYLES:
            messages = build_vision_prompt(style, num_images=3)
            self.assertIsInstance(messages, list)
            self.assertGreater(len(messages), 0)
            self.assertIn("role", messages[0])
            self.assertEqual(messages[0]["role"], "user")
            self.assertIn("content", messages[0])
            # Should have 3 image entries + 1 text entry
            image_entries = [c for c in messages[0]["content"] if c.get("type") == "image"]
            text_entries = [c for c in messages[0]["content"] if c.get("type") == "text"]
            self.assertEqual(len(image_entries), 3)
            self.assertEqual(len(text_entries), 1)
            self.assertIn("Style instructions:", text_entries[0]["text"])


if __name__ == "__main__":
    unittest.main()
