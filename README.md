# Z-Image-Turbo

A command-line tool for text-to-image generation using Alibaba's [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) model, with GPU acceleration support for NVIDIA CUDA and Apple Silicon MPS.

## Features

- **Fast Generation**: 9-step inference for quick image generation
- **Multi-GPU Support**: NVIDIA CUDA (Windows/Linux) and Apple MPS (macOS)
- **Bilingual Prompts**: Supports both Chinese and English prompts
- **Flexible Resolution**: Multiple preset aspect ratios and custom resolutions
- **Auto Device Selection**: Automatically selects best available GPU
- **Reproducible Results**: Seed support for consistent outputs

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/aicoder2048/z-image-turbo.git
cd z-image-turbo

# Install dependencies (without PyTorch)
uv sync
```

### Install PyTorch (Choose One)

**Mac (MPS):**
```bash
uv pip install torch
```

**Windows/Linux (CUDA - NVIDIA GPU):**
```bash
uv pip install torch --index-url https://download.pytorch.org/whl/cu121
```

**CPU Only:**
```bash
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Verify Installation

```bash
# Download model
uv run --no-sync z-image --download-only

# Check GPU detection
uv run --no-sync python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

> **Note**: Use `uv run --no-sync` to prevent uv from reinstalling PyTorch.

## Quick Start

```bash
# Basic usage (use --no-sync on Windows with CUDA)
uv run z-image -p "a cat floating in space"

# Chinese prompt (supports bilingual)
uv run z-image -p "一只猫在太空中漂浮"

# With aspect ratio
uv run z-image -p "mountain landscape" --ratio 16:9

# Custom resolution with seed
uv run z-image -p "portrait photo" --resolution 768x1344 --seed 42

# Generate multiple images
uv run z-image -p "sunset over ocean" -n 3
```

> **Windows CUDA Users**: Use `uv run --no-sync z-image ...` to prevent PyTorch from being reinstalled.

## Usage

```
z-image [-h] [--prompt TEXT] [--ratio RATIO] [--resolution WxH]
        [--device {auto,cuda,mps,cpu}] [--force-mps] [--seed INT] [--count N]
        [--download-only] [--model-dir DIR] [--output-dir DIR]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--prompt` | `-p` | Image generation prompt (Chinese/English) |
| `--ratio` | `-r` | Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3 |
| `--resolution` | | Custom resolution, e.g., 1024x768 (overrides --ratio) |
| `--device` | `-d` | Device: auto, cuda, mps, cpu (default: auto) |
| `--force-mps` | | [Experimental] Force MPS even if resolution exceeds limit (may crash) |
| `--seed` | `-s` | Random seed for reproducibility |
| `--count` | `-n` | Number of images to generate (default: 1) |
| `--download-only` | | Download model without generating |
| `--model-dir` | | Model cache directory (default: models) |
| `--output-dir` | | Output directory (default: output) |

### Examples

```bash
# YouTube thumbnail (16:9)
uv run z-image -p "epic fantasy landscape" --ratio 16:9

# Instagram post (1:1)
uv run z-image -p "minimalist product photo" --ratio 1:1

# Phone wallpaper (9:16)
uv run z-image -p "abstract art" --ratio 9:16

# iPhone wallpaper
uv run z-image -p "nature wallpaper" --resolution 768x1664

# High resolution (uses CPU on Mac)
uv run z-image -p "detailed cityscape" --resolution 1920x1080

