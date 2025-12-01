# Z-Image-Turbo 图像生成器实现方案

## 1. 问题陈述与目标

### 需求概要
在 MacBook Pro (Apple M2 Max) 上构建一个基于 Z-Image-Turbo 模型的命令行图像生成器，具备以下功能：

1. **模型管理**：支持显式下载模型到指定目录 (`models/`)，带进度显示和断点续传
2. **图像生成**：使用 Z-Image-Turbo 进行文生图
3. **输出管理**：按日期组织输出目录，文件名包含时间戳和种子值
4. **命令行接口**：支持 `--prompt`, `--ratio`, `--resolution` 等参数

### 成功标准
- [ ] 模型可下载到 `models/` 目录，支持断点续传
- [ ] 下载过程显示进度条
- [ ] 生成的图像保存到 `output/YYMMDD/hhmmss_<seed>_nbp.png`
- [ ] 支持常用命令行参数
- [ ] 在 M2 Max 上稳定运行，使用 MPS 加速

---

## 2. 技术架构

### 2.1 目录结构

```
Z_Image_HF/
├── src/                 # SRC_DIR - 源代码目录
│   └── z_image/         # 包目录
│       ├── __init__.py
│       ├── __main__.py  # 入口文件 (uv run z-image)
│       ├── cli.py       # 命令行解析
│       ├── generator.py # 图像生成逻辑
│       └── downloader.py # 模型下载逻辑
├── tests/               # 测试目录
│   └── test_cli.py
├── models/              # MODELS_DIR - 模型缓存目录
├── output/              # OUTPUT_DIR - 生成图像目录
│   └── 250101/          # 日期子目录 (YYMMDD)
│       └── 143052_42_nbp.png
├── pyproject.toml       # uv 项目配置
├── uv.lock              # uv 锁定文件
└── specs/
```

### 2.2 uv 项目配置

使用 `uv` 作为包管理器和运行工具。

**pyproject.toml**:

```toml
[project]
name = "z-image"
version = "0.1.0"
description = "Z-Image-Turbo 图像生成器"
requires-python = ">=3.11"
dependencies = [
    "torch>=2.1",
    "diffusers>=0.31.0",
    "transformers",
    "accelerate",
    "safetensors",
    "huggingface-hub>=0.20.0",
    "tqdm",
]

[project.scripts]
z-image = "z_image.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/z_image"]
```

**依赖管理命令**:

```bash
# 初始化项目（如已有 pyproject.toml 则跳过）
uv init

# 添加依赖
uv add torch diffusers transformers accelerate safetensors huggingface-hub tqdm

# 同步依赖
uv sync

# 运行项目
uv run z-image --prompt "A cat"
# 或
uv run python -m z_image --prompt "A cat"
```

### 2.3 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| Pipeline | `ZImagePipeline` | Z-Image-Turbo 官方支持 |
| dtype | `torch.float16` | M2 Max 不支持 bfloat16 |
| device | `mps` | Apple Silicon GPU 加速 |
| 下载库 | `huggingface_hub` | 原生支持断点续传和进度显示 |
| CLI | `argparse` | 标准库，无额外依赖 |

---

## 3. 实现细节

### 3.1 模型下载模块

**文件**: `src/z_image/downloader.py`

使用 `huggingface_hub.snapshot_download()` 实现断点续传：

```python
# src/z_image/downloader.py
from huggingface_hub import snapshot_download
from pathlib import Path

MODELS_DIR = Path("models")
MODEL_ID = "Tongyi-MAI/Z-Image-Turbo"

def download_model(model_id: str = MODEL_ID, cache_dir: Path = MODELS_DIR) -> Path:
    """
    下载模型到指定目录，支持断点续传和进度显示。

    Returns:
        本地模型路径
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    local_path = snapshot_download(
        repo_id=model_id,
        cache_dir=str(cache_dir),
        resume_download=True,  # 断点续传
        # tqdm 进度条默认启用
    )
    return Path(local_path)
```

**关键点**：
- `resume_download=True` 启用断点续传
- `huggingface_hub` 默认使用 tqdm 显示下载进度
- 模型会缓存到 `models/hub/models--Tongyi-MAI--Z-Image-Turbo/`

### 3.2 Pipeline 初始化

**文件**: `src/z_image/generator.py`

```python
# src/z_image/generator.py
import torch
from diffusers import ZImagePipeline

def load_pipeline(model_path: Path) -> ZImagePipeline:
    """
    加载 Z-Image-Turbo pipeline，针对 M2 Max 优化。
    """
    pipe = ZImagePipeline.from_pretrained(
        str(model_path),
        torch_dtype=torch.float16,  # M2 Max 使用 float16
        low_cpu_mem_usage=True,
        local_files_only=True,  # 仅从本地加载
    )
    pipe.to("mps")
    return pipe
```

