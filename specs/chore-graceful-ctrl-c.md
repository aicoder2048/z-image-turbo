# Chore: Graceful Ctrl+C Support During Image Generation

## Chore Description
添加对 Ctrl+C (KeyboardInterrupt) 的优雅处理支持，使用户在图像生成过程中可以随时中断程序，并得到友好的退出信息，而不是看到完整的 Python traceback。

当前行为：
- 用户按下 Ctrl+C 时，程序会抛出 `KeyboardInterrupt` 异常并显示完整的 stack trace
- 没有清理操作或友好的退出提示

期望行为：
- 用户按下 Ctrl+C 时，显示友好的中断消息（如 "用户中断，正在退出..."）
- 如果正在批量生成，显示已完成的进度（如 "已生成 3/10 张图像"）
- 干净地退出程序，不显示 traceback

## Relevant Files
Use these files to resolve the chore:

- `src/z_image/__main__.py` - 主入口文件，包含图像生成循环，需要添加 `try/except KeyboardInterrupt` 处理
- `tests/test_cli.py` - CLI 测试文件，需要添加 Ctrl+C 处理的测试用例

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: 修改 `__main__.py` 添加 KeyboardInterrupt 处理

- 在 `main()` 函数中，用 `try/except KeyboardInterrupt` 包裹图像生成循环
- 在循环开始前初始化计数器变量，跟踪已成功生成的图像数量
- 捕获 `KeyboardInterrupt` 时：
  - 打印友好的中断消息
  - 如果有已完成的图像，显示进度信息
  - 使用 `sys.exit(0)` 正常退出

具体修改：

```python
# 在文件顶部添加 import
import sys

# 在 main() 函数的图像生成部分:
# 5. 生成图像
total_images = len(prompts) * args.count
completed_images = 0  # 新增：跟踪已完成数量

try:
    for prompt_idx, original_prompt in enumerate(prompts):
        # ... 现有代码 ...

        for i in range(args.count):
            # ... 现有代码 ...

            image, used_seed, output_path = generate_image(...)
            completed_images += 1  # 新增：更新计数
            print(f"已保存: {output_path}")
            print(f"种子: {used_seed}")

except KeyboardInterrupt:
    print("\n")
    print("用户中断，正在退出...")
    if completed_images > 0:
        print(f"已完成 {completed_images}/{total_images} 张图像")
    sys.exit(0)
```

### Step 2: 添加测试用例

在 `tests/test_cli.py` 中添加测试，验证 KeyboardInterrupt 的处理逻辑：

```python
def test_main_handles_keyboard_interrupt(capsys):
    """测试 main() 优雅处理 Ctrl+C"""
    # Mock 各种依赖，让 generate_image 抛出 KeyboardInterrupt
    # 验证程序正常退出且输出友好消息
```

### Step 3: 运行验证命令

- 运行测试确保无回归
- 手动测试 Ctrl+C 行为

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest tests/ -v` - 运行所有测试确保无回归
- `uv run z-image -p "test" --download-only` - 测试基本功能（不需要实际生成）

## Notes

- Python 的 `KeyboardInterrupt` 在按下 Ctrl+C 时由操作系统发送 SIGINT 信号触发
- 使用 `sys.exit(0)` 而非 `sys.exit(1)` 因为用户主动中断不算错误
- 不需要使用 `signal` 模块，直接捕获 `KeyboardInterrupt` 异常更简单且足够
- 考虑到 Pipeline 加载时间较长，在加载阶段也应该能够中断，因此 try 块应该包含整个生成流程
