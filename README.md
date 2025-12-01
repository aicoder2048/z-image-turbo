# Z-Image-Turbo

A command-line tool for text-to-image generation using Alibaba's [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) model, optimized for Apple Silicon (M1/M2/M3/M4) Macs.

## Features

- **Fast Generation**: 9-step inference for quick image generation
- **Apple Silicon Optimized**: Native MPS (Metal Performance Shaders) support
- **Bilingual Prompts**: Supports both Chinese and English prompts
- **Flexible Resolution**: Multiple preset aspect ratios and custom resolutions
- **Auto CPU Fallback**: Automatically switches to CPU for high resolutions
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

# Install dependencies
uv sync

# Download model (optional, will auto-download on first run)
uv run z-image --download-only
```

## Quick Start

```bash
# Basic usage
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

## Usage

```
z-image [-h] [--prompt TEXT] [--ratio RATIO] [--resolution WxH]
        [--device {auto,mps,cpu}] [--seed INT] [--count N]
        [--download-only] [--model-dir DIR] [--output-dir DIR]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--prompt` | `-p` | Image generation prompt (Chinese/English) |
| `--ratio` | `-r` | Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3 |
| `--resolution` | | Custom resolution, e.g., 1024x768 (overrides --ratio) |
| `--device` | `-d` | Device: auto, mps, cpu (default: auto) |
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
    HHMMSS_<seed>_nbp.png
    ...
```

Example: `output/251201/143052_1234567890_nbp.png`

## Model Information

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

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run pytest tests/ -v

# Run with verbose output
uv run z-image -p "test" --ratio 1:1
```

## License

MIT License

## Credits

- Model: [Alibaba Tongyi-MAI](https://github.com/Tongyi-MAI/Z-Image)
- Framework: [Hugging Face Diffusers](https://github.com/huggingface/diffusers)
