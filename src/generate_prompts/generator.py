#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prompt generator using LLM (Ollama/OpenAI/Grok) to expand template descriptions."""

import json
import os
import datetime
import time
import random
import re
from pathlib import Path
from termcolor import cprint
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# Load environment variables
load_dotenv()

# Constants
DEFAULT_TEMPLATE_FILE = "src/generate_prompts/templates/default_template.json"
DEFAULT_OUTPUT_FILE = "input/prompts/prompts.json"
DEFAULT_INSTRUCTION_FILE = "src/generate_prompts/instructions/default_instruction.txt"
MAX_RETRIES = 3

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:27b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Grok (xAI) Configuration
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3-mini")
GROK_BASE_URL = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")


def create_llm_model() -> tuple[OpenAIChatModel, str, str]:
    """Create the LLM model based on the configured provider.

    Returns:
        A tuple of (model, provider_name, model_name) for the configured LLM provider.

    Raises:
        ValueError: If the provider is invalid or required API key is missing.
    """
    provider = LLM_PROVIDER

    if provider == "ollama":
        model = OpenAIChatModel(
            model_name=OLLAMA_MODEL,
            provider=OpenAIProvider(base_url=OLLAMA_URL)
        )
        return model, "Ollama", OLLAMA_MODEL

    elif provider == "openai":
        if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI provider. "
                "Please set it in your .env file."
            )
        model = OpenAIChatModel(
            model_name=OPENAI_MODEL,
            provider=OpenAIProvider(
                base_url=OPENAI_BASE_URL,
                api_key=OPENAI_API_KEY
            )
        )
        return model, "OpenAI", OPENAI_MODEL

    elif provider == "grok":
        if not GROK_API_KEY or not GROK_API_KEY.strip():
            raise ValueError(
                "GROK_API_KEY environment variable is required for Grok provider. "
                "Please set it in your .env file."
            )
        model = OpenAIChatModel(
            model_name=GROK_MODEL,
            provider=OpenAIProvider(
                base_url=GROK_BASE_URL,
                api_key=GROK_API_KEY
            )
        )
        return model, "Grok (xAI)", GROK_MODEL

    else:
        raise ValueError(
            f"Invalid LLM_PROVIDER: '{provider}'. "
            "Supported providers: ollama, openai, grok"
        )


def load_instruction_file(instruction_path: str = DEFAULT_INSTRUCTION_FILE) -> str:
    """Load the instruction template from a text file.

    Args:
        instruction_path: Path to the instruction file containing the LLM prompt template.
                         Must contain {template_description} placeholder.

    Returns:
        The instruction template content as a string.

    Raises:
        FileNotFoundError: If the instruction file does not exist.
        ValueError: If the instruction file does not contain {template_description} placeholder.
    """
    try:
        cprint(f"Loading instruction from {instruction_path}...", "cyan")
        with open(instruction_path, "r", encoding="utf-8") as f:
            instruction = f.read()

        if "{template_description}" not in instruction:
            raise ValueError(
                f"Instruction file '{instruction_path}' must contain "
                "{{template_description}} placeholder"
            )

        cprint("Instruction loaded successfully!", "green")
        return instruction
    except FileNotFoundError:
        cprint(f"Error: Instruction file not found: {instruction_path}", "red")
        raise
    except Exception as e:
        cprint(f"Error loading instruction: {str(e)}", "red")
        raise


def load_template(template_file: str = DEFAULT_TEMPLATE_FILE) -> dict:
    """Load the prompt template from the JSON file"""
    try:
        cprint(f"Loading template from {template_file}...", "cyan")
        with open(template_file, "r", encoding="utf-8") as f:
            template = json.load(f)
        cprint("Template loaded successfully!", "green")
        return template
    except Exception as e:
        cprint(f"Error loading template: {str(e)}", "red")
        raise


