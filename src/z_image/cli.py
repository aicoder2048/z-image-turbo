"""命令行接口模块"""

import argparse

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


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
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

    # 必需参数（download-only 模式除外）
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        default=None,
        metavar="文本",
        help="图像生成提示词（支持中英文）",
    )

    # 分辨率相关
    parser.add_argument(
        "--ratio",
        "-r",
        type=str,
        choices=list(ASPECT_RATIOS.keys()),
        default="1:1",
        metavar="比例",
        help="宽高比，可选: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3（默认: 1:1）",
    )
    parser.add_argument(
        "--resolution",
        type=str,
        metavar="宽x高",
        help="自定义分辨率，如 1024x768（优先于 --ratio）",
    )

    # 生成控制
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=None,
        metavar="整数",
        help="随机种子，用于复现结果（默认: 随机）",
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=1,
        metavar="数量",
        help="生成图像数量（默认: 1）",
    )

    # 模型管理
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="仅下载模型，不生成图像",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models",
        metavar="目录",
        help="模型缓存目录（默认: models）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        metavar="目录",
        help="输出目录（默认: output）",
    )

    args = parser.parse_args()

    # 验证：非 download-only 模式下 prompt 必需
    if not args.download_only and not args.prompt:
        parser.error("--prompt/-p 是必需的（除非使用 --download-only）")

    return args
