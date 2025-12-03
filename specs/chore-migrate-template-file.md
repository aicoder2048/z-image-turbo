# Chore: Migrate Default Template File Location

## Chore Description
将 `generate_prompts` 模块的默认模板文件从 `input/prompt_template.json` 迁移到 `src/generate_prompts/templates/default_template.json`。

这样做的好处：
- 模板文件与代码放在一起，便于版本控制
- 与 `instructions/default.txt` 保持一致的组织结构
- `input/` 目录被 `.gitignore` 忽略，用户自定义模板不会被意外提交

注意：用户请求的是 `.txt` 扩展名，但模板文件是 JSON 格式，应使用 `.json` 扩展名以保持一致性。

## Relevant Files
Use these files to resolve the chore:

- `src/generate_prompts/generator.py` - 定义 `DEFAULT_TEMPLATE_FILE` 常量，需要修改路径
- `src/generate_prompts/cli.py` - 从 generator.py 导入并使用 `DEFAULT_TEMPLATE_FILE`，帮助文本需要自动更新
- `README.md` - 文档中提到模板文件路径的地方需要更新
- `input/prompt_template.json` - 当前的默认模板文件，内容需要复制到新位置
- `tests/test_generate_prompts.py` - 测试文件，可能需要更新测试用例

### New Files
- `src/generate_prompts/templates/default_template.json` - 新的默认模板文件位置

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create templates directory and copy template file
- 创建 `src/generate_prompts/templates/` 目录
- 将 `input/prompt_template.json` 的内容复制到 `src/generate_prompts/templates/default_template.json`

### Step 2: Update DEFAULT_TEMPLATE_FILE constant in generator.py
- 修改 `src/generate_prompts/generator.py` 第 22 行
- 将 `DEFAULT_TEMPLATE_FILE = "input/prompt_template.json"` 改为 `DEFAULT_TEMPLATE_FILE = "src/generate_prompts/templates/default_template.json"`

### Step 3: Update README.md documentation
- 搜索 README.md 中所有提到 `input/prompt_template.json` 的地方
- 更新为新路径 `src/generate_prompts/templates/default_template.json`
- 更新代码结构部分，添加 `templates/` 目录说明

### Step 4: Verify tests still pass
- 检查 `tests/test_generate_prompts.py` 是否有硬编码的模板路径
- 运行测试确保没有回归

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `ls -la src/generate_prompts/templates/` - Verify templates directory exists and contains default_template.json
- `cat src/generate_prompts/templates/default_template.json` - Verify template content is valid JSON
- `grep -n "DEFAULT_TEMPLATE_FILE" src/generate_prompts/generator.py` - Verify constant is updated
- `grep -n "prompt_template.json" README.md` - Verify no old paths remain in README (should return empty)
- `uv run pytest tests/test_generate_prompts.py -v` - Run tests to validate no regressions

## Notes
- `input/prompt_template.json` 可以保留作为用户自定义模板的示例，但不再作为默认模板
- CLI 帮助文本会自动更新，因为它使用 `DEFAULT_TEMPLATE_FILE` 常量
- 这个改动与之前的 `instructions/default.txt` 迁移保持一致的目录结构