def load_existing_prompts(output_file: str = DEFAULT_OUTPUT_FILE) -> list:
    """Load existing prompts from the output file if it exists"""
    try:
        if os.path.exists(output_file):
            cprint(f"Loading existing prompts from {output_file}...", "cyan")
            if os.path.getsize(output_file) == 0:
                cprint("Empty prompts file found. Creating new.", "yellow")
                return []

            with open(output_file, "r", encoding="utf-8") as f:
                prompts = json.load(f)
            cprint(f"Loaded {len(prompts)} existing prompts.", "green")
            return prompts
        else:
            cprint("No existing prompts file found. Creating new.", "yellow")
            return []
    except Exception as e:
        cprint(f"Error loading existing prompts: {str(e)}", "red")
        return []


def generate_prompt_id() -> str:
    """Generate a unique ID in the format YYYY-MM-DD_HH-MM-SS"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")


def get_attribute_value(value, mode: str = "random"):
    """Get a value from an attribute that might have multiple options

    Args:
        value: The attribute value, which might contain multiple options separated by '|'
        mode: The selection mode, currently supports 'random'

    Returns:
        A single value selected according to the specified mode
    """
    if not value or not isinstance(value, str):
        return value

    if '|' in value:
        options = [opt.strip() for opt in value.split('|')]
        options = [opt for opt in options if opt]

        if not options:
            return ""

        if mode == "random":
            return random.choice(options)

    return value.strip()


def resolve_template_value(template: dict, path: str) -> str:
    """Resolve a dot-notation path to get a value from the template.

    Args:
        template: The template dictionary
        path: Dot-notation path like "subject.type" or "style"

    Returns:
        The resolved value after applying get_attribute_value(),
        or empty string if path doesn't exist.
    """
    parts = path.split(".")
    current = template

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return ""

    # Apply get_attribute_value to handle '|' random selection
    return get_attribute_value(current) if current else ""


def format_description(template: dict, format_string: str) -> str:
    """Format a description using a template and format string with placeholders.

    Args:
        template: The template dictionary containing values
        format_string: Format string with {path.to.field} placeholders

    Returns:
        Formatted description with placeholders replaced by values.
    """
    # Find all placeholders like {field} or {nested.field}
    placeholder_pattern = re.compile(r'\{([^}]+)\}')

    def replace_placeholder(match):
        path = match.group(1)
        return resolve_template_value(template, path)

    result = placeholder_pattern.sub(replace_placeholder, format_string)

    # Clean up multiple spaces
    result = re.sub(r'\s+', ' ', result)
    # Clean up empty parentheses like "()" or "( )"
    result = re.sub(r'\(\s*\)', '', result)
    # Clean up orphaned commas like ", ," or ",  ,"
    result = re.sub(r',\s*,', ',', result)
    # Clean up leading/trailing commas in phrases
    result = re.sub(r',\s*$', '', result)
    result = re.sub(r'^\s*,', '', result)
    # Clean up comma followed by period
    result = re.sub(r',\s*\.', '.', result)

    return result.strip()


def create_generic_description(template: dict) -> str:
    """Create a generic description by iterating over all template fields.

    Used as fallback when no description_format is provided.

    Args:
        template: The template dictionary

    Returns:
        A generic description in "key: value" format.
    """
    parts = []

    def process_value(key: str, value):
        """Process a single value, handling nested dicts."""
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                process_value(f"{key}.{sub_key}", sub_value)
        elif isinstance(value, str) and value:
            resolved = get_attribute_value(value)
            if resolved:
                parts.append(f"{key}: {resolved}")

    for key, value in template.items():
        # Skip description_format itself
        if key == "description_format":
            continue
        process_value(key, value)

    return ", ".join(parts) if parts else "Empty template"


def create_prompt_description(template: dict) -> str:
    """Create a description from the template attributes.

    If the template has a 'description_format' field, uses it as a format string
    with {path.to.field} placeholders. Otherwise, falls back to a generic
    key-value description.

    Args:
        template: The template dictionary

    Returns:
        A natural language description of the template.
    """
    try:
        # Check for custom format string
        if "description_format" in template:
            return format_description(template, template["description_format"])

        # Fallback to generic description
        return create_generic_description(template)
    except Exception as e:
        cprint(f"Error creating prompt description: {str(e)}", "red")
        return "Error creating description"


def count_words(text: str) -> int:
    """Count the number of words in a text string.

    Uses simple whitespace splitting, which works for both English and
    mixed Chinese/English text as a rough approximation.

    Args:
        text: The text to count words in.

    Returns:
        The number of words (whitespace-separated tokens).
    """
    if not text:
        return 0
    return len(text.split())


def print_enhancement_stats(original: str, enhanced: str) -> None:
    """Print statistics about prompt enhancement.

    Args:
        original: The original prompt before enhancement.
        enhanced: The enhanced prompt after LLM processing.
    """
    original_words = count_words(original)
    enhanced_words = count_words(enhanced)

    if original_words > 0:
        multiplier = enhanced_words / original_words
        cprint(
            f"Enhancement stats: {original_words} words → {enhanced_words} words ({multiplier:.1f}x)",
            "magenta"
        )
    else:
        cprint(f"Enhancement stats: 0 words → {enhanced_words} words", "magenta")


def create_fallback_prompt(base_description: str) -> str:
    """Create a fallback prompt when the LLM fails"""
    try:
        lighting = "golden hour lighting with warm tones"
        composition = "centered composition with rule of thirds"
        atmosphere = "serene and peaceful atmosphere"
        details = "fine details, high resolution, 8k quality"

        fallback_prompt = f"""
        {base_description}.
        {lighting}.
        {composition}.
        {atmosphere}.
        {details}.
        Natural skin tones, realistic textures, soft shadows,
        slight bokeh effect in background, photographic quality.
        """

        return fallback_prompt.strip()
    except Exception as e:
        cprint(f"Error creating fallback prompt: {str(e)}", "red")
        return base_description


def generate_detailed_prompt(
    template_description: str,
    instruction_template: str | None = None
) -> str:
    """Generate a detailed prompt using the configured LLM provider.

    Args:
        template_description: The base description from the template to expand.
        instruction_template: Optional custom instruction template. If None, loads from
                             DEFAULT_INSTRUCTION_FILE. Must contain {template_description}
                             placeholder.

    Returns:
        The detailed prompt generated by the LLM.
    """
    try:
        # Create LLM model based on provider configuration
        model, provider_name, model_name = create_llm_model()
        cprint(f"Using {provider_name} provider with model: {model_name}", "cyan")

        agent = Agent(model=model)

        # Use custom instruction or load from default file
        if instruction_template is None:
            instruction_template = load_instruction_file()

        # Substitute the placeholder with the actual description
        prompt_instruction = instruction_template.format(
            template_description=template_description
        )

        for attempt in range(MAX_RETRIES):
            try:
                cprint(f"Attempt {attempt+1}/{MAX_RETRIES}: Sending request to {provider_name}...", "cyan")
                result = agent.run_sync(prompt_instruction)
                cprint(f"Received response from {provider_name}!", "green")
                enhanced_prompt = result.output
                print_enhancement_stats(template_description, enhanced_prompt)
                return enhanced_prompt
            except Exception as e:
                cprint(f"Attempt {attempt+1}/{MAX_RETRIES} failed: {str(e)}", "yellow")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(1)

    except Exception as e:
        cprint(f"Error generating detailed prompt: {str(e)}", "red")
        cprint("Using fallback prompt generation method...", "yellow")
        fallback_result = create_fallback_prompt(template_description)
        print_enhancement_stats(template_description, fallback_result)
        return fallback_result


def save_prompts(prompts: list, output_file: str = DEFAULT_OUTPUT_FILE):
    """Save the generated prompts to the output file"""
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cprint(f"Saving prompts to {output_file}...", "cyan")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(prompts, f, indent=2)
        cprint(f"Prompts saved successfully to {output_file}!", "green")
    except Exception as e:
        cprint(f"Error saving prompts: {str(e)}", "red")
        raise


def generate_variations(template: dict, num_variations: int = 3) -> list:
    """Generate variations of the template

    Each variation will have randomly selected values for each attribute
    from the options available in the template.
    """
    variations = []

    def extract_options(value):
        if not value or not isinstance(value, str):
            return []
        return [opt.strip() for opt in value.split('|') if opt.strip()]

    subject_options = {}
    if "subject" in template and isinstance(template["subject"], dict):
        for key, value in template["subject"].items():
            subject_options[key] = extract_options(value)

    clothing_options = {}
    if "clothing" in template and isinstance(template["clothing"], dict):
        for key, value in template["clothing"].items():
            clothing_options[key] = extract_options(value)

    environment_options = extract_options(template.get("environment", ""))
    pose_options = extract_options(template.get("pose", ""))
    style_options = extract_options(template.get("style", ""))
    camera_angle_options = extract_options(template.get("camera_angle", ""))
    lighting_options = extract_options(template.get("lighting", ""))

    variations.append(template.copy())

    for i in range(1, num_variations):
        new_variation = {}

        if subject_options:
            new_variation["subject"] = {}
            for key, options in subject_options.items():
                if options:
                    new_variation["subject"][key] = random.choice(options)

        if clothing_options:
            new_variation["clothing"] = {}
            for key, options in clothing_options.items():
                if options:
                    new_variation["clothing"][key] = random.choice(options)

        if environment_options:
            new_variation["environment"] = random.choice(environment_options)

        if pose_options:
            new_variation["pose"] = random.choice(pose_options)

        if style_options:
            new_variation["style"] = random.choice(style_options)

        if camera_angle_options:
            new_variation["camera_angle"] = random.choice(camera_angle_options)

        if lighting_options:
            new_variation["lighting"] = random.choice(lighting_options)

        for key, value in template.items():
            if key not in new_variation and key not in ["subject", "clothing"]:
                new_variation[key] = value

        variations.append(new_variation)

    cprint(f"Created {len(variations)} variations with random attribute selections", "cyan")

    return variations


# Prompt sanitization utilities for use during image generation


def sanitize_prompt(prompt: str) -> str:
    """Sanitize the prompt to remove special tokens and problematic characters

    Args:
        prompt: The prompt to sanitize

    Returns:
        The sanitized prompt with problematic characters removed
    """
    if not prompt:
        return prompt

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

    for token in problematic_tokens:
        if token in sanitized:
            sanitized = sanitized.replace(token, ' ')
            cprint(f"Removed special token '{token}' from prompt", "yellow")

    original_len = len(sanitized)
    sanitized = re.sub(r'[^\s]*</w>', '', sanitized)
    if len(sanitized) != original_len:
        cprint("Removed </w> token patterns from prompt", "yellow")

    original_len = len(sanitized)
    sanitized = re.sub(r'<[^>]*>', '', sanitized)
    if len(sanitized) != original_len:
        cprint("Removed angle bracket tokens from prompt", "yellow")

    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    if sanitized != prompt:
        cprint("Prompt was sanitized to remove special tokens", "yellow")
        if len(sanitized) < 10:
            cprint("Warning: Sanitized prompt is very short. This may affect generation quality.", "red")

    return sanitized


def is_prompt_problematic(prompt: str) -> bool:
    """Check if a prompt is likely to cause issues with generation

    Args:
        prompt: The prompt to check

    Returns:
        bool: True if the prompt is likely problematic, False otherwise
    """
    if not prompt or prompt.strip() == "":
        return True

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

    clean_prompt = re.sub(r'[^\w\s]', '', prompt, flags=re.UNICODE).strip()
    if len(clean_prompt) < 3:
        return True

    return False
