# Chore: 增强 --resolution 参数的帮助信息

## Chore Description
增强 `--resolution` 参数的帮助提示，包含更多分辨率选项案例，并备注每个分辨率的 Ratio（宽高比）和使用场景（如 iPhone、iPad、社交媒体等）。

目前 `--resolution` 参数只有简单提示 `自定义分辨率，如 1024x768`，需要扩展为更丰富的帮助信息，方便用户选择合适的分辨率。

## Relevant Files
Use these files to resolve the chore:

- `src/z_image/cli.py` - CLI 主模块，包含 `--resolution` 参数定义和帮助信息，需要修改 `epilog` 部分添加分辨率表格
- `tests/test_cli.py` - CLI 测试文件，验证修改后的功能正常

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: 定义常用分辨率预设表

在 `src/z_image/cli.py` 中添加常用分辨率预设常量，包含以下信息：
- 分辨率 (宽x高)
- 宽高比 (Ratio)
- 使用场景描述

常用分辨率参考：
| 分辨率 | 比例 | 场景 |
|--------|------|------|
| 1024x1024 | 1:1 | Instagram 帖子、头像 |
| 1344x768 | 16:9 | YouTube 封面、桌面壁纸 |
| 768x1344 | 9:16 | 手机壁纸、抖音/TikTok、Instagram Stories |
| 1152x896 | 4:3 | iPad、传统显示器 |
| 896x1152 | 3:4 | 竖版海报、Pinterest |
| 1216x832 | 3:2 | 传统照片比例 |
| 832x1216 | 2:3 | 竖版照片、书籍封面 |
| 1280x720 | 16:9 | 720p HD 视频 |
| 1920x1080 | 16:9 | 1080p FHD 视频 |
| 1170x2532 | 约9:19.5 | iPhone 14/15 Pro |
| 1290x2796 | 约9:19.5 | iPhone 14/15 Pro Max |
| 2048x2732 | 3:4 | iPad Pro 12.9" |

### Step 2: 更新 argparse epilog 帮助信息

修改 `parse_args()` 函数中的 `epilog` 参数，添加分辨率参考表格：
- 将常用分辨率及其使用场景以表格形式展示
- 保持原有示例，并添加更多分辨率相关示例
- 使用清晰的格式便于命令行阅读

### Step 3: 更新 --resolution 参数的帮助文本

更新 `--resolution` 参数的 `help` 文本：
- 添加更多示例分辨率
- 提示用户可查看下方表格获取更多分辨率建议

### Step 4: 运行验证命令

执行所有验证命令确保修改正确无误。

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd /Users/szou/Python/Playground/Z_Image_HF && uv run pytest tests/ -v` - 运行测试确保无回归
- `cd /Users/szou/Python/Playground/Z_Image_HF && uv run python -m z_image --help` - 验证帮助信息显示正确

## Notes
- 分辨率建议基于 SDXL 模型的推荐尺寸（接近 1024x1024 总像素数最佳）
- iPhone 等设备的实际分辨率可能过大，建议使用近似比例的较小分辨率
- 帮助文本需要保持简洁，避免过长导致命令行显示不友好