# Force CPU mode
uv run z-image -p "test" --resolution 2560x1440 --device cpu
```

## Resolution Guide

### Preset Aspect Ratios (--ratio)

| Ratio | Resolution | Use Case |
|-------|------------|----------|
| 1:1 | 1024x1024 | Instagram, avatars, social media |
| 16:9 | 1344x768 | YouTube, desktop wallpaper, landscape |
| 9:16 | 768x1344 | Phone wallpaper, TikTok, Stories |
| 4:3 | 1152x896 | iPad landscape, traditional displays |
| 3:4 | 896x1152 | Posters, Pinterest |
| 3:2 | 1216x832 | Traditional photo ratio |
| 2:3 | 832x1216 | Portrait photos, book covers |

### Custom Resolutions (--resolution)

| Resolution | Ratio | Use Case |
|------------|-------|----------|
| 1024x1024 | 1:1 | Instagram posts, avatars |
| 512x512 | 1:1 | Thumbnails, icons |
| 1344x768 | 16:9 | YouTube covers, wallpapers |
| 1920x1080 | 16:9 | 1080p FHD video, desktop |
| 2560x1440 | 16:9 | 2K QHD wallpaper |
| 3840x2160 | 16:9 | 4K UHD wallpaper |
| 768x1344 | 9:16 | Phone wallpaper, TikTok |
| 768x1664 | 9:19.5 | iPhone 14/15 Pro wallpaper |

> **Note**: Resolution must be divisible by 16 (Z-Image model requirement). The tool automatically aligns to the nearest valid resolution.

## Mac MPS Resolution Limitation

### The Problem

When running on Apple Silicon Macs with MPS (Metal Performance Shaders), you may encounter this error at high resolutions:

```
[MPSNDArray initWithDevice:descriptor:] Error: total bytes of NDArray > 2**32
```

### Root Cause

This is a **known bug in PyTorch's MPS backend**, not a memory limitation:

- The MPS backend uses 32-bit integers to calculate tensor sizes
- When intermediate tensors exceed 2^32 bytes (~4GB), the operation fails
- This is NOT related to your Mac's RAM (even 64GB+ Macs are affected)
- `enable_attention_slicing()` helps but doesn't fully resolve the issue

### Resolution Limits on MPS

| Resolution | Pixels | Status |
|------------|--------|--------|
| 1024x1024 | ~1.0M | Works |
| 1344x768 | ~1.0M | Works |
| 768x1344 | ~1.0M | Works |
| 1920x1080 | ~2.1M | Fails |
| 2560x1440 | ~3.7M | Fails |

**Safe limit**: ~1.1 megapixels (approximately 1344x768 or equivalent)

### Solutions

#### 1. Auto Mode (Default)

The tool automatically switches to CPU for high resolutions:

```bash
uv run z-image -p "test" --resolution 1920x1080
# Output: Device: cpu (auto-switched for high resolution)
```

#### 2. Force CPU Mode

Explicitly use CPU for any resolution:

```bash
uv run z-image -p "test" --resolution 2560x1440 --device cpu
```

#### 3. Force MPS Mode

If you want to use MPS and the resolution is within limits:

```bash
uv run z-image -p "test" --ratio 16:9 --device mps
```

### Performance Comparison

| Device | 1024x1024 | Notes |
|--------|-----------|-------|
| MPS (M2 Max) | ~68 sec | Fast, limited resolution |
| CPU (M2 Max) | ~5-10 min | Slow, any resolution |
| CUDA (RTX 3090) | ~10 sec | Fast, any resolution |

### Power User Workarounds

For advanced users who want to experiment with MPS at higher resolutions:

#### 1. Force MPS Mode (Experimental)

Use `--force-mps` to bypass the resolution safety check:

```bash
# WARNING: May crash or produce corrupted images
uv run z-image -p "test" --resolution 1920x1080 --force-mps
```

This flag:
- Forces MPS usage even when resolution exceeds the safe limit
- May cause program crashes, system instability, or corrupted output
- Useful for testing if your specific Mac/configuration can handle higher resolutions

#### 2. PyTorch MPS Fallback Environment Variable

Enable partial CPU fallback for unsupported MPS operations:

```bash
# Set before running
export PYTORCH_ENABLE_MPS_FALLBACK=1
uv run z-image -p "test" --resolution 1920x1080 --force-mps
```

This environment variable tells PyTorch to fall back to CPU for operations that fail on MPS, potentially allowing higher resolutions to work (with reduced performance).

#### 3. Experimental Examples

```bash
# Try 1080p with force-mps (risky)
uv run z-image -p "landscape" --resolution 1920x1080 --force-mps

# Try with MPS fallback enabled
PYTORCH_ENABLE_MPS_FALLBACK=1 uv run z-image -p "test" --resolution 2560x1440 --force-mps

# Safe: use CPU for guaranteed high-res support
uv run z-image -p "4k wallpaper" --resolution 3840x2160 --device cpu
```

#### Warnings

- **Data Loss Risk**: Crashes may occur without warning
- **System Instability**: High memory pressure can affect other applications
- **No Support**: Issues encountered with `--force-mps` are expected behavior
- **Recommendation**: For production use, stick with auto mode or explicit CPU for high resolutions

### References

- [PyTorch MPS NDArray Issue #84039](https://github.com/pytorch/pytorch/issues/84039)
- [Hugging Face MPS Optimization Guide](https://huggingface.co/docs/diffusers/en/optimization/mps)
- [Stable Diffusion WebUI Discussion #5278](https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/5278)

## Output Structure

Generated images are saved to:

```
output/
  YYMMDD/
    HHMMSS_<seed>_nbp.png
    ...