### 3.3 图像生成模块

**文件**: `src/z_image/generator.py` (续)

```python
# src/z_image/generator.py (续)
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")

def generate_image(
    pipe: ZImagePipeline,
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    seed: int | None = None,
) -> tuple[Image.Image, int, Path]:
    """
    生成图像并保存到输出目录。

    Returns:
        (PIL Image, seed, 保存路径)
    """
    # 处理种子
    if seed is None:
        seed = torch.randint(0, 2**32 - 1, (1,)).item()

    generator = torch.Generator("mps").manual_seed(seed)

    # 生成图像
    image = pipe(
        prompt=prompt,
        height=height,
        width=width,
        num_inference_steps=9,
        guidance_scale=0.0,  # Turbo 固定为 0
        generator=generator,
    ).images[0]

    # 构建输出路径: output/YYMMDD/hhmmss_<seed>_nbp.png
    now = datetime.now()
    date_dir = OUTPUT_DIR / now.strftime("%y%m%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{now.strftime('%H%M%S')}_{seed}_nbp.png"
    output_path = date_dir / filename

    image.save(output_path)
    return image, seed, output_path
```

### 3.4 宽高比与分辨率处理

**文件**: `src/z_image/cli.py`

```python
# src/z_image/cli.py
# 预设宽高比
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:3": (1152, 896),
    "3:4": (896, 1152),
    "3:2": (1216, 832),
    "2:3": (832, 1216),
}

def parse_resolution(ratio: str | None, resolution: str | None) -> tuple[int, int]:
    """
    解析分辨率参数。

    优先级: resolution > ratio > 默认 1:1

    Args:
        ratio: 宽高比字符串，如 "16:9"
        resolution: 分辨率字符串，如 "1024x768"

    Returns:
        (width, height)
    """
    if resolution:
        w, h = resolution.lower().split("x")
        return int(w), int(h)

    if ratio and ratio in ASPECT_RATIOS:
        return ASPECT_RATIOS[ratio]

    return (1024, 1024)  # 默认
```

### 3.5 命令行接口

**文件**: `src/z_image/cli.py` (续)

```python
# src/z_image/cli.py (续)
import argparse

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Z-Image-Turbo 图像生成器 - 基于阿里通义 Z-Image 模型的文生图工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -p "一只猫在太空中漂浮"
  %(prog)s -p "山水风景" --ratio 16:9
  %(prog)s -p "人像照片" --resolution 768x1344 --seed 42
        """,
    )

    # 必需参数
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        required=True,
        metavar="文本",
        help="图像生成提示词（支持中英文）"
    )

    # 分辨率相关
    parser.add_argument(
        "--ratio", "-r",
        type=str,
        choices=list(ASPECT_RATIOS.keys()),
        default="1:1",
        metavar="比例",
        help="宽高比，可选: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3（默认: 1:1）"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        metavar="宽x高",
        help="自定义分辨率，如 1024x768（优先于 --ratio）"
    )

    # 生成控制
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        metavar="整数",
        help="随机种子，用于复现结果（默认: 随机）"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        metavar="数量",
        help="生成图像数量（默认: 1）"
    )

    # 模型管理
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="仅下载模型，不生成图像"
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models",
        metavar="目录",
        help="模型缓存目录（默认: models）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        metavar="目录",
        help="输出目录（默认: output）"
    )

    return parser.parse_args()
```

### 3.6 主程序流程

**文件**: `src/z_image/__main__.py`

```python
# src/z_image/__main__.py
from pathlib import Path
from .cli import parse_args, parse_resolution, ASPECT_RATIOS
from .downloader import download_model, MODELS_DIR
from .generator import load_pipeline, generate_image, OUTPUT_DIR

def main():
    args = parse_args()

    # 更新全局目录配置
    global MODELS_DIR, OUTPUT_DIR
    MODELS_DIR = Path(args.model_dir)
    OUTPUT_DIR = Path(args.output_dir)

    # 1. 下载/检查模型
    print("📦 检查模型...")
    model_path = download_model(cache_dir=MODELS_DIR)
    print(f"✅ 模型就绪: {model_path}")

    if args.download_only:
        return

    # 2. 加载 Pipeline
    print("🚀 加载 Pipeline...")
    pipe = load_pipeline(model_path)
    print("✅ Pipeline 已加载")

    # 3. 解析分辨率
    width, height = parse_resolution(args.ratio, args.resolution)
    print(f"📐 分辨率: {width}x{height}")

    # 4. 生成图像
    for i in range(args.count):
        seed = args.seed if args.seed is not None else None
        if args.count > 1 and args.seed is not None:
            seed = args.seed + i  # 多图时递增种子

        print(f"\n🎨 生成图像 [{i+1}/{args.count}]...")
        image, used_seed, output_path = generate_image(
            pipe=pipe,
            prompt=args.prompt,
            width=width,
            height=height,
            seed=seed,
        )
        print(f"✅ 已保存: {output_path}")
        print(f"   种子: {used_seed}")

if __name__ == "__main__":
    main()
```

