#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for generate_prompts module."""

import json
import pytest
from pathlib import Path

from generate_prompts.generator import (
    get_attribute_value,
    create_prompt_description,
    create_fallback_prompt,
    generate_variations,
    sanitize_prompt,
    is_prompt_problematic,
    generate_prompt_id,
    load_instruction_file,
    DEFAULT_INSTRUCTION_FILE,
)


class TestGetAttributeValue:
    """Tests for get_attribute_value function."""

    def test_single_value(self):
        """Test single value without pipe separator."""
        assert get_attribute_value("summer") == "summer"

    def test_multiple_options_returns_one(self):
        """Test that multiple options return one of the options."""
        value = "summer|autumn|winter|spring"
        result = get_attribute_value(value)
        assert result in ["summer", "autumn", "winter", "spring"]

    def test_empty_value(self):
        """Test empty value returns as-is."""
        assert get_attribute_value("") == ""
        assert get_attribute_value(None) is None

    def test_strips_whitespace(self):
        """Test that whitespace is stripped from options."""
        value = " summer | autumn | winter "
        result = get_attribute_value(value)
        assert result in ["summer", "autumn", "winter"]
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_non_string_value(self):
        """Test non-string values are returned as-is."""
        assert get_attribute_value(123) == 123
        assert get_attribute_value(["a", "b"]) == ["a", "b"]


class TestCreatePromptDescription:
    """Tests for create_prompt_description function."""

    def test_basic_template(self):
        """Test basic template description creation."""
        template = {
            "subject": {
                "type": "person",
                "age": "30 years old",
                "ethnicity": "English",
                "expression": "smile",
            },
            "clothing": {
                "top": "t-shirt",
                "bottom": "jeans",
                "shoes": "sneakers",
            },
            "environment": "park",
            "style": "photo-realistic",
            "pose": "casual pose",
            "camera_angle": "medium shot",
            "lighting": "natural",
        }
        description = create_prompt_description(template)
        assert "person" in description
        assert "30 years old" in description
        assert "t-shirt" in description
        assert "park" in description
        assert "photo-realistic" in description

    def test_empty_template(self):
        """Test empty template handling."""
        description = create_prompt_description({})
        assert description  # Should return some string, not raise error


class TestCreateFallbackPrompt:
    """Tests for create_fallback_prompt function."""

    def test_fallback_includes_base_description(self):
        """Test that fallback prompt includes base description."""
        base = "A person in a park"
        result = create_fallback_prompt(base)
        assert base in result

    def test_fallback_includes_enhancements(self):
        """Test that fallback prompt includes quality enhancements."""
        result = create_fallback_prompt("test")
        assert "lighting" in result.lower()
        assert "8k" in result or "quality" in result.lower()


class TestGenerateVariations:
    """Tests for generate_variations function."""

    def test_generates_correct_number(self):
        """Test correct number of variations generated."""
        template = {
            "subject": {"type": "person|animal"},
            "environment": "indoor|outdoor",
        }
        variations = generate_variations(template, num_variations=5)
        assert len(variations) == 5

    def test_first_variation_is_original(self):
        """Test first variation is the original template."""
        template = {
            "subject": {"type": "person"},
            "environment": "indoor",
        }
        variations = generate_variations(template, num_variations=3)
        assert variations[0] == template

    def test_variations_have_required_keys(self):
        """Test all variations have the required keys."""
        template = {
            "subject": {"type": "person|animal", "age": "young|old"},
            "environment": "indoor|outdoor",
            "style": "realistic",
        }
        variations = generate_variations(template, num_variations=3)
        for var in variations:
            assert "subject" in var or "environment" in var or "style" in var


class TestSanitizePrompt:
    """Tests for sanitize_prompt function."""

    def test_clean_prompt_unchanged(self):
        """Test clean prompt remains unchanged."""
        prompt = "A beautiful sunset over the ocean"
        result = sanitize_prompt(prompt)
        assert result == prompt

    def test_removes_special_tokens(self):
        """Test removal of special tokens."""
        prompt = "A sunset</w> over the ocean"
        result = sanitize_prompt(prompt)
        assert "</w>" not in result

    def test_removes_angle_bracket_tokens(self):
        """Test removal of angle bracket tokens."""
        prompt = "A sunset <|endoftext|> over the ocean"
        result = sanitize_prompt(prompt)
        assert "<|endoftext|>" not in result

    def test_removes_problematic_unicode(self):
        """Test removal of problematic unicode characters like em dashes and curly quotes."""
        prompt = "A beautiful sunset — over the ocean"
        result = sanitize_prompt(prompt)
        # Em dash should be replaced with space
        assert "—" not in result
        assert "sunset" in result
        assert "ocean" in result

    def test_preserves_chinese_characters(self):
        """Test that Chinese characters are preserved."""
        prompt = "一只猫在太空中漂浮"
        result = sanitize_prompt(prompt)
        assert result == prompt

    def test_preserves_mixed_language_prompt(self):
        """Test that mixed Chinese and English prompts are preserved."""
        prompt = "一只 cute cat 在太空中漂浮"
        result = sanitize_prompt(prompt)
        assert "一只" in result
        assert "cute cat" in result
        assert "太空中漂浮" in result

    def test_normalizes_whitespace(self):
        """Test whitespace normalization."""
        prompt = "A   beautiful    sunset"
        result = sanitize_prompt(prompt)
        assert "   " not in result

    def test_empty_prompt(self):
        """Test empty prompt handling."""
        assert sanitize_prompt("") == ""
        assert sanitize_prompt(None) is None


