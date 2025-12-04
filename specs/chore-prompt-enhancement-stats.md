# Chore: Add Prompt Enhancement Statistics

## Chore Description
在 `generate_detailed_prompt()` 函数中添加增强统计信息，显示 LLM 增强前后的 prompt 字数对比。这有助于用户了解 LLM 扩展 prompt 的效果。

统计信息将包括：
- 原始 prompt 字数
- 增强后 prompt 字数
- 增长比例（百分比）

## Relevant Files
Use these files to resolve the chore:

- `src/generate_prompts/generator.py` - 包含 `generate_detailed_prompt()` 函数，需要在返回结果前添加统计输出
- `tests/test_generate_prompts.py` - 可能需要更新测试以验证统计功能（可选）

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add word count helper function
- 在 `generator.py` 中添加 `count_words(text: str) -> int` 辅助函数
- 使用简单的空格分割来计算字数（支持中英文混合）

### Step 2: Update generate_detailed_prompt() to show statistics
- 在成功获取 LLM 响应后，计算原始和增强后的字数
- 使用 `cprint` 输出统计信息：
  - 原始字数
  - 增强后字数
  - 增长倍数或百分比
- 确保 fallback 路径也显示统计信息

### Step 3: Run validation commands
- 运行测试确保无回归
- 手动测试验证统计信息输出正确

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest tests/test_generate_prompts.py -v` - Run tests to validate no regressions
- `uv run python -c "from generate_prompts.generator import generate_detailed_prompt; generate_detailed_prompt('A person in a park')"` - Manually test statistics output (requires LLM running)

## Notes
- 统计信息使用 `cprint` 输出到终端，不影响函数返回值
- 字数统计使用简单的空格分割，对中文可能不完全准确，但足够作为参考
- 颜色建议：使用 "magenta" 或 "blue" 区分统计信息和其他输出
