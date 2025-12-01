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

    def test_removes_non_ascii(self):
        """Test removal of non-ASCII characters."""
        prompt = "A beautiful sunset — over the océan"
        result = sanitize_prompt(prompt)
        # Should only contain ASCII
        assert all(ord(c) < 128 for c in result)

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