class TestIsPromptProblematic:
    """Tests for is_prompt_problematic function."""

    def test_clean_prompt_not_problematic(self):
        """Test clean prompt is not problematic."""
        assert not is_prompt_problematic("A beautiful sunset over the ocean")

    def test_empty_prompt_problematic(self):
        """Test empty prompt is problematic."""
        assert is_prompt_problematic("")
        assert is_prompt_problematic("   ")

    def test_special_tokens_problematic(self):
        """Test prompts with special tokens are problematic."""
        assert is_prompt_problematic("test</w>")
        assert is_prompt_problematic("<|endoftext|>")

    def test_angle_brackets_problematic(self):
        """Test prompts with angle brackets are problematic."""
        assert is_prompt_problematic("test <tag> test")

    def test_double_brackets_problematic(self):
        """Test prompts with double brackets are problematic."""
        assert is_prompt_problematic("test [[token]] test")
        assert is_prompt_problematic("test {{token}} test")

    def test_very_short_prompt_problematic(self):
        """Test very short prompts are problematic."""
        assert is_prompt_problematic("hi")
        assert is_prompt_problematic("!!!")

    def test_chinese_prompt_not_problematic(self):
        """Test that Chinese prompts are not marked as problematic."""
        assert not is_prompt_problematic("一只猫")
        assert not is_prompt_problematic("一只猫在太空中漂浮")

    def test_mixed_language_prompt_not_problematic(self):
        """Test that mixed Chinese and English prompts are not problematic."""
        assert not is_prompt_problematic("一只 cute cat 在太空")


class TestGeneratePromptId:
    """Tests for generate_prompt_id function."""

    def test_format(self):
        """Test ID format is correct."""
        prompt_id = generate_prompt_id()
        # Format: YYYY-MM-DD_HH-MM-SS
        parts = prompt_id.split("_")
        assert len(parts) == 2
        date_part = parts[0].split("-")
        time_part = parts[1].split("-")
        assert len(date_part) == 3  # YYYY, MM, DD
        assert len(time_part) == 3  # HH, MM, SS

    def test_uniqueness(self):
        """Test IDs are unique (within reasonable time)."""
        import time
        id1 = generate_prompt_id()
        time.sleep(1.1)  # Sleep just over 1 second
        id2 = generate_prompt_id()
        assert id1 != id2


class TestLoadInstructionFile:
    """Tests for load_instruction_file function."""

    def test_load_default_instruction_file(self):
        """Test loading the default instruction file."""
        instruction = load_instruction_file()
        assert "{template_description}" in instruction
        assert "image generation prompt" in instruction.lower()

    def test_load_default_instruction_file_explicit_path(self):
        """Test loading instruction file with explicit default path."""
        instruction = load_instruction_file(DEFAULT_INSTRUCTION_FILE)
        assert "{template_description}" in instruction

    def test_load_custom_instruction_file(self, tmp_path):
        """Test loading a custom instruction file."""
        custom_instruction = "Generate a prompt for: {template_description}\nMake it creative!"
        instruction_file = tmp_path / "custom_instruction.txt"
        instruction_file.write_text(custom_instruction, encoding="utf-8")

        instruction = load_instruction_file(str(instruction_file))
        assert instruction == custom_instruction

    def test_load_instruction_file_missing_placeholder(self, tmp_path):
        """Test that loading file without placeholder raises ValueError."""
        invalid_instruction = "Generate a prompt without the required placeholder"
        instruction_file = tmp_path / "invalid_instruction.txt"
        instruction_file.write_text(invalid_instruction, encoding="utf-8")

        with pytest.raises(ValueError) as exc_info:
            load_instruction_file(str(instruction_file))
        assert "{template_description}" in str(exc_info.value)

    def test_load_instruction_file_not_found(self):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_instruction_file("/nonexistent/path/instruction.txt")

    def test_load_instruction_file_with_unicode(self, tmp_path):
        """Test loading instruction file with unicode content."""
        unicode_instruction = "为以下描述生成详细的提示词: {template_description}\n使用中英文混合。"
        instruction_file = tmp_path / "unicode_instruction.txt"
        instruction_file.write_text(unicode_instruction, encoding="utf-8")

        instruction = load_instruction_file(str(instruction_file))
        assert instruction == unicode_instruction
        assert "中英文" in instruction

    def test_load_instruction_file_multiple_placeholders(self, tmp_path):
        """Test loading file with multiple placeholders works correctly."""
        multi_placeholder = """
        First: {template_description}
        Second reference: {template_description}
        End of instruction.
        """
        instruction_file = tmp_path / "multi_placeholder.txt"
        instruction_file.write_text(multi_placeholder, encoding="utf-8")

        instruction = load_instruction_file(str(instruction_file))
        assert instruction.count("{template_description}") == 2

    def test_instruction_template_substitution(self, tmp_path):
        """Test that instruction template can be used with .format()."""
        template_instruction = "Create prompt for: {template_description}. Style: detailed."
        instruction_file = tmp_path / "format_test.txt"
        instruction_file.write_text(template_instruction, encoding="utf-8")

        instruction = load_instruction_file(str(instruction_file))
        result = instruction.format(template_description="a cat in space")
        assert "a cat in space" in result
        assert "{template_description}" not in result
