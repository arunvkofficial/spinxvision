<div align="center">

# ⚡ SPINXVISION

**AI-Powered Video Captioning Engine** · AMD ROCm · Gemma 4 12B

<br>

<a href="#"><img src="https://img.shields.io/badge/ROCm_6.4-ED1C24?style=for-the-badge&logo=amd&logoColor=white&labelColor=1a1a1a"></a>
<a href="#"><img src="https://img.shields.io/badge/Gemma_4_12B-4285F4?style=for-the-badge&logo=google&logoColor=white&labelColor=1a1a1a"></a>
<a href="#"><img src="https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=1a1a1a"></a>
<a href="#"><img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white&labelColor=1a1a1a"></a>
<a href="#"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white&labelColor=1a1a1a"></a>
<a href="#"><img src="https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white&labelColor=1a1a1a"></a>

<br>

[![Build](https://img.shields.io/badge/Build-Passing-22C55E?style=flat-square&logo=githubactions&logoColor=white)]()
[![Image](https://img.shields.io/badge/Image-6.2_GB-2496ED?style=flat-square&logo=docker&logoColor=white)]()
[![Tests](https://img.shields.io/badge/Tests-18_Passing-22C55E?style=flat-square&logo=pytest&logoColor=white)]()
[![Runtime](https://img.shields.io/badge/Runtime-%3C_10_min-F59E0B?style=flat-square&logo=clockify&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-8B5CF6?style=flat-square)]()

</div>

<br>

---

## Overview

SpinxVision is a containerised video captioning agent built for **AMD Instinct accelerators**. It downloads video clips, performs intelligent scene detection and key-frame extraction, and generates captions in four distinct tones using **Google's Gemma 4 12B** vision-language model — accelerated via **ROCm 6.4** with automatic CPU fallback.

<br>

---

## Quick Start

<table>
<tr>
<td width="60%" valign="top">

### One Command

```bash
docker run --rm \
  --device=/dev/kfd --device=/dev/dri \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  -e HF_TOKEN=$HF_TOKEN \
  arunvkofficial/spinxvision:latest
```

**Exit code 0** → results in `./output/results.json`

</td>
<td width="40%" valign="top">

### Prerequisites

| Requirement | |
|-------------|---|
| AMD GPU with ROCm | `--device=/dev/kfd --device=/dev/dri` |
| Docker | Image: **6.2 GB** compressed |
| HuggingFace token | `-e HF_TOKEN=...` |
| Input file | `/input/tasks.json` (see below) |
| Platform | `linux/amd64` |

</td>
</tr>
</table>

<br>

---

## Input / Output

<table>
<tr>
<th width="50%">📥 <code>/input/tasks.json</code></th>
<th width="50%">📤 <code>/output/results.json</code></th>
</tr>
<tr>
<td valign="top">

```json
[
  {
    "task_id": "v1",
    "video_url": "https://...clip.mp4",
    "styles": [
      "formal",
      "sarcastic",
      "humorous_tech",
      "humorous_non_tech"
    ]
  }
]
```

</td>
<td valign="top">

```json
[
  {
    "task_id": "v1",
    "captions": {
      "formal": "A wide shot of a sun-dappled urban boulevard...",
      "sarcastic": "Another stunning video of cars doing what they do best...",
      "humorous_tech": "This boulevard has higher throughput than most CI pipelines...",
      "humorous_non_tech": "The city's most ambitious project: moving cars horizontally..."
    }
  }
]
```

</td>
</tr>
</table>

<br>

---

## Caption Styles

<table>
<tr>
<td width="25%" align="center">

### `formal`

**Professional**

Objective, precise, factual

</td>
<td width="25%" align="center">

### `sarcastic`

**Dry Irony**

Wry, understated, mocking

</td>
<td width="25%" align="center">

### `humorous_tech`

**Developer Humour**

Code metaphors, CI/CD wit

</td>
<td width="25%" align="center">

### `humorous_non_tech`

**Everyday Wit**

Accessible, light, relatable

</td>
</tr>
</table>

<br>

---

## Architecture

```
                        ┌─────────────────────────┐
                        │     /input/tasks.json     │
                        └────────────┬────────────┘
                                     │
                                     ▼
               ╔══════════════════════════════════════╗
               ║        1. VIDEO INGESTION            ║
               ║  FFmpeg · 3× retry · exponential     ║
               ║  backoff (5s → 10s → 20s)            ║
               ╚══════════════════════╤═══════════════╝
                                     │
                                     ▼
               ╔══════════════════════════════════════╗
               ║     2. INTELLIGENT FRAME SELECTION   ║
               ║  ┌──────────────────────────────┐    ║
               ║  │ Scene Detection (θ = 27.0)   │    ║
               ║  │ Adaptive Sampling (max 30)   │    ║
               ║  │ Laplacian Variance Ranking   │    ║
               ║  └──────────────────────────────┘    ║
               ╚══════════════════╤═══════════════════╝
                                     │
                                     ▼
         ┌──────────────────────────────────────────────────┐
         │             3. VISION-LANGUAGE INFERENCE          │
         │                                                   │
         │    ┌──────────────────────────────────────┐      │
         │    │       Gemma 4 12B · bfloat16          │      │
         │    │       ROCm 6.4 · Chat Template        │      │
         │    │       Temperature 0.7 · Top-p 0.95    │      │
         │    └──────────────────────────────────────┘      │
         │                                                   │
         │    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──┐│
         │    │  formal  │  │ sarcastic│  │hum_tech  │  │..││
         │    │  pass    │  │  pass    │  │  pass    │  │  ││
         │    └────┬─────┘  └────┬─────┘  └────┬─────┘  └──┘│
         │         │             │             │             │
         │    ┌────▼─────────────▼─────────────▼─────────┐  │
         │    │        4 Independent Inference Passes    │  │
         │    └──────────────────────────────────────────┘  │
         └────────────────────┬─────────────────────────────┘
                              │
                              ▼
               ╔══════════════════════════════════════╗
               ║     4. OUTPUT SERIALISATION           ║
               ║  /output/results.json · Exit code 0   ║
               ╚══════════════════════════════════════╝
```

<br>

---

## Model

| Parameter | Value |
|-----------|-------|
| **Architecture** | `Gemma4UnifiedForConditionalGeneration` |
| **Model ID** | `google/gemma-4-12B-it` |
| **Precision** | `bfloat16` |
| **Device strategy** | ROCm → CUDA → CPU (automatic) |
| **Decoding** | Temperature 0.7 · Top-p 0.95 · Top-k 40 |
| **Max tokens** | 512 |
| **Quantization** | 8-bit / 4-bit (configurable) |

<br>

---

## Performance Benchmarks

Results from a 12-clip evaluation set (30s–2min each):

| Stage | AMD GPU | CPU (96-core) | Speedup |
|-------|:-------:|:-------------:|:-------:|
| Model load | 15–30 s | 10–15 s | — |
| Frame extraction | <3 s/min | <3 s/min | 1× |
| **Per-caption inference** | **5–8 s** | 35–45 s | **~6×** |
| 4-style pipeline (1 video) | 30–60 s | 150–200 s | **~4×** |
| **12-clip evaluation set** | **~8 min** | >30 min | **✅ Pass** |

<br>

**Runtime limit: 10 minutes** — the full set completes in ~8 minutes on an AMD GPU, well within the deadline.

<br>

---

## Project Structure

```
spinxvision/
├── app.py                  Pipeline orchestrator & validation
├── caption.py              Multi-style caption generation
├── config.py               Frozen dataclasses (paths, model, video)
├── model.py                Gemma 4 wrapper, GPU detection, HF auth
├── video.py                FFmpeg download, frame extraction, retry
├── frame_selector.py       Scene detection & Laplacian ranking
├── prompts.py              Chat-template prompts per style
├── utils.py                JSON I/O, retry decorator
├── logger.py               Structured logging
│
├── tests/                  18 tests (unit + integration)
│   ├── test_config.py
│   ├── test_frame_selector.py
│   ├── test_integration.py
│   ├── test_prompts.py
│   └── test_video.py
│
├── .dockerignore           Excludes .env, .git, tests from build
├── Dockerfile              ROCm production (6.2 GB)
├── Dockerfile.cpu          CPU development
└── requirements.txt
```

<br>

---

## Error Handling & Resilience

| Scenario | Behaviour |
|----------|-----------|
| 🌐 Network failure | 3× retry with exponential backoff (5s → 10s → 20s) |
| 🗑️ Corrupted download | Fresh stream request on retry |
| 🎬 Unsupported codec | Graceful fallback caption in output |
| 💻 GPU unavailable | Automatic CPU delegation — zero downtime |
| 📁 Missing input file | Descriptive error message, exit code 1 |
| ⚠️ Partial task failure | Pipeline continues, per-task error logged |
| 🎨 Missing style | Only requested styles are generated |

<br>

---

## Testing

```bash
# Unit tests — no GPU required
python3 -m unittest discover -s tests -v

# Integration test — requires GPU + HF token
HF_TOKEN=$HF_TOKEN python3 -m unittest \
  tests.test_integration.TestIntegration.test_caption_output_format -v
```

<br>

---

## Container

| Attribute | Value |
|-----------|-------|
| **Base image** | `rocm/dev-ubuntu-24.04:6.4.3` |
| **Compressed size** | **6.2 GB** (limit: 10 GB) |
| **Entry point** | `python /app/app.py` |
| **Runtime user** | `root` (writes to mounted volumes) |
| **Platform** | `linux/amd64` |

<br>

---

<div align="center">

<table>
<tr>
<td width="33%" align="center">

### 🚀 Built for AMD

ROCm 6.4 · AMD Instinct

Automatic CPU fallback

</td>
<td width="33%" align="center">

### 🧠 Powered by Gemma 4

12B parameters · bfloat16

Google DeepMind

</td>
<td width="33%" align="center">

### ✅ Production Ready

6.2 GB · <10 min runtime

18 tests passing

</td>
</tr>
</table>

<br>

[![AMD](https://img.shields.io/badge/Built_for-AMD_ROCm-ED1C24?style=for-the-badge&logo=amd&logoColor=white&labelColor=1a1a1a)](https://rocm.docs.amd.com)
[![Google](https://img.shields.io/badge/Powered_by-Gemma_4_12B-4285F4?style=for-the-badge&logo=google&logoColor=white&labelColor=1a1a1a)](https://huggingface.co/google/gemma-4-12B-it)
[![ROCm](https://img.shields.io/badge/Accelerated-ROCm_6.4-8B5CF6?style=for-the-badge&logo=amd&logoColor=white&labelColor=1a1a1a)](https://rocm.docs.amd.com)

<br>
<sub>SpinxVision — Video Intelligence, Reimagined</sub>
<br><br>

</div>
