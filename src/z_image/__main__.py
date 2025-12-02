"""Z-Image-Turbo 命令行入口"""

import sys
from pathlib import Path

from generate_prompts.generator import is_prompt_problematic, sanitize_prompt

from .cli import (
    get_interactive_help,
    load_prompts,
    parse_args,
    parse_interactive_input,
    parse_resolution,
)
from .downloader import download_model
from .generator import (
    MPS_MAX_PIXELS,
    align_resolution,
    generate_image,
    load_pipeline,
    resolve_device,
)


def generate_images(
    pipe,
    prompts: list[str],
    width: int,
    height: int,
    count: int,
    seed: int | None,
    output_dir: Path,
    device: str,
) -> int:
    """
    生成图像的核心函数。

    Args:
        pipe: ZImagePipeline 实例
        prompts: prompt 列表
        width: 图像宽度
        height: 图像高度
        count: 每个 prompt 生成的数量
        seed: 随机种子
        output_dir: 输出目录
        device: 计算设备

    Returns:
        成功生成的图像数量
    """
    total_images = len(prompts) * count
    completed_images = 0

    for prompt_idx, original_prompt in enumerate(prompts):
        # Sanitize prompt 以移除可能导致生成问题的特殊字符
        prompt = sanitize_prompt(original_prompt)

        # 检查 sanitize 后的 prompt 是否有效
        if not prompt or prompt.strip() == "":
            print(f"\n[跳过] Prompt {prompt_idx + 1}: sanitize 后为空")
            continue

        if is_prompt_problematic(prompt):
            print(f"\n[警告] Prompt {prompt_idx + 1} 可能包含问题字符，尝试继续生成...")

        for i in range(count):
            image_num = completed_images + 1
            current_seed = seed
            if seed is not None:
                # 每张图使用不同的种子
                current_seed = seed + image_num - 1

            # 显示进度
            if len(prompts) > 1:
                print(f"\n生成图像 [Prompt {prompt_idx + 1}/{len(prompts)}, Image {i + 1}/{count}] ({image_num}/{total_images})...")
                # 显示 prompt 前 50 个字符
                prompt_preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
                print(f"Prompt: {prompt_preview}")
            else:
                print(f"\n生成图像 [{i + 1}/{count}]...")

            image, used_seed, output_path = generate_image(
                pipe=pipe,
                prompt=prompt,
                width=width,
                height=height,
                seed=current_seed,
                output_dir=output_dir,
                device=device,
            )
            completed_images += 1
            print(f"已保存: {output_path}")
            print(f"种子: {used_seed}")

    return completed_images


def print_status(device: str, width: int, height: int, output_dir: Path):
    """打印当前状态信息"""
    print(f"\n当前设置:")
    print(f"  设备: {device}")
    print(f"  默认分辨率: {width}x{height}")
    print(f"  输出目录: {output_dir}")
    print()


