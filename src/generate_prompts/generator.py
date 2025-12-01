#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prompt generator using Ollama/LLM to expand template descriptions."""

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
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

# Load environment variables
load_dotenv()

# Constants
DEFAULT_TEMPLATE_FILE = "input/prompt_template.json"
DEFAULT_OUTPUT_FILE = "input/prompts/prompts.json"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:27b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
MAX_RETRIES = 3


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


def create_prompt_description(template: dict) -> str:
    """Create a description from the template attributes"""
    try:
        subject = template.get("subject", {})
        clothing = template.get("clothing", {})
        environment = template.get("environment", "")
        style = template.get("style", "")
        pose = template.get("pose", "")
        camera_angle = template.get("camera_angle", "")
        lighting = template.get("lighting", "")

        subject_type = get_attribute_value(subject.get("type", ""))
        age = get_attribute_value(subject.get("age", ""))
        ethnicity = get_attribute_value(subject.get("ethnicity", ""))
        expression = get_attribute_value(subject.get("expression", ""))

        top = get_attribute_value(clothing.get("top", ""))
        bottom = get_attribute_value(clothing.get("bottom", ""))
        shoes = get_attribute_value(clothing.get("shoes", ""))

        clothing_desc = f"wearing {top}, {bottom}, {shoes}"

        environment = get_attribute_value(environment)
        style = get_attribute_value(style)
        pose = get_attribute_value(pose)
        camera_angle = get_attribute_value(camera_angle)
        lighting = get_attribute_value(lighting)

        description = f"A {subject_type} who is {age}, {ethnicity}, and {expression}, {clothing_desc} {pose} in {environment} with {style} style"

        if camera_angle:
            description += f", {camera_angle} camera angle"

        if lighting:
            description += f", {lighting} lighting"

        return description.strip()
    except Exception as e:
        cprint(f"Error creating prompt description: {str(e)}", "red")
        return "Error creating description"


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


def generate_detailed_prompt(template_description: str) -> str:
    """Generate a detailed prompt using Ollama model"""
    try:
        cprint(f"Connecting to Ollama model at {OLLAMA_URL}...", "cyan")

        ollama_model = OpenAIModel(
            model_name=OLLAMA_MODEL,
            provider=OpenAIProvider(base_url=OLLAMA_URL)
        )

        agent = Agent(model=ollama_model)

        prompt_instruction = f"""
        Create a detailed image generation prompt based on the following description:

        {template_description}

        Expand this into a comprehensive, highly descriptive, and very-detailed prompt that would help an AI image generator
        create a high-quality image. Include specific details about lighting, composition,
        atmosphere, and any other relevant elements. Make it vivid and descriptive.

        Important: When describing the person, make sure to naturally incorporate their ethnicity
        (English) as part of the description in a way that flows naturally, rather than listing it
        as a separate attribute.

        Important: Just return the resulting prompt, do not repeat the request and do not include any other text.
        """

        for attempt in range(MAX_RETRIES):
            try:
                cprint(f"Attempt {attempt+1}/{MAX_RETRIES}: Sending request to Ollama model...", "cyan")
                result = agent.run_sync(prompt_instruction)
                cprint("Received response from Ollama model!", "green")
                return result.output
            except Exception as e:
                cprint(f"Attempt {attempt+1}/{MAX_RETRIES} failed: {str(e)}", "yellow")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(1)

    except Exception as e:
        cprint(f"Error generating detailed prompt: {str(e)}", "red")
        cprint("Using fallback prompt generation method...", "yellow")
        return create_fallback_prompt(template_description)


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

    original_len = len(sanitized)
    sanitized = re.sub(r'[^\x00-\x7F]+', ' ', sanitized)
    if len(sanitized) != original_len:
        cprint("Removed non-ASCII characters from prompt", "yellow")

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

    clean_prompt = re.sub(r'[^\w\s]', '', prompt).strip()
    if len(clean_prompt) < 5:
        return True

    return False