```

Example: `output/251201/143052_1234567890_nbp.png`

## Model Information

### Z-Image-Turbo

- **Model**: [Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- **Size**: ~6B parameters
- **Native Resolution**: 1024x1024
- **Inference Steps**: 9 (Turbo mode)
- **Guidance Scale**: 0.0 (fixed for Turbo)

## Troubleshooting

### Black Images

If you get black images, ensure:
- Using `torch.float32` (not float16) - already configured
- MPS sync is called after generation - already configured

### Slow Generation

- Use MPS mode for resolutions under 1344x768
- Use `--ratio` presets for optimal performance
- CPU mode is significantly slower but supports any resolution

### Model Download Issues

```bash
# Clear cache and re-download
rm -rf models/
uv run z-image --download-only
```

## Generate Prompts

This project includes a prompt generation tool that uses LLM (via Ollama) to create detailed image generation prompts from templates.

### Setup

1. Copy `.env.example` to `.env` and configure your Ollama settings:
   ```bash
   # .env
   OLLAMA_URL=http://localhost:11434/v1
   OLLAMA_MODEL=dolphin3:latest
   ```

2. Create a template file at `input/prompt_template.json` (a sample is provided)

### Usage

```bash
# Interactive mode
uv run generate_prompts

# Generate 5 variations
uv run generate_prompts -n 5

# Use custom template file
uv run generate_prompts -t my_template.json

# Custom output file
uv run generate_prompts -o input/prompts/my_prompts.json
```

### Template Format

Templates use JSON format with support for random selection using `|`:

```json
{
  "subject": {
    "type": "person | animal",
    "age": "young | old",
    "expression": "smile | serious"
  },
  "clothing": {
    "top": "t-shirt | sweater",
    "bottom": "jeans | shorts"
  },
  "environment": "indoor | outdoor | beach",
  "style": "photo-realistic",
  "camera_angle": "medium shot | close-up",
  "lighting": "natural | dramatic"
}
```

### Prompt Sanitization

The module includes utilities for sanitizing prompts before image generation:

```python
from generate_prompts.generator import sanitize_prompt, is_prompt_problematic

# Check if prompt might cause issues
if is_prompt_problematic(prompt):
    print("Warning: Prompt may cause generation issues")

# Clean up problematic characters
clean_prompt = sanitize_prompt(prompt)
```

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run pytest tests/ -v

# Run with verbose output
uv run z-image -p "test" --ratio 1:1
```

## Codebase Structure

```
z-image-turbo/
├── src/
│   ├── z_image/
│   │   ├── __init__.py      # Package initialization, version info
│   │   ├── __main__.py      # Entry point for `python -m z_image`
│   │   ├── cli.py           # CLI argument parsing, aspect ratio presets
│   │   ├── generator.py     # Image generation logic, device selection
│   │   └── downloader.py    # Model download utilities
│   └── generate_prompts/
│       ├── __init__.py      # Package initialization
│       ├── __main__.py      # Entry point for `python -m generate_prompts`
│       ├── cli.py           # CLI with interactive/batch modes, variation generation
│       └── generator.py     # PydanticAI/Ollama LLM integration, prompt sanitization
├── tests/
│   ├── __init__.py
│   ├── test_cli.py              # CLI unit tests
│   └── test_generate_prompts.py # Prompt generation tests
├── input/                   # Input templates (git-ignored)
├── models/                  # Model cache directory (git-ignored)
├── output/                  # Generated images output (git-ignored)
├── ai_docs/                 # AI documentation (pydantic_ai, diffusers, etc.)
├── pyproject.toml           # Project configuration and dependencies
├── uv.lock                  # Dependency lock file
└── README.md
```

### Key Modules

| Module | Description |
|--------|-------------|
| `z_image/cli.py` | Handles command-line argument parsing, defines aspect ratio presets and resolution validation |
| `z_image/generator.py` | Core image generation using Diffusers pipeline, manages device selection (MPS/CPU) and resolution limits |
| `z_image/downloader.py` | Downloads and caches Z-Image-Turbo model from Hugging Face |
| `generate_prompts/cli.py` | Interactive/batch CLI with template variation generation (`-n` for batch mode) |
| `generate_prompts/generator.py` | PydanticAI + Ollama LLM integration, random attribute selection (`\|` syntax), prompt sanitization utilities |

## License

MIT License

## Credits

- Model: [Alibaba Tongyi-MAI](https://github.com/Tongyi-MAI/Z-Image)
- Framework: [Hugging Face Diffusers](https://github.com/huggingface/diffusers)
