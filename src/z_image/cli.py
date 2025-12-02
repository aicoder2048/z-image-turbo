"""命令行接口模块"""

import argparse
import json
import shlex
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
  %(prog)s -i                                     # 启动交互模式

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
        choices=["auto", "cuda", "mps", "cpu"],
        default="auto",
        help="计算设备: auto=自动选择, cuda=NVIDIA GPU, mps=Mac GPU, cpu=CPU模式",
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

    # 交互模式
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="启用交互模式：模型加载后等待用户输入，支持多次生成而无需重新加载模型",
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
    if not args.download_only and not args.interactive:
        if args.prompt and args.prompts_file:
            parser.error("--prompt/-p 和 --prompts-file/-f 不能同时使用")
        if not args.prompt and not args.prompts_file:
            parser.error("必须指定 --prompt/-p 或 --prompts-file/-f（除非使用 --download-only 或 --interactive）")

    return args


# 交互模式特殊命令
INTERACTIVE_COMMANDS = {"help", "quit", "exit", "status"}


def parse_interactive_input(input_line: str) -> dict:
    """
    解析交互模式下的用户输入。

    支持的格式:
    - "prompt text" - 直接输入 prompt（引号可选）
    - -p "prompt" -r 16:9 -n 2 - 带选项的完整命令
    - help / quit / exit / status - 特殊命令

    Args:
        input_line: 用户输入的命令行

    Returns:
        dict: 解析结果，包含以下字段:
            - command: "generate" | "help" | "quit" | "status" | "error"
            - prompt: str | None (当 command 为 "generate" 时)
            - prompts_file: str | None (当使用 -f 时)
            - ratio: str | None
            - resolution: str | None
            - count: int
            - seed: int | None
            - error: str | None (当 command 为 "error" 时)
    """
    input_line = input_line.strip()

    if not input_line:
        return {"command": "empty"}

    # 检查特殊命令
    lower_input = input_line.lower()
    if lower_input in ("quit", "exit"):
        return {"command": "quit"}
    if lower_input == "help":
        return {"command": "help"}
    if lower_input == "status":
        return {"command": "status"}

    # 默认值
    result = {
        "command": "generate",
        "prompt": None,
        "prompts_file": None,
        "ratio": "1:1",
        "resolution": None,
        "count": 1,
        "seed": None,
        "force_mps": False,
    }

    # 尝试解析为带选项的命令
    try:
        tokens = shlex.split(input_line)
    except ValueError as e:
        return {"command": "error", "error": f"解析错误: {e}"}

    if not tokens:
        return {"command": "empty"}

    # 如果第一个 token 不是选项，则将整个输入作为 prompt
    if not tokens[0].startswith("-"):
        # 整个输入作为 prompt（移除外层引号如果有的话）
        result["prompt"] = input_line.strip("\"'")
        return result

    # 解析带选项的命令
    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ("-p", "--prompt"):
            if i + 1 < len(tokens):
                result["prompt"] = tokens[i + 1]
                i += 2
            else:
                return {"command": "error", "error": "-p/--prompt 需要参数"}

        elif token in ("-r", "--ratio"):
            if i + 1 < len(tokens):
                ratio = tokens[i + 1]
                if ratio in ASPECT_RATIOS:
                    result["ratio"] = ratio
                    i += 2
                else:
                    return {"command": "error", "error": f"无效的宽高比: {ratio}，可选: {', '.join(ASPECT_RATIOS.keys())}"}
            else:
                return {"command": "error", "error": "-r/--ratio 需要参数"}

        elif token == "--resolution":
            if i + 1 < len(tokens):
                result["resolution"] = tokens[i + 1]
                i += 2
            else:
                return {"command": "error", "error": "--resolution 需要参数"}

        elif token in ("-n", "--count"):
            if i + 1 < len(tokens):
                try:
                    result["count"] = int(tokens[i + 1])
                    i += 2
                except ValueError:
                    return {"command": "error", "error": f"-n/--count 需要整数参数"}
            else:
                return {"command": "error", "error": "-n/--count 需要参数"}

        elif token in ("-s", "--seed"):
            if i + 1 < len(tokens):
                try:
                    result["seed"] = int(tokens[i + 1])
                    i += 2
                except ValueError:
                    return {"command": "error", "error": "-s/--seed 需要整数参数"}
            else:
                return {"command": "error", "error": "-s/--seed 需要参数"}

        elif token in ("-f", "--prompts-file"):
            if i + 1 < len(tokens):
                result["prompts_file"] = tokens[i + 1]
                i += 2
            else:
                return {"command": "error", "error": "-f/--prompts-file 需要参数"}

        elif token == "--force-mps":
            result["force_mps"] = True
            i += 1

        else:
            # 未知选项，可能是 prompt 的一部分
            return {"command": "error", "error": f"未知选项: {token}"}

    # 验证必须有 prompt 或 prompts_file
    if result["prompt"] is None and result["prompts_file"] is None:
        return {"command": "error", "error": "缺少 prompt，请使用 -p \"prompt\"、-f 文件 或直接输入文本"}

    # 验证 -p 和 -f 不能同时使用
    if result["prompt"] is not None and result["prompts_file"] is not None:
        return {"command": "error", "error": "-p 和 -f 不能同时使用"}

    return result


def get_interactive_help() -> str:
    """返回交互模式的帮助信息"""
    return """
交互模式帮助
============

命令格式:
  "prompt text"              直接输入 prompt 生成图像
  -p "prompt" [选项]         带选项的生成命令
  -f 文件 [选项]             从文件批量生成

可用选项:
  -p, --prompt TEXT          图像生成提示词（支持中英文）
  -f, --prompts-file FILE    从文件读取 prompts（JSON 或 TXT）
  -r, --ratio RATIO          宽高比: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3
  --resolution WxH           自定义分辨率，如 1024x768
  -n, --count N              每个 prompt 生成数量（默认: 1）
  -s, --seed INT             随机种子
  --force-mps                强制使用 MPS（即使分辨率超限，可能崩溃）

特殊命令:
  help                       显示此帮助信息
  status                     显示当前设置
  quit / exit                退出程序

示例:
  一只猫在太空中漂浮
  -p "山水风景" -r 16:9
  -p "人像照片" -n 3 -s 42
  -f prompts.json -r 16:9
  -f prompts.txt -n 2
"""
