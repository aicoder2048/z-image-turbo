"""Z-Image-Turbo 命令行入口"""

from pathlib import Path

from .cli import parse_args, parse_resolution
from .downloader import download_model
from .generator import (
    align_resolution,
    generate_image,
    load_pipeline,
    resolve_device,
)


def main():
    args = parse_args()

    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)

    # 1. 解析并验证分辨率（在加载模型前检查，避免浪费时间）
    width, height = parse_resolution(args.ratio, args.resolution)

    # 对齐到 16 的倍数 (Z-Image 模型架构要求)
    aligned_width, aligned_height = align_resolution(width, height)
    if (aligned_width, aligned_height) != (width, height):
        print(f"分辨率已对齐: {width}x{height} -> {aligned_width}x{aligned_height} (必须是 16 的倍数)")
        width, height = aligned_width, aligned_height

    # 确定使用的设备
    device = resolve_device(args.device, width, height)

    print(f"分辨率: {width}x{height}")
    print(f"设备: {device}" + (" (高分辨率自动切换)" if args.device == "auto" and device == "cpu" else ""))

    # 2. 下载/检查模型
    print("检查模型...")
    model_path = download_model(cache_dir=model_dir)
    print(f"模型就绪: {model_path}")

    if args.download_only:
        return

    # 3. 加载 Pipeline
    print("加载 Pipeline...")
    pipe, device = load_pipeline(model_path, device=device)
    print("Pipeline 已加载")

    # 4. 生成图像
    for i in range(args.count):
        seed = args.seed
        if args.count > 1 and args.seed is not None:
            seed = args.seed + i  # 多图时递增种子

        print(f"\n生成图像 [{i + 1}/{args.count}]...")
        image, used_seed, output_path = generate_image(
            pipe=pipe,
            prompt=args.prompt,
            width=width,
            height=height,
            seed=seed,
            output_dir=output_dir,
            device=device,
        )
        print(f"已保存: {output_path}")
        print(f"种子: {used_seed}")


if __name__ == "__main__":
    main()