---

## 4. 使用示例

### 安装依赖

```bash
# 同步项目依赖
uv sync
```

### 基本用法

```bash
# 生成单张图像
uv run z-image --prompt "一只猫在太空中漂浮"

# 指定宽高比
uv run z-image --prompt "山水风景画" --ratio 16:9

# 自定义分辨率
uv run z-image --prompt "古装美女肖像" --resolution 768x1344

# 指定种子（可复现结果）
uv run z-image --prompt "机器人" --seed 42

# 批量生成（种子自动递增）
uv run z-image --prompt "抽象艺术" --count 5 --seed 100

# 仅下载模型（不生成图像）
uv run z-image --download-only

# 查看帮助
uv run z-image --help

# 也可以用 python -m 方式运行
uv run python -m z_image --prompt "一只可爱的猫咪"
```

### 输出示例

```
📦 检查模型...
Downloading (…)model.safetensors: 100%|████████| 12.5G/12.5G [10:23<00:00]
✅ 模型就绪: models/hub/models--Tongyi-MAI--Z-Image-Turbo/snapshots/abc123

🚀 加载 Pipeline...
✅ Pipeline 已加载
📐 分辨率: 1024x1024

🎨 生成图像 [1/1]...
✅ 已保存: output/250130/143052_42_nbp.png
   种子: 42
```

---

## 5. 潜在问题与解决方案

### 5.1 MPS 内存不足

**问题**：生成大分辨率图像时可能 OOM

**解决**：
```python
pipe.enable_vae_slicing()
```

### 5.2 首次下载中断

**问题**：网络不稳定导致下载失败

**解决**：`resume_download=True` 已启用断点续传，重新运行即可继续

### 5.3 dtype 不匹配

**问题**：M2 Max 不支持 bfloat16

**解决**：强制使用 `torch.float16`

### 5.4 模型路径问题

**问题**：`snapshot_download` 返回的路径包含 hash

**解决**：使用返回的完整路径，或通过 `local_dir` 参数指定平坦目录结构

---

## 6. 测试策略

### 单元测试

**文件**: `tests/test_cli.py`

```python
# tests/test_cli.py
from z_image.cli import parse_resolution

def test_parse_resolution():
    assert parse_resolution(None, "1024x768") == (1024, 768)
    assert parse_resolution("16:9", None) == (1344, 768)
    assert parse_resolution(None, None) == (1024, 1024)

def test_output_path_format():
    # 验证文件名格式: hhmmss_<seed>_nbp.png
    import re
    pattern = r"^\d{6}_\d+_nbp\.png$"
    assert re.match(pattern, "143052_42_nbp.png")
```

### 集成测试

1. 运行 `--download-only` 验证模型下载
2. 生成单张图像，检查输出路径格式
3. 批量生成，验证种子递增逻辑
4. 断网后重连，验证断点续传

---

## 7. 实现步骤清单

### 项目初始化
1. [ ] 更新 `pyproject.toml`，配置 uv + src layout
2. [ ] 创建 `src/z_image/` 目录结构
3. [ ] 运行 `uv sync` 安装依赖

### 核心模块实现
4. [ ] 实现 `src/z_image/downloader.py` - `download_model()` 函数
5. [ ] 实现 `src/z_image/generator.py` - `load_pipeline()`, `generate_image()` 函数
6. [ ] 实现 `src/z_image/cli.py` - `parse_args()`, `parse_resolution()` 函数
7. [ ] 实现 `src/z_image/__main__.py` - `main()` 入口

### 测试验证
8. [ ] `uv run z-image --download-only` 验证模型下载与断点续传
9. [ ] `uv run z-image --prompt "test"` 测试图像生成与保存
10. [ ] 测试各命令行参数组合 (`--ratio`, `--resolution`, `--seed`, `--count`)

---

## 8. 注意事项

- **Z-Image-Turbo 模型较大**（约 12GB），首次下载需要较长时间
- **MPS 不支持 FlashAttention**，无需配置 attention backend
- **guidance_scale 必须为 0.0**，这是 Turbo 模型的硬性要求
- **推理步数固定为 9**，不建议修改
