"""图像生成模块 - Pipeline 加载与生成逻辑"""

import platform
from datetime import datetime
from pathlib import Path

import torch
from diffusers import ZImagePipeline
from PIL import Image

DEFAULT_OUTPUT_DIR = Path("output")

# 分辨率对齐要求 - 宽高必须是 16 的倍数 (Z-Image 模型架构要求)
RESOLUTION_ALIGNMENT = 16

# MPS (Mac Metal) 最大像素数限制
# PyTorch MPS 后端有 2^32 字节 NDArray 限制，这是已知 bug
# 经测试: 1344x768 (~1MP) 可工作, 1920x1080 (~2MP) 失败
MPS_MAX_PIXELS = 1_100_000


def align_resolution(width: int, height: int) -> tuple[int, int]:
    """
    将分辨率对齐到 16 的倍数（向下取整）。

    Args:
        width: 原始宽度
        height: 原始高度

    Returns:
        (对齐后的宽度, 对齐后的高度)
    """
    aligned_width = (width // RESOLUTION_ALIGNMENT) * RESOLUTION_ALIGNMENT
    aligned_height = (height // RESOLUTION_ALIGNMENT) * RESOLUTION_ALIGNMENT
    return aligned_width, aligned_height


def resolve_device(device: str, width: int, height: int) -> str:
    """
    解析设备选择。

    Args:
        device: 用户指定的设备 ("auto", "mps", "cpu")
        width: 图像宽度
        height: 图像高度

    Returns:
        实际使用的设备 ("mps" 或 "cpu")

    Raises:
        ValueError: 当 device="mps" 但分辨率超过 MPS 限制时
    """
    if platform.system() != "Darwin":
        return "cpu"

    total_pixels = width * height
    exceeds_mps_limit = total_pixels > MPS_MAX_PIXELS

    if device == "cpu":
        return "cpu"

    if device == "mps":
        if exceeds_mps_limit:
            raise ValueError(
                f"分辨率 {width}x{height} ({total_pixels:,} 像素) 超过 Mac MPS 限制。\n"
                f"这是 PyTorch MPS 后端的已知 bug (NDArray > 2^32 bytes)。\n"
                f"请使用 --device cpu 启用 CPU 模式，或降低分辨率。"
            )
        return "mps"

    # device == "auto"
    if exceeds_mps_limit:
        return "cpu"
    return "mps"


def load_pipeline(model_path: Path, device: str = "mps") -> tuple[ZImagePipeline, str]:
    """
    加载 Z-Image-Turbo pipeline。

    Args:
        model_path: 本地模型路径
        device: 目标设备 ("mps" 或 "cpu")

    Returns:
        (ZImagePipeline 实例, 实际使用的设备)
    """
    pipe = ZImagePipeline.from_pretrained(
        str(model_path),
        torch_dtype=torch.float32,  # float32 避免 NaN latents 导致黑色图像
        low_cpu_mem_usage=True,
        local_files_only=True,  # 仅从本地加载
    )
    pipe.to(device)

    # MPS 模式启用 attention slicing 优化
    if device == "mps":
        pipe.enable_attention_slicing(slice_size="max")

    return pipe, device


def generate_image(
    pipe: ZImagePipeline,
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    seed: int | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    device: str = "mps",
) -> tuple[Image.Image, int, Path]:
    """
    生成图像并保存到输出目录。

    Args:
        pipe: ZImagePipeline 实例
        prompt: 文本提示词
        width: 图像宽度
        height: 图像高度
        seed: 随机种子（None 则自动生成）
        output_dir: 输出目录
        device: 计算设备 ("mps" 或 "cpu")

    Returns:
        (PIL Image, seed, 保存路径)
    """
    # 处理种子
    if seed is None:
        seed = torch.randint(0, 2**32 - 1, (1,)).item()

    generator = torch.Generator(device).manual_seed(seed)

    # 生成图像
    image = pipe(
        prompt=prompt,
        height=height,
        width=width,
        num_inference_steps=9,
        guidance_scale=0.0,  # Turbo 固定为 0
        generator=generator,
    ).images[0]

    # MPS 同步 - 确保 GPU 操作完成后再保存图像
    if device == "mps":
        torch.mps.synchronize()

    # 构建输出路径: output/YYMMDD/hhmmss_<seed>_nbp.png
    now = datetime.now()
    date_dir = output_dir / now.strftime("%y%m%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{now.strftime('%H%M%S')}_{seed}_nbp.png"
    output_path = date_dir / filename

    image.save(output_path)
    return image, seed, output_path
