"""图像生成模块 - Pipeline 加载与生成逻辑"""

from datetime import datetime
from pathlib import Path

import torch
from diffusers import ZImagePipeline
from PIL import Image

DEFAULT_OUTPUT_DIR = Path("output")


def load_pipeline(model_path: Path) -> ZImagePipeline:
    """
    加载 Z-Image-Turbo pipeline，针对 M2 Max 优化。

    Args:
        model_path: 本地模型路径

    Returns:
        ZImagePipeline 实例
    """
    pipe = ZImagePipeline.from_pretrained(
        str(model_path),
        torch_dtype=torch.float32,  # float32 避免 NaN latents 导致黑色图像
        low_cpu_mem_usage=True,
        local_files_only=True,  # 仅从本地加载
    )
    pipe.to("mps")
    return pipe


def generate_image(
    pipe: ZImagePipeline,
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    seed: int | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
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

    # MPS 同步 - 确保 GPU 操作完成后再保存图像
    torch.mps.synchronize()

    # 构建输出路径: output/YYMMDD/hhmmss_<seed>_nbp.png
    now = datetime.now()
    date_dir = output_dir / now.strftime("%y%m%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{now.strftime('%H%M%S')}_{seed}_nbp.png"
    output_path = date_dir / filename

    image.save(output_path)
    return image, seed, output_path
