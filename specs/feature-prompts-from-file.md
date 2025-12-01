# Feature: Read Prompts from File

## Feature Description
Add the ability for z-image-turbo to read prompts from external files instead of requiring a single prompt via command line. Supports two file formats:
1. **JSON file** (default: `input/prompts/prompts.json`) - reads the `description` field from each object
2. **Text file** (`.txt`) - each line is treated as a separate prompt

When using file-based prompts, the `--count` option applies to **each prompt** individually, allowing batch generation of multiple variations per prompt.

## User Story
As a **power user generating multiple images**
I want to **read prompts from a file**
So that **I can batch process multiple prompts without running the command repeatedly**

## Problem Statement
Currently, z-image-turbo only accepts a single prompt via the `-p/--prompt` argument. Users who want to generate images from multiple prompts must run the command multiple times or write wrapper scripts. This is inefficient and doesn't integrate with the existing `generate_prompts` module which outputs prompts to JSON files.

## Solution Statement
Add a new `--prompts-file` / `-f` argument that accepts a file path. The file type is detected by extension:
- `.json` files: Parse as JSON array, extract `description` field from each object
- `.txt` files: Read line by line, each non-empty line is a prompt

When `--prompts-file` is used:
- `--prompt` becomes optional (mutually exclusive with `--prompts-file`)
- `--count` applies to each prompt (e.g., 3 prompts × 2 count = 6 images total)
- Progress shows current prompt index and count

## Relevant Files
Use these files to implement the feature:

- `src/z_image/cli.py` - Add new `--prompts-file` argument and file parsing logic
- `src/z_image/__main__.py` - Modify main loop to iterate over prompts from file
- `tests/test_cli.py` - Add unit tests for prompt file parsing

### New Files
- `src/z_image/prompt_loader.py` - Module for loading prompts from JSON/text files (optional, can be in cli.py)

## Implementation Plan

### Phase 1: Foundation
Add prompt loading functions to parse JSON and text files:
- `load_prompts_from_json(path)` - Parse JSON, extract `description` fields
- `load_prompts_from_text(path)` - Read lines, filter empty
- `load_prompts(path)` - Dispatcher based on file extension

### Phase 2: Core Implementation
Modify CLI to accept file-based prompts:
- Add `--prompts-file` / `-f` argument
- Make `--prompt` and `--prompts-file` mutually exclusive
- Update validation logic for the new argument combination

### Phase 3: Integration
Update main generation loop:
- Load prompts from file if `--prompts-file` is provided
- Iterate over each prompt, applying `--count` to each
- Display progress with prompt index (e.g., "Prompt 1/5, Image 2/3")

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Prompt Loading Functions to cli.py
- Add `load_prompts_from_json(file_path: Path) -> list[str]` function
  - Read JSON file, expect array of objects with `description` key
  - Return list of description strings
  - Handle missing `description` key gracefully (skip or warn)
- Add `load_prompts_from_text(file_path: Path) -> list[str]` function
  - Read file line by line
  - Strip whitespace, filter empty lines
  - Return list of prompt strings
- Add `load_prompts(file_path: Path) -> list[str]` dispatcher
  - Check file extension (`.json` vs `.txt`)
  - Call appropriate loader
  - Raise error for unsupported extensions

### Step 2: Update CLI Argument Parser
- Add `--prompts-file` / `-f` argument
  - Type: `str` (file path)
  - Default: `None`
  - Help: "Read prompts from JSON file (extracts 'description' field) or text file (one prompt per line). Default JSON path: input/prompts/prompts.json"
- Modify validation logic:
  - If neither `--prompt` nor `--prompts-file` is provided (and not `--download-only`), show error
  - If both are provided, show error (mutually exclusive)

### Step 3: Update Main Generation Loop
- In `__main__.py`, check if `args.prompts_file` is set
- If set, call `load_prompts(args.prompts_file)` to get prompt list
- If not set, use `[args.prompt]` as single-item list
- Modify generation loop to iterate over prompts:
  ```python
  for prompt_idx, prompt in enumerate(prompts):
      for i in range(args.count):
          print(f"\n生成图像 [Prompt {prompt_idx+1}/{len(prompts)}, Image {i+1}/{args.count}]...")
          # ... generate_image call
  ```

### Step 4: Add Unit Tests
- Test `load_prompts_from_json` with valid JSON
- Test `load_prompts_from_json` with missing `description` key
- Test `load_prompts_from_text` with multi-line file
- Test `load_prompts_from_text` with empty lines (should be filtered)
- Test `load_prompts` dispatcher for `.json` and `.txt` extensions
- Test `load_prompts` with unsupported extension (should raise error)

### Step 5: Run Validation Commands
- Run all tests to ensure no regressions
- Test manually with sample JSON and text files

## Testing Strategy

### Unit Tests
- `test_load_prompts_from_json_valid` - Valid JSON array with description fields
- `test_load_prompts_from_json_missing_description` - Objects without description key
- `test_load_prompts_from_json_empty_array` - Empty JSON array
- `test_load_prompts_from_text_multiline` - Multiple lines with prompts
- `test_load_prompts_from_text_empty_lines` - Empty/whitespace lines filtered
- `test_load_prompts_dispatcher_json` - Correct dispatcher for .json
- `test_load_prompts_dispatcher_txt` - Correct dispatcher for .txt
- `test_load_prompts_unsupported_extension` - Raises error for .csv, etc.

### Integration Tests
- Test argument parsing with `--prompts-file`
- Test mutual exclusivity of `--prompt` and `--prompts-file`

### Edge Cases
- Empty JSON array → should handle gracefully (no prompts to process)
- Text file with only whitespace → should result in empty prompt list
- JSON file with some objects missing `description` → skip those entries
- Very long prompts in text file → should work normally
- Unicode/Chinese prompts in both formats → should preserve encoding

## Acceptance Criteria
- [ ] `--prompts-file` / `-f` argument is available
- [ ] JSON files are parsed correctly, extracting `description` field
- [ ] Text files are parsed correctly, one prompt per line
- [ ] `--count` applies to each prompt individually
- [ ] Progress output shows prompt index and image count
- [ ] `--prompt` and `--prompts-file` are mutually exclusive
- [ ] Existing behavior unchanged when using `--prompt`
- [ ] All unit tests pass
- [ ] Works with output from `generate_prompts` module (JSON format)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest tests/ -v` - Run all tests to validate the feature works with zero regressions
- `uv run z-image --help` - Verify new argument appears in help
- `uv run z-image -f input/prompts/prompts.json --download-only` - Test JSON file argument parsing (dry run)
- `echo -e "a cat\na dog" > /tmp/test_prompts.txt && uv run z-image -f /tmp/test_prompts.txt --download-only` - Test text file argument parsing

## Notes
- The default JSON path `input/prompts/prompts.json` matches the output of the `generate_prompts` module
- No new libraries required - uses standard `json` and `pathlib`
- Future enhancement: Add `--prompts-file` default behavior (auto-detect if file exists)
- Future enhancement: Support other formats like CSV or YAML
