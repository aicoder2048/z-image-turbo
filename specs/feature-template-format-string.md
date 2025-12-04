# Feature: Template Format String Support

## Feature Description
扩展 JSON 模板格式，支持自定义 `description_format` 字段。这允许模板作者定义如何将模板属性组合成自然语言描述，而不是依赖硬编码的 `create_prompt_description()` 函数。

当前的 `create_prompt_description()` 函数硬编码了特定字段（如 `subject.age`, `subject.ethnicity`）和固定的句子结构，导致不同结构的模板（如 Marvel 角色模板）无法正确生成描述。

## User Story
As a template author
I want to define a custom format string in my template
So that I can create natural language descriptions for any template structure

## Problem Statement
当前 `create_prompt_description()` 函数硬编码了字段名和句子结构：

```python
description = f"A {subject_type} who is {age}, {ethnicity}, and {expression}, {clothing_desc} {pose} in {environment} with {style} style"
```

这导致：
- `girl_template.json`（有 `age`, `ethnicity`）可以正常工作
- `marvel_template.json`（有 `identity`, `attributes`，没有 `age`, `ethnicity`）生成错误输出如 "A Iron Man who is , , and determined..."

## Solution Statement
在模板 JSON 中添加可选的 `description_format` 字段，使用占位符语法 `{path.to.field}` 引用嵌套字段。

示例：
```json
{
  "description_format": "A {subject.type} ({subject.identity}) with {subject.attributes}, {subject.expression} expression, wearing {clothing.top} and {clothing.bottom}, in {pose} at {environment}, {style} style, {camera_angle}, {lighting} lighting",
  "subject": { ... }
}
```

**关键设计决策**：
1. `description_format` 是可选的 - 如果没有，使用通用 fallback
2. 占位符使用点号语法访问嵌套字段：`{subject.type}`, `{clothing.top}`
3. 每个占位符的值会经过 `get_attribute_value()` 处理，支持 `|` 随机选择
4. 空值占位符会被优雅处理（替换为空字符串并清理多余空格）

## Relevant Files
Use these files to implement the feature:

- `src/generate_prompts/generator.py` - 包含 `create_prompt_description()` 函数，需要重写以支持格式字符串
- `src/generate_prompts/templates/girl_template.json` - 需要添加 `description_format` 字段
- `src/generate_prompts/templates/marvel_template.json` - 需要添加 `description_format` 字段
- `tests/test_generate_prompts.py` - 需要添加新测试用例
- `README.md` - 需要更新文档说明新的模板格式

## Implementation Plan

### Phase 1: Foundation
1. 创建 `resolve_template_value()` 辅助函数，支持点号语法访问嵌套字段
2. 创建 `format_description()` 函数，解析并替换格式字符串中的占位符

### Phase 2: Core Implementation
1. 重写 `create_prompt_description()` 函数：
   - 检查模板是否有 `description_format` 字段
   - 如果有，使用格式字符串生成描述
   - 如果没有，使用通用 fallback（遍历所有字段生成描述）
2. 处理边界情况：空值、缺失字段、嵌套深度

### Phase 3: Integration
1. 更新现有模板添加 `description_format`
2. 更新 README.md 文档
3. 确保向后兼容性（无 `description_format` 的模板仍能工作）

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add helper function `resolve_template_value()`
- 在 `generator.py` 中添加 `resolve_template_value(template, path)` 函数
- 支持点号语法如 `"subject.type"` 访问嵌套字段
- 返回值经过 `get_attribute_value()` 处理
- 缺失字段返回空字符串

### Step 2: Add `format_description()` function
- 在 `generator.py` 中添加 `format_description(template, format_string)` 函数
- 使用正则表达式找到所有 `{path.to.field}` 占位符
- 调用 `resolve_template_value()` 获取值并替换
- 清理多余空格和标点

### Step 3: Create fallback description generator
- 添加 `create_generic_description(template)` 函数
- 遍历模板所有字段生成通用描述
- 格式: "key1: value1, key2: value2, ..."
- 用于没有 `description_format` 的模板

### Step 4: Refactor `create_prompt_description()`
- 检查模板是否有 `description_format` 字段
- 如果有，调用 `format_description()`
- 如果没有，调用 `create_generic_description()`
- 保持错误处理

### Step 5: Add unit tests
- 测试 `resolve_template_value()` 的各种情况
- 测试 `format_description()` 的占位符替换
- 测试带 `description_format` 的模板
- 测试无 `description_format` 的 fallback 行为
- 测试空值和缺失字段处理

### Step 6: Update existing templates
- 更新 `girl_template.json` 添加 `description_format`
- 更新 `marvel_template.json` 添加 `description_format`

### Step 7: Update README.md documentation
- 在 Template Format 部分添加 `description_format` 说明
- 提供示例展示如何使用占位符语法

### Step 8: Run validation commands
- 运行所有测试确保无回归
- 手动测试模板生成

## Testing Strategy

### Unit Tests
- `test_resolve_template_value_simple`: 测试简单字段访问 `{style}`
- `test_resolve_template_value_nested`: 测试嵌套访问 `{subject.type}`
- `test_resolve_template_value_missing`: 测试缺失字段返回空字符串
- `test_resolve_template_value_with_pipe`: 测试 `|` 随机选择
- `test_format_description_basic`: 测试基本格式字符串替换
- `test_format_description_cleanup`: 测试多余空格/标点清理
- `test_create_prompt_description_with_format`: 测试带格式字符串的模板
- `test_create_prompt_description_fallback`: 测试无格式字符串的 fallback

### Integration Tests
- 使用 `girl_template.json` 生成描述并验证包含预期内容
- 使用 `marvel_template.json` 生成描述并验证包含预期内容

### Edge Cases
- 空模板 `{}`
- 只有 `description_format` 没有其他字段
- 格式字符串引用不存在的字段
- 深度嵌套字段 `{a.b.c.d}`
- 多个连续占位符之间的空格处理

## Acceptance Criteria
1. 带 `description_format` 的模板正确生成描述
2. 无 `description_format` 的模板使用 fallback 生成描述
3. `|` 随机选择功能在格式字符串中正常工作
4. 缺失字段被优雅处理（不产生错误，不留下空占位符）
5. 现有测试全部通过
6. 新增测试覆盖所有新功能

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest tests/test_generate_prompts.py -v` - Run all generate_prompts tests
- `uv run pytest tests/test_generate_prompts.py -v -k "description"` - Run description-related tests specifically
- `uv run python -c "from generate_prompts.generator import create_prompt_description; import json; t = json.load(open('src/generate_prompts/templates/marvel_template.json')); print(create_prompt_description(t))"` - Test Marvel template description generation

## Notes
- 保持向后兼容性：没有 `description_format` 的模板应该使用 fallback 而不是报错
- 格式字符串中的占位符语法 `{field}` 与 Python 的 f-string 类似，但使用自定义解析器以支持嵌套字段
- 考虑未来可能添加的功能：条件占位符 `{field?prefix:suffix}`、默认值 `{field|default}`
