"""命令行接口模块"""

import argparse
import json
from pathlib import Path

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

# 常用分辨率参考表 (分辨率, 比例, 使用场景)
RESOLUTION_PRESETS = [
    # 正方形
    ("1024x1024", "1:1", "Instagram 帖子、头像、社交媒体图标"),
    ("512x512", "1:1", "缩略图、小图标"),
    ("2048x2048", "1:1", "2K 正方形、高清头像"),
    # 横向 (Landscape)
    ("1344x768", "16:9", "YouTube 封面、桌面壁纸、横屏视频"),
    ("1280x720", "16:9", "720p HD 视频封面"),
    ("1920x1080", "16:9", "1080p FHD 视频、桌面壁纸"),
    ("2560x1440", "16:9", "2K QHD 壁纸、高端显示器"),
    ("3840x2160", "16:9", "4K UHD 壁纸、电视背景"),
    ("2048x1080", "17:9", "DCI 2K 电影标准"),
    ("4096x2160", "17:9", "DCI 4K 电影标准"),
    ("1152x896", "4:3", "iPad 横屏、传统显示器"),
    ("1216x832", "3:2", "传统照片比例、数码相机"),
    # 纵向 (Portrait)
    ("768x1344", "9:16", "手机壁纸、抖音/TikTok、Instagram Stories/Reels"),
    ("896x1152", "3:4", "竖版海报、Pinterest"),
    ("832x1216", "2:3", "竖版照片、书籍封面"),
    ("720x1280", "9:16", "手机壁纸 (720p)"),
    ("1080x1920", "9:16", "1080p 竖屏视频"),
    ("1440x2560", "9:16", "2K QHD 竖屏壁纸"),
    ("2160x3840", "9:16", "4K UHD 竖屏壁纸"),
    # 设备专用 (近似比例，适合 SDXL)
    ("768x1664", "9:19.5", "iPhone 14/15 Pro 壁纸 (近似)"),
    ("768x1024", "3:4", "iPad 竖屏"),
    ("1024x768", "4:3", "iPad 横屏 (紧凑)"),
]


def load_prompts_from_json(file_path: Path) -> list[str]:
    """
    从 JSON 文件加载 prompts。

    期望格式: [{"description": "prompt1", ...}, {"description": "prompt2", ...}]

    Args:
        file_path: JSON 文件路径

    Returns:
        提取的 description 字符串列表
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    prompts = []
    for i, item in enumerate(data):
        if isinstance(item, dict) and "description" in item:
            prompts.append(item["description"])
        else:
            print(f"警告: 跳过第 {i + 1} 项，缺少 'description' 字段")

    return prompts


def load_prompts_from_text(file_path: Path) -> list[str]:
    """
    从文本文件加载 prompts（每行一个）。

    Args:
        file_path: 文本文件路径

    Returns:
        非空行的列表
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return [line.strip() for line in lines if line.strip()]


def load_prompts(file_path: Path) -> list[str]:
    """
    根据文件扩展名加载 prompts。

    Args:
        file_path: 文件路径 (.json 或 .txt)

    Returns:
        prompts 列表

    Raises:
        ValueError: 不支持的文件扩展名
    """
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        return load_prompts_from_json(file_path)
    elif suffix == ".txt":
        return load_prompts_from_text(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {suffix}（仅支持 .json 和 .txt）")


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
  %(prog)s -f input/prompts/prompts.json          # 从 JSON 文件批量生成
  %(prog)s -f prompts.txt -n 2                    # 每个 prompt 生成 2 张

常用分辨率参考:
  分辨率        比例      使用场景
  ──────────────────────────────────────────────────────────
  1024x1024    1:1       Instagram 帖子、头像、社交媒体图标
  512x512      1:1       缩略图、小图标
  2048x2048    1:1       2K 正方形、高清头像
  ──────────────────────────────────────────────────────────
  1344x768     16:9      YouTube 封面、桌面壁纸、横屏视频
  1280x720     16:9      720p HD 视频封面
  1920x1080    16:9      1080p FHD 视频、桌面壁纸
  2560x1440    16:9      2K QHD 壁纸、高端显示器
  3840x2160    16:9      4K UHD 壁纸、电视背景
  2048x1080    17:9      DCI 2K 电影标准
  4096x2160    17:9      DCI 4K 电影标准
  1152x896     4:3       iPad 横屏、传统显示器
  1216x832     3:2       传统照片比例、数码相机
  1024x768     4:3       iPad 横屏 (紧凑)
  ──────────────────────────────────────────────────────────
  768x1344     9:16      手机壁纸、抖音/TikTok、Instagram Stories
  896x1152     3:4       竖版海报、Pinterest
  832x1216     2:3       竖版照片、书籍封面
  720x1280     9:16      手机壁纸 (720p)
  1080x1920    9:16      1080p 竖屏视频
  1440x2560    9:16      2K QHD 竖屏壁纸
  2160x3840    9:16      4K UHD 竖屏壁纸
  768x1664     9:19.5    iPhone 14/15 Pro 壁纸 (近似)
  768x1024     3:4       iPad 竖屏

提示:
  - 分辨率必须是 16 的倍数 (Z-Image 模型要求)，程序会自动对齐
  - Mac MPS 限制: 最大约 1344x768，超过此限制自动切换到 CPU 模式
  - CPU 模式较慢但支持任意分辨率，可用 --device cpu 强制使用
  - 2K/4K 分辨率建议使用 CUDA GPU 或耐心等待 CPU 生成
        """,
    )

    # Prompt 输入（二选一）
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        default=None,
        metavar="文本",
        help="图像生成提示词（支持中英文），与 -f 互斥",
    )
    parser.add_argument(
        "--prompts-file",
        "-f",
        type=str,
        default=None,
        metavar="文件",
        help="从文件读取 prompts：JSON 文件提取 'description' 字段，TXT 文件每行一个 prompt（与 -p 互斥）",
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
        help="自定义分辨率，如 1024x768、768x1344、1920x1080（优先于 --ratio，详见下方分辨率表）",
    )

    # 设备选择
    parser.add_argument(
        "--device",
        "-d",
        type=str,
        choices=["auto", "mps", "cpu"],
        default="auto",
        help="计算设备: auto=自动选择, mps=GPU加速, cpu=CPU模式(慢但支持高分辨率)",
    )
    parser.add_argument(
        "--force-mps",
        action="store_true",
        help="[实验性] 强制使用 MPS 即使分辨率超过限制（可能导致崩溃）",
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

    # 验证 prompt 输入
    if not args.download_only:
        if args.prompt and args.prompts_file:
            parser.error("--prompt/-p 和 --prompts-file/-f 不能同时使用")
        if not args.prompt and not args.prompts_file:
            parser.error("必须指定 --prompt/-p 或 --prompts-file/-f（除非使用 --download-only）")

    return args
