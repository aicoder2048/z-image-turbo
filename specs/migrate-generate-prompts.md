# Migrate the Project of "Generate Prompts"

## Copy Files
- COPY directory `/Users/szou/Python/Playground/MLX-FLUX/documents/pydantic_ai` to `ai_docs/.`
- COPY file `/Users/szou/Python/Playground/MLX-FLUX/.env` to current directory `.`
- CREATE new directory: `./src/generate_prompts`
- COPY file `/Users/szou/Python/Playground/MLX-FLUX/generate_prompts.py` to `./src/generate_prompts/.`
- CREATE new direcotry: `./input` and Add the directory to .gitignore
- COPY file `/Users/szou/Python/Playground/MLX-FLUX/prompt_template.json` to `./input`

## Env
- Update the pyproject.toml to support 'uv run generate_prompt'
- Use 'uv add' to add dependencies

## Test
- Add tests

## Document

Update the README.md for this migrated Project


## READ the follow Code for Reference When use the generated prompt for image generation
- Function to Remove Illigal Chars from Prompt
```Python
def sanitize_prompt(prompt):
    """Sanitize the prompt to remove special tokens and problematic characters"""
    if not prompt:
        return prompt

    # List of known problematic tokens/characters
    problematic_tokens = [
        '—</w>',
        '</w>',
        '<|endoftext|>',
        '<|end|>',
        '\u2014',  # em dash
        '—',       # another em dash
        '–',       # en dash
        ''',       # curly quote
        ''',       # curly quote
        '"',       # curly quote
        '"',       # curly quote
        '…',       # ellipsis
    ]

    sanitized = prompt

    # First check for specific problematic tokens
    for token in problematic_tokens:
        if token in sanitized:
            sanitized = sanitized.replace(token, ' ')
            cprint(f"Removed special token '{token}' from prompt", "yellow")

    # Use regex to catch any remaining </w> patterns with any characters before them
    original_len = len(sanitized)
    sanitized = re.sub(r'[^\s]*</w>', '', sanitized)
    if len(sanitized) != original_len:
        cprint("Removed </w> token patterns from prompt", "yellow")

    # Use regex to catch any remaining special tokens with angle brackets
    original_len = len(sanitized)
    sanitized = re.sub(r'<[^>]*>', '', sanitized)
    if len(sanitized) != original_len:
        cprint("Removed angle bracket tokens from prompt", "yellow")

    # Remove any non-ASCII characters
    original_len = len(sanitized)
    sanitized = re.sub(r'[^\x00-\x7F]+', ' ', sanitized)
    if len(sanitized) != original_len:
        cprint("Removed non-ASCII characters from prompt", "yellow")

    # Replace multiple spaces with a single space
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    # If the prompt was modified, log it
    if sanitized != prompt:
        cprint("Prompt was sanitized to remove special tokens", "yellow")
        if len(sanitized) < 10:  # If sanitizing made the prompt too short
            cprint("Warning: Sanitized prompt is very short. This may affect generation quality.", "red")

    return sanitized
```
- Function to Check if Prompt has Illigal Chars
```Python
def is_prompt_problematic(prompt):
    """Check if a prompt is likely to cause issues with generation

    Args:
        prompt: The prompt to check

    Returns:
        bool: True if the prompt is likely problematic, False otherwise
    """
    if not prompt or prompt.strip() == "":
        return True

    # Check for common problematic patterns
    problematic_patterns = [
        r'</w>',
        r'<\|.*?\|>',
        r'<[^>]*>',  # Any tag-like structure
        r'\[\[.*?\]\]',  # Double brackets
        r'\{\{.*?\}\}',  # Double curly braces
    ]

    for pattern in problematic_patterns:
        if re.search(pattern, prompt):
            return True

    # Check if the prompt is too short after removing special characters
    clean_prompt = re.sub(r'[^\w\s]', '', prompt).strip()
    if len(clean_prompt) < 5:  # Arbitrary threshold
        return True

    return False
```
- Code Sample to Use the Functions of sanitize_prompt and is_prompt_problematic
```Python
try:
    # Sanitize the prompt to remove any special tokens that might cause issues
    original_prompt = prompt
    prompt = sanitize_prompt(prompt)

    # Check if prompt is still valid after sanitization
    if not prompt or prompt.strip() == "":
        cprint("Error: Prompt is empty after sanitization. Skipping.", "red")
        return False

    # Check if the sanitized prompt is still likely to cause issues
    if is_prompt_problematic(prompt):
        cprint("Warning: Prompt may still contain problematic patterns after sanitization.", "yellow")
        cprint("Attempting generation anyway, but errors may occur.", "yellow")
    ...
```
