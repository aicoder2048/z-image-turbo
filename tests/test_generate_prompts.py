#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for generate_prompts module."""

import json
import pytest
from pathlib import Path

from generate_prompts.generator import (
    get_attribute_value,
    resolve_template_value,
    format_description,
    create_generic_description,
    create_prompt_description,
    create_fallback_prompt,
    generate_variations,
    sanitize_prompt,
    is_prompt_problematic,
    generate_prompt_id,
    load_instruction_file,
    create_llm_model,
    DEFAULT_INSTRUCTION_FILE,
)
from generate_prompts import generator as generator_module


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


class TestResolveTemplateValue:
    """Tests for resolve_template_value function."""

    def test_simple_field(self):
        """Test simple field access."""
        template = {"style": "photo-realistic"}
        assert resolve_template_value(template, "style") == "photo-realistic"

    def test_nested_field(self):
        """Test nested field access with dot notation."""
        template = {"subject": {"type": "person", "age": "30"}}
        assert resolve_template_value(template, "subject.type") == "person"
        assert resolve_template_value(template, "subject.age") == "30"

    def test_missing_field(self):
        """Test missing field returns empty string."""
        template = {"style": "photo-realistic"}
        assert resolve_template_value(template, "missing") == ""
        assert resolve_template_value(template, "subject.type") == ""

    def test_with_pipe_selection(self):
        """Test that pipe-separated values are resolved."""
        template = {"style": "realistic | cartoon"}
        result = resolve_template_value(template, "style")
        assert result in ["realistic", "cartoon"]

    def test_deep_nesting(self):
        """Test deeply nested field access."""
        template = {"a": {"b": {"c": "deep_value"}}}
        assert resolve_template_value(template, "a.b.c") == "deep_value"

    def test_empty_value(self):
        """Test empty value returns empty string."""
        template = {"style": ""}
        assert resolve_template_value(template, "style") == ""


class TestFormatDescription:
    """Tests for format_description function."""

    def test_basic_placeholder(self):
        """Test basic placeholder replacement."""
        template = {"style": "realistic", "environment": "park"}
        format_str = "A {style} image in a {environment}"
        result = format_description(template, format_str)
        assert result == "A realistic image in a park"

    def test_nested_placeholder(self):
        """Test nested placeholder replacement."""
        template = {"subject": {"type": "person", "expression": "smile"}}
        format_str = "A {subject.type} with a {subject.expression}"
        result = format_description(template, format_str)
        assert result == "A person with a smile"

    def test_missing_placeholder_cleanup(self):
        """Test that missing placeholders are cleaned up."""
        template = {"style": "realistic"}
        format_str = "A {style} image ({missing})"
        result = format_description(template, format_str)
        # Empty parentheses should be removed
        assert "()" not in result
        assert "realistic" in result

    def test_multiple_spaces_cleanup(self):
        """Test that multiple spaces are normalized."""
        template = {"a": "value"}
        format_str = "Test  {missing}  text"
        result = format_description(template, format_str)
        assert "  " not in result

    def test_comma_cleanup(self):
        """Test that orphaned commas are cleaned up."""
        template = {"a": "value"}
        format_str = "Test, {missing}, more"
        result = format_description(template, format_str)
        assert ", ," not in result


class TestCreateGenericDescription:
    """Tests for create_generic_description function."""

    def test_simple_template(self):
        """Test generic description with simple fields."""
        template = {"style": "realistic", "environment": "park"}
        result = create_generic_description(template)
        assert "style: realistic" in result
        assert "environment: park" in result

    def test_nested_template(self):
        """Test generic description with nested fields."""
        template = {"subject": {"type": "person", "age": "30"}}
        result = create_generic_description(template)
        assert "subject.type: person" in result
        assert "subject.age: 30" in result

    def test_empty_template(self):
        """Test empty template returns placeholder text."""
        result = create_generic_description({})
        assert result == "Empty template"

    def test_skips_description_format(self):
        """Test that description_format field is skipped."""
        template = {"description_format": "ignore this", "style": "realistic"}
        result = create_generic_description(template)
        assert "description_format" not in result
        assert "style: realistic" in result


