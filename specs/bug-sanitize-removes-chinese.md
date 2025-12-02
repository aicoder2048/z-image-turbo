# Bug: Sanitize Prompt Removes Chinese Characters

## Bug Description
`sanitize_prompt()` 函数会移除所有中文字符，导致中文 prompt 在图像生成时被清空或变得无意义。

**症状**:
- 输入中文 prompt 如 "一只猫在太空中漂浮"，sanitize 后变成空字符串或只剩空格
- 程序显示警告 "Removed non-ASCII characters from prompt"
- 图像生成失败或输出不符合预期

**期望行为**:
- 中文 prompt 应该保持完整，因为 Z-Image-Turbo 模型原生支持中英双语

**实际行为**:
- 所有非 ASCII 字符（包括中文）都被移除，替换为空格

## Problem Statement
`sanitize_prompt()` 函数中的正则表达式 `r'[^\x00-\x7F]+'` 移除了所有非 ASCII 字符，这是错误的设计，因为：
1. Z-Image-Turbo 模型支持中文 prompt
2. 中文是合法的输入，不应被移除
3. 该函数的目的是移除有问题的特殊 token（如 `</w>`、`<|endoftext|>`），而不是移除所有非英文字符

## Solution Statement
修改 `sanitize_prompt()` 函数，只移除已知的问题字符（如 em dash、curly quotes 等），而不是移除所有非 ASCII 字符。同时更新 `is_prompt_problematic()` 函数以正确处理中文 prompt。

具体修改：
1. 删除移除所有非 ASCII 字符的正则表达式
2. 保留对已知问题字符的替换逻辑（已在 `problematic_tokens` 列表中定义）
3. 更新测试用例以验证中文保留
4. 修复 `is_prompt_problematic()` 中的 `\w` 正则，因为它在某些情况下也不匹配中文

## Steps to Reproduce
1. 运行 `uv run python -c "from generate_prompts.generator import sanitize_prompt; print(repr(sanitize_prompt('一只猫在太空中漂浮')))"`
2. 观察输出为空字符串或只有空格

## Root Cause Analysis
在 `src/generate_prompts/generator.py` 第 341-344 行：

```python
original_len = len(sanitized)
sanitized = re.sub(r'[^\x00-\x7F]+', ' ', sanitized)
if len(sanitized) != original_len:
    cprint("Removed non-ASCII characters from prompt", "yellow")
```

这段代码使用 `[^\x00-\x7F]+` 正则表达式移除所有非 ASCII 字符（ASCII 范围是 0x00-0x7F）。中文字符的 Unicode 码点远超过 0x7F，所以全部被移除。

这是一个过度激进的清理策略，原本可能是为了处理 LLM 输出中的特殊字符，但错误地影响了合法的多语言输入。

## Relevant Files
Use these files to fix the bug:

- `src/generate_prompts/generator.py` - 包含 `sanitize_prompt()` 和 `is_prompt_problematic()` 函数，需要修改正则表达式逻辑
- `tests/test_generate_prompts.py` - 包含相关测试用例，需要添加中文保留测试并修改现有测试

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: 修改 `sanitize_prompt()` 函数

在 `src/generate_prompts/generator.py` 中：

- 删除第 341-344 行移除非 ASCII 字符的代码块：
  ```python
  original_len = len(sanitized)
  sanitized = re.sub(r'[^\x00-\x7F]+', ' ', sanitized)
  if len(sanitized) != original_len:
      cprint("Removed non-ASCII characters from prompt", "yellow")
  ```

- 保留其他清理逻辑（`problematic_tokens` 列表中的字符已经涵盖了需要移除的特殊字符）

### Step 2: 修改 `is_prompt_problematic()` 函数

在 `src/generate_prompts/generator.py` 中：

- 修改第 380-381 行的正则表达式，使用 Unicode 感知的方式检查 prompt 长度：
  ```python
  # 原代码:
  clean_prompt = re.sub(r'[^\w\s]', '', prompt).strip()
  if len(clean_prompt) < 5:

  # 修改为使用 re.UNICODE 标志或更简单的方式:
  clean_prompt = re.sub(r'[^\w\s]', '', prompt, flags=re.UNICODE).strip()
  if len(clean_prompt) < 3:  # 中文字符通常更短但含义更丰富
  ```

### Step 3: 更新测试用例

在 `tests/test_generate_prompts.py` 中：

- 修改 `test_removes_non_ascii` 测试，因为我们不再移除所有非 ASCII 字符
- 添加新测试 `test_preserves_chinese_characters` 验证中文保留
- 添加新测试 `test_chinese_prompt_not_problematic` 验证中文 prompt 不被认为是问题

### Step 4: 运行验证命令

- 运行所有测试确保无回归
- 手动验证中文 prompt 保留

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python -c "from generate_prompts.generator import sanitize_prompt; print(repr(sanitize_prompt('一只猫在太空中漂浮')))"` - 验证中文被保留（修复前输出空字符串，修复后应输出原始中文）
- `uv run python -c "from generate_prompts.generator import is_prompt_problematic; print(is_prompt_problematic('一只猫'))"` - 验证中文 prompt 不被认为有问题（应输出 False）
- `uv run pytest tests/ -v` - 运行所有测试确保无回归

## Notes

- Z-Image-Turbo 模型由阿里通义团队开发，原生支持中英双语 prompt，这是模型的核心特性之一
- `problematic_tokens` 列表中已经包含了需要移除的特殊字符（em dash、curly quotes 等），不需要额外的"移除所有非 ASCII"逻辑
- `\w` 在 Python 正则表达式中默认支持 Unicode 字符（包括中文），但为明确起见可以添加 `re.UNICODE` 标志
- 将 `is_prompt_problematic` 中的最小长度从 5 降到 3，因为中文字符表达信息更密集