def interactive_loop(pipe, device: str, output_dir: Path, default_width: int, default_height: int):
    """
    交互式命令循环。

    Args:
        pipe: ZImagePipeline 实例
        device: 计算设备
        output_dir: 输出目录
        default_width: 默认宽度
        default_height: 默认高度
    """
    print("\n" + "=" * 50)
    print("进入交互模式")
    print("=" * 50)

    while True:
        try:
            print("\n输入 'help' 查看帮助，'quit' 退出")
            user_input = input("z-image> ").strip()

            if not user_input:
                continue

            # 解析输入
            parsed = parse_interactive_input(user_input)
            command = parsed.get("command")

            if command == "empty":
                continue

            elif command == "quit":
                print("退出...")
                break

            elif command == "help":
                print(get_interactive_help())

            elif command == "status":
                print_status(device, default_width, default_height, output_dir)

            elif command == "error":
                print(f"错误: {parsed.get('error')}")

            elif command == "generate":
                # 解析分辨率
                width, height = parse_resolution(
                    parsed.get("ratio"),
                    parsed.get("resolution")
                )

                # 对齐分辨率
                aligned_width, aligned_height = align_resolution(width, height)
                if (aligned_width, aligned_height) != (width, height):
                    print(f"分辨率已对齐: {width}x{height} -> {aligned_width}x{aligned_height}")
                    width, height = aligned_width, aligned_height

                # 检查 MPS 分辨率限制
                total_pixels = width * height
                force_mps = parsed.get("force_mps", False)

                if device == "mps" and total_pixels > MPS_MAX_PIXELS:
                    if force_mps:
                        print(f"\n[WARNING] --force-mps 已启用，分辨率超过 MPS 安全限制")
                        print(f"  当前: {width}x{height} ({total_pixels:,} 像素)")
                        print(f"  限制: ~{MPS_MAX_PIXELS:,} 像素")
                        print("  可能导致程序崩溃或系统不稳定\n")
                    else:
                        print(f"\n[错误] 分辨率 {width}x{height} ({total_pixels:,} 像素) 超过 MPS 限制")
                        print(f"  MPS 安全限制: ~{MPS_MAX_PIXELS:,} 像素")
                        print("  解决方案:")
                        print("    1. 使用较低分辨率（如 1344x768）")
                        print("    2. 添加 --force-mps 强制尝试（可能崩溃）")
                        continue

                # 获取 prompts（从 -p 或 -f）
                prompts_file = parsed.get("prompts_file")
                if prompts_file:
                    try:
                        prompts_path = Path(prompts_file)
                        if not prompts_path.exists():
                            print(f"错误: 文件不存在: {prompts_file}")
                            continue
                        prompts = load_prompts(prompts_path)
                        if not prompts:
                            print("错误: 文件中没有有效的 prompts")
                            continue
                        print(f"已加载 {len(prompts)} 个 prompts")
                    except ValueError as e:
                        print(f"错误: {e}")
                        continue
                else:
                    prompts = [parsed["prompt"]]

                # 生成图像
                try:
                    generate_images(
                        pipe=pipe,
                        prompts=prompts,
                        width=width,
                        height=height,
                        count=parsed.get("count", 1),
                        seed=parsed.get("seed"),
                        output_dir=output_dir,
                        device=device,
                    )
                except KeyboardInterrupt:
                    print("\n生成被中断")

        except KeyboardInterrupt:
            print("\n(输入 'quit' 退出程序)")
            continue

        except EOFError:
            print("\n退出...")
            break


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
    device = resolve_device(args.device, width, height, force_mps=args.force_mps)

    # 显示分辨率和设备信息
    print(f"分辨率: {width}x{height}")

    # 构建设备状态信息
    device_info = f"设备: {device}"
    if device == "cuda":
        import torch
        gpu_name = torch.cuda.get_device_name(0)
        device_info += f" ({gpu_name})"
    elif args.force_mps and device == "mps":
        device_info += " (--force-mps 已启用)"
    elif args.device == "auto" and device == "cpu":
        device_info += " (无 GPU 可用)"
    print(device_info)

    # MPS 特定警告信息（CUDA 没有分辨率限制）
    total_pixels = width * height
    if device == "mps" or (args.device == "auto" and device == "cpu"):
        if args.device == "auto" and device == "cpu" and total_pixels > MPS_MAX_PIXELS:
            print("\n[WARNING] CPU 模式已自动启用")
            print(f"  分辨率 {width}x{height} ({total_pixels:,} 像素) 超过 MPS 安全限制 ({MPS_MAX_PIXELS:,} 像素)")
            print("  CPU 模式较慢但支持任意分辨率")
            print("  如需强制使用 MPS，可添加 --force-mps（可能导致崩溃）\n")

        if args.force_mps and total_pixels > MPS_MAX_PIXELS:
            print("\n[WARNING] --force-mps 已启用，分辨率超过 MPS 安全限制")
            print(f"  当前: {width}x{height} ({total_pixels:,} 像素)")
            print(f"  限制: ~{MPS_MAX_PIXELS:,} 像素")
            print("  这是实验性功能，可能导致程序崩溃或系统不稳定\n")

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

    # 4. 根据模式执行
    if args.interactive:
        # 交互模式
        interactive_loop(pipe, device, output_dir, width, height)
    else:
        # 单次运行模式
        # 加载 prompts
        if args.prompts_file:
            prompts_file = Path(args.prompts_file)
            print(f"从文件加载 prompts: {prompts_file}")
            prompts = load_prompts(prompts_file)
            if not prompts:
                print("错误: 文件中没有有效的 prompts")
                return
            print(f"已加载 {len(prompts)} 个 prompts")
        else:
            prompts = [args.prompt]

        total_images = len(prompts) * args.count

        try:
            completed = generate_images(
                pipe=pipe,
                prompts=prompts,
                width=width,
                height=height,
                count=args.count,
                seed=args.seed,
                output_dir=output_dir,
                device=device,
            )
        except KeyboardInterrupt:
            print("\n")
            print("用户中断，正在退出...")
            # 注意：这里无法获取 completed_images，因为它在 generate_images 内部
            sys.exit(0)


if __name__ == "__main__":
    main()
