"""Z-Image-Turbo 命令行入口"""

from pathlib import Path

from .cli import parse_args, parse_resolution
from .downloader import download_model
from .generator import generate_image, load_pipeline


def main():
    args = parse_args()

    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)

    # 1. 下载/检查模型
    print("检查模型...")
    model_path = download_model(cache_dir=model_dir)
    print(f"模型就绪: {model_path}")

    if args.download_only:
        return

    # 2. 加载 Pipeline
    print("加载 Pipeline...")
    pipe = load_pipeline(model_path)
    print("Pipeline 已加载")

    # 3. 解析分辨率
    width, height = parse_resolution(args.ratio, args.resolution)
    print(f"分辨率: {width}x{height}")

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
        )
        print(f"已保存: {output_path}")
        print(f"种子: {used_seed}")


if __name__ == "__main__":
    main()
