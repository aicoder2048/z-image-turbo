# Feature: Interactive Mode (REPL)

## Feature Description
添加交互式模式（REPL - Read-Eval-Print Loop），让用户在模型加载后可以持续输入新的生成命令，而无需重新启动程序和重新加载模型。这将大大节省时间，因为 Z-Image-Turbo 模型约 6B 参数，加载需要较长时间。

用户可以通过新的 `--interactive` 或 `-i` 标志启动交互模式，或者在不带 prompt 参数启动时自动进入交互模式。

## User Story
As a **图像生成用户**
I want to **在模型加载后持续生成多张图像而无需重启程序**
So that **节省每次重新加载模型的时间（通常需要 10-30 秒）**

## Problem Statement
当前 z-image CLI 在生成图像后立即退出。如果用户想要生成另一张图像，必须重新运行命令，这意味着：
1. 每次都要重新加载 ~6B 参数的模型（耗时 10-30 秒）
2. 频繁生成时浪费大量时间在模型加载上
3. 用户体验不佳，特别是在迭代创作时

## Solution Statement
实现交互式模式（REPL），在模型加载完成后进入命令循环：
1. 添加 `--interactive` / `-i` 标志启用交互模式
2. 交互模式下显示 `z-image> ` 提示符等待用户输入
3. 支持所有现有 CLI 选项（如 `-p`, `-r`, `-n`, `-s` 等）
4. 支持特殊命令：`help`, `quit`/`exit`, `status`
5. 保持现有的单次运行模式作为默认行为

## Relevant Files
Use these files to implement the feature:

- `src/z_image/__main__.py` - 主入口文件，需要添加交互式循环逻辑
- `src/z_image/cli.py` - CLI 参数解析，需要添加 `--interactive` 参数和交互式命令解析器
- `tests/test_cli.py` - 测试文件，需要添加交互模式相关测试

## Implementation Plan

### Phase 1: Foundation
1. 在 `cli.py` 中添加 `--interactive` / `-i` 参数
2. 创建 `parse_interactive_input()` 函数解析交互式输入
3. 修改 prompt 验证逻辑，允许交互模式下不带 prompt 启动

### Phase 2: Core Implementation
1. 在 `__main__.py` 中重构代码，分离模型加载和图像生成逻辑
2. 实现 REPL 循环，包含：
   - 命令解析
   - 参数验证
   - 图像生成
   - 错误处理
3. 实现特殊命令 (`help`, `quit`, `status`)

### Phase 3: Integration
1. 确保 Ctrl+C 在交互模式下行为正确（中断当前生成但不退出程序）
2. 保持现有单次运行模式完全兼容
3. 添加友好的提示信息和帮助文档

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: 添加 `--interactive` CLI 参数

在 `src/z_image/cli.py` 中：

- 在 `parse_args()` 函数中添加 `--interactive` / `-i` 参数
- 修改 prompt 验证逻辑：当 `--interactive` 启用时，不要求必须指定 prompt
- 更新帮助文档说明交互模式

```python
parser.add_argument(
    "--interactive",
    "-i",
    action="store_true",
    help="启用交互模式：模型加载后等待用户输入，支持多次生成",
)
```

### Step 2: 创建交互式命令解析函数

在 `src/z_image/cli.py` 中添加新函数：

- `parse_interactive_input(input_line: str) -> dict` - 解析用户在交互模式下输入的命令
- 支持的格式：
  - `"prompt text"` - 直接输入 prompt
  - `-p "prompt" -r 16:9 -n 2` - 带选项的完整命令
  - `help` - 显示帮助
  - `quit` / `exit` - 退出
  - `status` - 显示当前设置

### Step 3: 重构 `__main__.py` 分离加载和生成逻辑

在 `src/z_image/__main__.py` 中：

- 提取 `generate_images()` 函数，接收 pipeline、prompt、参数等
- 提取 `print_status()` 函数显示当前配置
- 保持 `main()` 函数处理初始化和模式选择

### Step 4: 实现交互式循环

在 `src/z_image/__main__.py` 中添加 `interactive_loop()` 函数：

```python
def interactive_loop(pipe, device, output_dir, default_width, default_height):
    """交互式命令循环"""
    print("\n进入交互模式。输入 'help' 查看帮助，'quit' 退出。\n")

    while True:
        try:
            user_input = input("z-image> ").strip()
            if not user_input:
                continue

            # 解析并执行命令
            ...

        except KeyboardInterrupt:
            print("\n(按 Ctrl+C 中断当前操作，输入 'quit' 退出程序)")
            continue
        except EOFError:
            print("\n退出...")
            break
```

### Step 5: 实现特殊命令处理

- `help` - 显示交互模式帮助信息
- `quit` / `exit` - 退出程序
- `status` - 显示当前设备、分辨率等设置
- `set <option> <value>` - 修改默认设置（可选，增强功能）

### Step 6: 添加测试用例

在 `tests/test_cli.py` 中添加：

- `test_parse_interactive_input_prompt_only` - 测试纯 prompt 解析
- `test_parse_interactive_input_with_options` - 测试带选项的命令解析
- `test_parse_interactive_input_special_commands` - 测试特殊命令解析
- `test_interactive_mode_flag` - 测试 `--interactive` 参数

### Step 7: 运行验证命令

- 运行所有测试确保无回归
- 手动测试交互模式

## Testing Strategy

### Unit Tests
- 测试 `parse_interactive_input()` 函数对各种输入格式的解析
- 测试特殊命令识别
- 测试参数验证逻辑

### Integration Tests
- 测试交互模式启动流程
- 测试 Ctrl+C 在交互模式下的行为

### Edge Cases
- 空输入处理
- 无效命令处理
- 引号内包含特殊字符的 prompt
- 中文 prompt 输入
- EOF (Ctrl+D) 处理

## Acceptance Criteria

1. ✅ `uv run z-image -i` 启动交互模式，加载模型后显示 `z-image>` 提示符
2. ✅ 输入 `"一只猫"` 或 `-p "一只猫"` 生成图像
3. ✅ 输入 `-p "风景" -r 16:9 -n 2` 生成 2 张 16:9 图像
4. ✅ 输入 `help` 显示帮助信息
5. ✅ 输入 `quit` 或 `exit` 退出程序
6. ✅ Ctrl+C 中断当前生成但不退出交互模式
7. ✅ 所有现有测试通过（无回归）
8. ✅ 现有单次运行模式保持不变

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest tests/ -v` - 运行所有测试确保无回归
- `uv run z-image -p "test" --download-only` - 验证单次模式仍然工作
- `echo -e "help\nquit" | uv run z-image -i --download-only` - 验证交互模式基本功能（不加载完整模型）

## Notes

- 使用 Python 内置的 `shlex.split()` 来正确解析带引号的命令行参数
- 交互模式下的 Ctrl+C 应该只中断当前生成，而不是退出程序
- 考虑使用 `readline` 模块提供历史记录和自动补全（可作为后续增强）
- 保持向后兼容：不带 `-i` 参数时行为与之前完全一致
- 交互模式下可以动态改变分辨率，但设备在启动时已确定，不支持动态切换