class TestCreatePromptDescription:
    """Tests for create_prompt_description function."""

    def test_with_format_string(self):
        """Test template with description_format uses it."""
        template = {
            "description_format": "A {subject.type} in {environment}",
            "subject": {"type": "person"},
            "environment": "park",
        }
        description = create_prompt_description(template)
        assert description == "A person in park"

    def test_without_format_string_fallback(self):
        """Test template without description_format uses generic fallback."""
        template = {
            "subject": {"type": "person"},
            "environment": "park",
        }
        description = create_prompt_description(template)
        assert "subject.type: person" in description
        assert "environment: park" in description

    def test_basic_template_with_format(self):
        """Test basic template with description_format."""
        template = {
            "description_format": "A {subject.type} who is {subject.age}, {subject.ethnicity}, with {subject.expression} expression, wearing {clothing.top}, {clothing.bottom}, {clothing.shoes}, {pose} in {environment} with {style} style, {camera_angle} camera angle, {lighting} lighting",
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

    def test_marvel_style_template(self):
        """Test Marvel-style template with different structure."""
        template = {
            "description_format": "A {subject.type} ({subject.identity}) with {subject.attributes}, {subject.expression} expression, wearing {clothing.top} and {clothing.bottom}, in {pose} at {environment}, {style} style, {camera_angle}, {lighting} lighting",
            "subject": {
                "type": "Iron Man",
                "identity": "Avenger",
                "attributes": "armored suit",
                "expression": "determined",
            },
            "clothing": {
                "top": "armor plating",
                "bottom": "armored leggings",
            },
            "pose": "hero landing pose",
            "environment": "battlefield",
            "style": "cinematic",
            "camera_angle": "dynamic low angle",
            "lighting": "dramatic",
        }
        description = create_prompt_description(template)
        assert "Iron Man" in description
        assert "Avenger" in description
        assert "armored suit" in description
        assert "battlefield" in description


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


class TestCreateLlmModel:
    """Tests for create_llm_model function."""

    def test_create_llm_model_ollama_default(self, monkeypatch):
        """Test default provider is Ollama."""
        monkeypatch.setattr(generator_module, "LLM_PROVIDER", "ollama")
        monkeypatch.setattr(generator_module, "OLLAMA_MODEL", "test-model")
        monkeypatch.setattr(generator_module, "OLLAMA_URL", "http://localhost:11434/v1")

        model, provider_name, model_name = create_llm_model()
        assert provider_name == "Ollama"
        assert model_name == "test-model"
        assert model is not None

    def test_create_llm_model_openai(self, monkeypatch):
        """Test OpenAI provider creation."""
        monkeypatch.setattr(generator_module, "LLM_PROVIDER", "openai")
        monkeypatch.setattr(generator_module, "OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setattr(generator_module, "OPENAI_MODEL", "gpt-4o-mini")
        monkeypatch.setattr(generator_module, "OPENAI_BASE_URL", "https://api.openai.com/v1")

        model, provider_name, model_name = create_llm_model()
        assert provider_name == "OpenAI"
        assert model_name == "gpt-4o-mini"
        assert model is not None

    def test_create_llm_model_grok(self, monkeypatch):
        """Test Grok provider creation."""
        monkeypatch.setattr(generator_module, "LLM_PROVIDER", "grok")
        monkeypatch.setattr(generator_module, "GROK_API_KEY", "xai-test-key")
        monkeypatch.setattr(generator_module, "GROK_MODEL", "grok-3-mini")
        monkeypatch.setattr(generator_module, "GROK_BASE_URL", "https://api.x.ai/v1")

        model, provider_name, model_name = create_llm_model()
        assert provider_name == "Grok (xAI)"
        assert model_name == "grok-3-mini"
        assert model is not None

    def test_create_llm_model_openai_missing_api_key(self, monkeypatch):
        """Test error for missing OpenAI API key."""
        monkeypatch.setattr(generator_module, "LLM_PROVIDER", "openai")
        monkeypatch.setattr(generator_module, "OPENAI_API_KEY", "")

        with pytest.raises(ValueError) as exc_info:
            create_llm_model()
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_create_llm_model_grok_missing_api_key(self, monkeypatch):
        """Test error for missing Grok API key."""
        monkeypatch.setattr(generator_module, "LLM_PROVIDER", "grok")
        monkeypatch.setattr(generator_module, "GROK_API_KEY", "")

        with pytest.raises(ValueError) as exc_info:
            create_llm_model()
        assert "GROK_API_KEY" in str(exc_info.value)

    def test_create_llm_model_invalid_provider(self, monkeypatch):
        """Test error for unknown provider."""
        monkeypatch.setattr(generator_module, "LLM_PROVIDER", "invalid_provider")

        with pytest.raises(ValueError) as exc_info:
            create_llm_model()
        assert "Invalid LLM_PROVIDER" in str(exc_info.value)
        assert "invalid_provider" in str(exc_info.value)

    def test_create_llm_model_whitespace_api_key(self, monkeypatch):
        """Test error for whitespace-only API key."""
        monkeypatch.setattr(generator_module, "LLM_PROVIDER", "openai")
        monkeypatch.setattr(generator_module, "OPENAI_API_KEY", "   ")

        with pytest.raises(ValueError) as exc_info:
            create_llm_model()
        assert "OPENAI_API_KEY" in str(exc_info.value)
