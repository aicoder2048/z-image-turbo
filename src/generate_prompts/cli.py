#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command-line interface for prompt generation."""

import argparse
import time
from termcolor import cprint

from .generator import (
    load_template,
    load_existing_prompts,
    load_instruction_file,
    generate_prompt_id,
    create_prompt_description,
    generate_detailed_prompt,
    save_prompts,
    generate_variations,
    DEFAULT_TEMPLATE_FILE,
    DEFAULT_OUTPUT_FILE,
    DEFAULT_INSTRUCTION_FILE,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate detailed prompts from templates using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run generate_prompts                         # Interactive mode
  uv run generate_prompts -n 5                    # Generate 5 variations
  uv run generate_prompts -t custom.json          # Use custom template
  uv run generate_prompts -o output/prompts.json  # Custom output file
  uv run generate_prompts -i custom_instruction.txt  # Use custom instruction
        """,
    )
    parser.add_argument(
        "-t", "--template",
        default=DEFAULT_TEMPLATE_FILE,
        help=f"Template file path (default: {DEFAULT_TEMPLATE_FILE})",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output file path (default: {DEFAULT_OUTPUT_FILE})",
    )
    parser.add_argument(
        "-n", "--num-variations",
        type=int,
        default=0,
        help="Number of variations to generate (0 for interactive mode)",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser.add_argument(
        "-i", "--instruction",
        default=None,
        help=f"Path to custom instruction file (default: {DEFAULT_INSTRUCTION_FILE})",
    )
    return parser.parse_args()


def main():
    """Main function to generate prompts"""
    args = parse_args()

    try:
        cprint("Starting prompt generation process...", "yellow")
        cprint("Random selection feature: Use '|' to separate multiple options for any attribute.", "cyan")
        cprint("Example: 'ethnicity': 'English | Russian' will randomly select one of these options.", "cyan")

        # Load the template
        template = load_template(args.template)

        # Load custom instruction if provided, otherwise use default
        instruction_template = None
        if args.instruction:
            instruction_template = load_instruction_file(args.instruction)
        else:
            # Load default instruction file
            instruction_template = load_instruction_file()

        # Load existing prompts
        existing_prompts = load_existing_prompts(args.output)

        # Determine if we should generate variations
        if args.num_variations > 0:
            generate_variations_flag = True
            num_variations = args.num_variations
        elif args.yes:
            generate_variations_flag = False
            num_variations = 1
        else:
            generate_variations_input = input("Generate variations of the template? (y/n, default: n): ").strip().lower()
            generate_variations_flag = generate_variations_input == 'y'
            num_variations = 3

            if generate_variations_flag:
                num_input = input("How many variations to generate? (default: 3): ").strip()
                if num_input:
                    num_variations = int(num_input)

        if generate_variations_flag:
            templates = generate_variations(template, num_variations)
            cprint(f"Generated {len(templates)} template variations.", "green")

            # Print a sample of the variations
            cprint("\nSample of template variations:", "cyan")
            for i, var_template in enumerate(templates[:min(3, len(templates))]):
                cprint(f"\nVariation {i+1}:", "cyan", attrs=["bold"])

                if "subject" in var_template and isinstance(var_template["subject"], dict):
                    cprint("  Subject:", "cyan")
                    for key, value in var_template["subject"].items():
                        cprint(f"    {key}: {value}", "cyan")

                if "clothing" in var_template and isinstance(var_template["clothing"], dict):
                    cprint("  Clothing:", "cyan")
                    for key, value in var_template["clothing"].items():
                        cprint(f"    {key}: {value}", "cyan")

                other_attrs = [k for k in var_template.keys() if k not in ["subject", "clothing"]]
                if other_attrs:
                    cprint("  Other attributes:", "cyan")
                    for key in other_attrs:
                        cprint(f"    {key}: {var_template[key]}", "cyan")

                if i == 0:
                    cprint("\nRandom selection preview:", "green")
                    description = create_prompt_description(var_template)
                    cprint(f"Sample description: {description}", "green")
                    cprint("(Each time a prompt is generated, different options may be selected)", "green")
        else:
            templates = [template]

        # Process each template
        new_prompts = []
        for i, current_template in enumerate(templates):
            cprint(f"\nProcessing template {i+1}/{len(templates)}...", "yellow")

            description = create_prompt_description(current_template)
            cprint(f"Created base description: {description}", "cyan")

            detailed_prompt = generate_detailed_prompt(description, instruction_template)
            cprint("Generated detailed prompt!", "green")

            prompt_id = generate_prompt_id()
            prompt = {
                "id": prompt_id,
                "description": detailed_prompt
            }

            new_prompts.append(prompt)

            if i < len(templates) - 1:
                time.sleep(1)

        # Combine existing and new prompts
        all_prompts = existing_prompts + new_prompts

        # Save all prompts
        save_prompts(all_prompts, args.output)

        cprint(f"\nSuccessfully generated {len(new_prompts)} new prompts!", "green")
        cprint(f"Total prompts in {args.output}: {len(all_prompts)}", "green")

        return 0

    except KeyboardInterrupt:
        cprint("\nOperation cancelled by user.", "yellow")
        return 1
    except Exception as e:
        cprint(f"Error in main process: {str(e)}", "red")
        return 1


if __name__ == "__main__":
    main()
