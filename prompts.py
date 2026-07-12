from config import StyleType


SYSTEM_PROMPT_BASE = """You are a precise video analyst and expert caption writer.

You are shown key frames extracted from a video clip.

For formal captions: describe ONLY visible content. Never invent details.
For creative styles (sarcastic, humorous): you may add light interpretation
and wit, but the core description must still match what is visible.

Be concise. Each caption should be 2-4 sentences."""

STYLE_INSTRUCTIONS: dict[StyleType, str] = {
    "formal": (
        "Write an objective, professional caption as if for a news report or documentary. "
        "State exactly what is shown — setting, subjects, actions, lighting, colours. "
        "Avoid opinion, exaggeration, or emotional language."
    ),
    "sarcastic": (
        "Write a dry, ironic caption that describes the scene with mock seriousness. "
        "Use understatement — treat mundane subjects as if they are remarkable. "
        "The sarcasm should feel subtle and intelligent, not mean-spirited."
    ),
    "humorous_tech": (
        "Write a funny caption using programming or tech metaphors. "
        "Compare real-world scenes to code, systems, debugging, or engineering workflows. "
        "Avoid overused jokes. Be clever and original."
    ),
    "humorous_non_tech": (
        "Write a light, relatable caption using everyday humour. "
        "The joke should be understandable to anyone without technical knowledge. "
        "Use playful observations about ordinary situations."
    ),
}


def build_vision_prompt(style: StyleType, num_images: int = 5) -> list[dict]:
    style_instruction = STYLE_INSTRUCTIONS[style]

    content: list[dict] = []
    for _ in range(num_images):
        content.append({"type": "image"})

    text = (
        f"{SYSTEM_PROMPT_BASE}\n\n"
        f"Style instructions: {style_instruction}\n\n"
        "Write a caption for the video shown in the attached image(s). "
        "Match the requested style precisely."
    )
    content.append({"type": "text", "text": text})

    return [{"role": "user", "content": content}]
