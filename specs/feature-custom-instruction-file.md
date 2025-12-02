# Feature: Custom Instruction File Support

## Feature Description
Add support for loading custom prompt instructions from an external file, allowing users to define their own LLM prompting strategy instead of relying solely on the hardcoded default `prompt_instruction`. This enables users to customize how the LLM expands template descriptions into detailed image generation prompts, supporting different styles, tones, or specialized requirements.

## User Story
As a **power user of generate_prompts**
I want to **provide my own instruction file to control how LLM generates detailed prompts**
So that **I can customize the prompt expansion style, tone, and specific requirements for different use cases (e.g., anime style, product photography, portrait photography) without modifying the source code**

## Problem Statement
Currently, the `generate_detailed_prompt()` function in `generator.py` uses a hardcoded `prompt_instruction` string (lines 173-187) that cannot be modified without editing the source code. Users who want different prompt expansion styles must fork or modify the codebase directly. This limits flexibility and makes it difficult to:
- Use different instruction styles for different projects
- Share and reuse instruction templates
- Quickly iterate on prompt engineering without code changes

## Solution Statement
Add a new optional CLI argument `--instruction` / `-i` that accepts a path to a text file containing custom LLM instructions. The file content will replace the default `prompt_instruction` template. The file should support a placeholder `{template_description}` (f-string style) that will be substituted with the template description at runtime. If no instruction file is provided, the existing default behavior is preserved.

## Relevant Files
Use these files to implement the feature:

- `src/generate_prompts/generator.py` - Contains `generate_detailed_prompt()` function with hardcoded `prompt_instruction`. This is where we'll add the instruction loading logic and modify the function signature.
- `src/generate_prompts/cli.py` - Contains CLI argument parsing. We'll add the new `--instruction` argument here and pass it through to the generator.
- `tests/test_generate_prompts.py` - Contains existing tests. We'll add tests for the new instruction file loading functionality.
- `README.md` - Documentation. We'll add usage examples for the new feature.

### New Files
- `src/generate_prompts/instructions/default.txt` - Default instruction file containing the LLM prompt template with `{template_description}` placeholder

## Implementation Plan

### Phase 1: Foundation
1. Create a new function `load_instruction_file()` in `generator.py` to read and validate instruction files
2. Define the default instruction as a module-level constant for easy reference
3. Ensure the function handles file encoding (UTF-8) and missing files gracefully

### Phase 2: Core Implementation
1. Modify `generate_detailed_prompt()` to accept an optional `instruction_template` parameter
2. Update the function to use the provided template or fall back to the default
3. Implement placeholder substitution for `{description}` in custom instructions

### Phase 3: Integration
1. Add `--instruction` / `-i` CLI argument to `cli.py`
2. Load the instruction file in `main()` and pass it to `generate_detailed_prompt()`
3. Update help text and error messages
4. Add documentation and examples

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Default Instruction File
- Create `input/prompts_enhancing_instructions/default.txt` with the current hardcoded instruction content
- The file uses `{template_description}` as an f-string placeholder

### Step 2: Add Constants and Load Function in generator.py
- Define `DEFAULT_INSTRUCTION_FILE` as a module-level constant pointing to `src/generate_prompts/instructions/default.txt`
- Create `load_instruction_file(instruction_path: str) -> str` function that:
  - Reads the file with UTF-8 encoding
  - Validates the file contains `{template_description}` placeholder
  - Returns the instruction content
  - Raises appropriate exceptions with clear error messages

### Step 3: Modify generate_detailed_prompt() Function
- Add optional parameter `instruction_template: str | None = None`
- If `instruction_template` is provided, use it; otherwise load from `DEFAULT_INSTRUCTION_FILE`
- Use f-string formatting to substitute `{template_description}` with the actual description
- Ensure backward compatibility (existing calls without the parameter still work)

### Step 4: Update CLI Argument Parser
- Add `--instruction` / `-i` argument to `parse_args()`:
  - Type: `str` (file path)
  - Required: `False`
  - Default: `None`
  - Help: "Path to custom instruction file (default: src/generate_prompts/instructions/default.txt)"

### Step 5: Integrate in CLI main() Function
- After loading template, check if `args.instruction` is provided
- If provided, call `load_instruction_file()` to load custom instruction
- Pass the instruction template to `generate_detailed_prompt()` calls
- Handle file not found and validation errors with user-friendly messages

### Step 6: Add Unit Tests
- Test `load_instruction_file()` with valid file
- Test `load_instruction_file()` with missing file (should raise)
- Test `load_instruction_file()` with file missing `{template_description}` placeholder (should raise/warn)
- Test `generate_detailed_prompt()` with custom instruction template
- Test `generate_detailed_prompt()` without instruction (default behavior preserved)

### Step 7: Update Documentation
- Add section in README.md explaining custom instruction files
- Provide example instruction file content
- Document the `{template_description}` placeholder requirement

### Step 8: Run Validation Commands
- Run all tests to ensure zero regressions
- Manually test with example instruction file

## Testing Strategy

### Unit Tests
- `test_load_instruction_file_valid`: Test loading a valid instruction file
- `test_load_instruction_file_missing`: Test error handling for missing files
- `test_load_instruction_file_no_placeholder`: Test warning/error for files without `{template_description}`
- `test_generate_detailed_prompt_with_custom_instruction`: Test custom instruction is used correctly
- `test_generate_detailed_prompt_default`: Test default instruction is used when none provided

### Integration Tests
- Test full CLI flow with `--instruction` argument
- Test CLI without `--instruction` (backward compatibility)

### Edge Cases
- Empty instruction file
- Instruction file with multiple `{template_description}` placeholders
- Very large instruction file
- Instruction file with special characters/unicode
- Non-UTF-8 encoded file

## Acceptance Criteria
1. Users can provide `--instruction` / `-i` CLI argument with a file path
2. The instruction file content is used instead of the default instruction file
3. The `{template_description}` placeholder in the instruction file is replaced with the actual template description (f-string style)
4. If no instruction file is provided, the tool uses `src/generate_prompts/instructions/default.txt`
5. Clear error messages are shown for missing or invalid instruction files
6. All existing tests pass without modification
7. New tests cover the instruction file loading functionality
8. README.md is updated with usage examples

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest tests/ -v` - Run all tests to validate zero regressions
- `uv run generate_prompts --help` - Verify new `--instruction` argument appears in help
- `uv run generate_prompts -t input/prompt_template.json -n 1 -y` - Test with default instruction file (requires Ollama running)
- `uv run generate_prompts -t input/prompt_template.json -i src/generate_prompts/instructions/default.txt -n 1 -y` - Test with explicit instruction file path

## Notes
- The `{template_description}` placeholder uses Python f-string style substitution
- The default instruction is now externalized to `src/generate_prompts/instructions/default.txt` for easy modification
- Consider supporting environment variable `GENERATE_PROMPTS_INSTRUCTION` in future iterations for more flexibility
- Users can create project-specific instruction files and commit them to version control for reproducibility
- The instruction file should be plain text (.txt) but the extension is not enforced

## Default Instruction File Content
The `src/generate_prompts/instructions/default.txt` file should contain:

```
Create a detailed image generation prompt based on the following description:

{template_description}

Expand this into a comprehensive, highly descriptive, and very-detailed prompt that would help an AI image generator
create a high-quality image. Include specific details about lighting, composition,
atmosphere, and any other relevant elements. Make it vivid and descriptive.

Important: When describing the person, make sure to naturally incorporate their ethnicity
(English) as part of the description in a way that flows naturally, rather than listing it
as a separate attribute.

Important: Just return the resulting prompt, do not repeat the request and do not include any other text.
```
