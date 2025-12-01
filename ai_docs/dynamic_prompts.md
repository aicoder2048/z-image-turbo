# Dynamic Prompts Library

> A flexible and intuitive templating language for generating prompts for text-to-image systems like Stable Diffusion, Midjourney, and DALL-E 2.

**Repository:** https://github.com/adieyal/dynamicprompts
**License:** MIT
**Maintainer:** adieyal

---

## Installation

Basic installation:
```bash
pip install dynamicprompts
```

With optional features:
```bash
pip install "dynamicprompts[magicprompt, attentiongrabber]"
```

---

## Key Features

- Template syntax for creating multiple unique prompts from single templates
- Wildcard file support as placeholders in templates
- Wildcard library management (text, JSON, YAML formats)
- Exhaustive combinatorial prompt generation
- Variable assignment for reusable prompt snippets
- Magic Prompt integration for automatic modifier enhancement
- "I'm Feeling Lucky" feature using semantic search on Lexica.art
- Attention Grabber for emphasis on random phrases
- Jinja2-powered templating for advanced users

---

## Syntax Reference

### Variants

Variants randomly select from multiple options using curly brackets and pipes.

**Basic Syntax:**
```
{summer|autumn|winter|spring} is coming
```

**Weighted Options:**
Add weights using `::` to control selection frequency:
```
{0.5::summer|0.1::autumn|0.3::winter|0.1::spring}
```
Omitted weights default to 1. Weights are relative and needn't sum to 1.

**Multiple Selections:**
Use `N$$` to select multiple values without replacement:
```
{2$$chocolate|vanilla|strawberry}
```

**Custom Separators:**
```
{2$$ and $$chocolate|vanilla|strawberry}
```
Generates combinations like "chocolate and vanilla", "vanilla and strawberry", etc.

**Range Syntax:**
Specify lower and upper bounds for selection count:
```
{1-2$$ and $$chocolate|vanilla|strawberry}
```
- `{-2$$...}` - minimum to 2
- `{1-$$...}` - 1 to maximum available

---

### Wildcards

Wildcards inject values from files using double underscores `__`.

**Basic Syntax:**
```
__season__ is coming
```
References a file (e.g., `seasons.txt`) with one value per line.

**Wildcards in Variants:**
```
{2$$__flavours__}
```
Guarantees no duplicates when selecting multiple wildcard values.

**Variants in Wildcards:**
File content can include variants:
```
summer
{autumn|fall}
```

**Nested Wildcards:**
Wildcard files can reference other wildcards, creating hierarchies:
```
__people_of_the_world__
```
(which contains `__africa__`, etc.)

**Globbing:**
Use asterisks to match multiple files:
```
__colours*__
```
Matches `colours-cold.txt`, `colours-warm.txt`, etc.

**Recursive Globbing:**
```
__artists/**__
```
Matches any file nested under `artists/` directory.

---

### Wildcard File Formats

**Text Files (.txt):**
Simple format with one value per line; comments start with `#`:
```
# This is a comment
summer
autumn
winter
spring
```

**YAML Files:**
Supports hierarchical data:
```yaml
clothing:
  - T-shirt
  - Pants
artists:
  finnish:
    - Akseli Gallen-Kallela
```
Non-array entries are ignored. Weights: `2::red | 3::blue`

**JSON Files:**
Standard JSON with nested arrays:
```json
{
  "clothing": ["T-shirt", "Pants"],
  "artists": {
    "finnish": ["Akseli Gallen-Kallela"]
  }
}
```

---

### Variables

Store and reuse values throughout prompts.

**Assignment Syntax:**
```
${variable_name=value}
```

**Immediate Evaluation (`!`):**
Use `!` to evaluate once:
```
${season=!{summer|autumn|winter|spring}}
```
All uses reference the same selected value.

**Non-immediate Evaluation:**
Without `!`, expression re-evaluates each time:
```
${season={summer|autumn|winter|spring}}
```
Each usage may produce different results.

**Default Values:**
Prevents errors if variable undefined:
```
${season:summer}
```

**Preserving Existing Values (`?=`):**
Use `?=` to avoid overwriting existing variables:
```
${subject?=!{man|woman}}
```
Respects previously assigned values in nested templates.

---

### Parameterized Templates

Pass values to template files for dynamic generation.

**Basic Syntax:**
Create template file with variables, then invoke:
```
__season_clothes(season=winter)__
```
Only literal strings can be passed (not expressions).

**Default Values:**
Templates can specify fallbacks:
```
In ${season:summer}, I wear ${season:summer} shirts
```

---

### Whitespace and Comments

Complex prompts support readability features:
- Whitespace (newlines, tabs) is ignored in prompts
- Python-style `#` comments are supported

```
# Set season
${season={
    summer
    | autumn
    # | fall  (disabled)
    | winter
}}
```

**Note:** Wildcard `.txt` files treat newlines as delimiters, so use YAML format for readable multi-line values.

---

### Wrap Command

Wraps a template around another prompt, similar to styles.

**Syntax:**
```
%{wrapper with ..., modifiers$$inner_prompt}
```
Results in: `wrapper with inner_prompt, modifiers`

Supports various ellipsis characters (`...`, `…`, etc.). Both sides evaluate before wrapping.

---

### Samplers

Control how values are selected from variants and wildcards.

**Random Sampler (`~`):**
Picks values randomly (default for many generators):
```
{~red|green|blue} or __~colours__
```

**Combinatorial Sampler:**
Produces all possible combinations:
```
{red|green|blue} {square|circle}
```
Generates 6 outputs (3 × 2). Finite, non-repeating.

**Cyclical Sampler (`@`):**
Cycles through values in repeating pattern:
```
{@red|green|blue} {@square|circle}
```
Keeps paired values synchronized across multiple variants.

---

## Quick Reference Table

| Feature | Syntax | Example |
|---------|--------|---------|
| Variant | `{a\|b\|c}` | `{red\|blue}` |
| Weighted | `weight::value` | `0.5::red` |
| Multiple | `N$$option` | `2$$red\|blue` |
| Range | `N-M$$option` | `1-3$$red\|blue` |
| Wildcard | `__name__` | `__colors__` |
| Glob | `__pattern*__` | `__color*__` |
| Variable | `${name=value}` | `${x=red}` |
| Immediate | `${n=!expr}` | `${x=!__w__}` |
| Default | `${n:default}` | `${x:red}` |
| Preserve | `${n?=val}` | `${x?=red}` |
| Template | `__file(var=val)__` | `__tmpl(x=5)__` |
| Wrap | `%{wrap...$$inner}` | `%{A...$$B}` |
| Random | `{~a\|b}` | `{~red\|blue}` |
| Cyclical | `{@a\|b}` | `{@red\|blue}` |

---

## Python API Usage

### Random Generation

```python
from dynamicprompts.generators import RandomPromptGenerator

generator = RandomPromptGenerator()
prompts = generator.generate("I love {red|green|blue} roses", num_images=5)
```

### With Wildcards

```python
from pathlib import Path
from dynamicprompts.generators import RandomPromptGenerator
from dynamicprompts.wildcards.wildcard_manager import WildcardManager

wm = WildcardManager(Path("/path/to/wildcard/directory"))
generator = RandomPromptGenerator(wildcard_manager=wm)
prompts = generator.generate("I love __colours__ roses")
```

### Combinatorial Generation

```python
from dynamicprompts.generators import CombinatorialPromptGenerator

generator = CombinatorialPromptGenerator()
prompts = generator.generate("I love {red|green|blue} roses", max_prompts=5)
```

### With Random Seeds

```python
generator = RandomPromptGenerator(wildcard_manager=wm, seed=999)
prompts = generator.generate(
    "I love __colours__ roses",
    num_prompts=3,
    seeds=[1, 2, 3]
)
```

---

## Advanced Features

### Magic Prompt

Automatically enhances prompts using Gustavosta's MagicPrompt model (500MB download):

```python
from dynamicprompts.generators import RandomPromptGenerator
from dynamicprompts.generators.magicprompt import MagicPromptGenerator

generator = RandomPromptGenerator()
magic_generator = MagicPromptGenerator(generator, device=0)  # GPU device
```

Installation: `pip install "dynamicprompts[magicprompt]"`

### I'm Feeling Lucky

Queries Lexica.art for prompt inspiration:

```python
from dynamicprompts.generators import RandomPromptGenerator
from dynamicprompts.generators.feelinglucky import FeelingLuckyGenerator

generator = RandomPromptGenerator()
lucky_generator = FeelingLuckyGenerator(generator)
```

### Attention Generator

Adds random attention syntax for Stable Diffusion:

```python
from dynamicprompts.generators import RandomPromptGenerator
from dynamicprompts.generators.attentiongenerator import AttentionGenerator

generator = RandomPromptGenerator()
attention_generator = AttentionGenerator(generator)
```

Optionally install spacy for better NLP: `pip install spacy`

---

## Jinja2 Templates

For advanced templating scenarios:

```python
from dynamicprompts.generators import JinjaGenerator

generator = JinjaGenerator()
template = """
{% for colour in ['red', 'blue', 'green'] %}
    {% prompt %}I love {{ colour }} roses{% endprompt %}
{% endfor %}
"""
prompts = generator.generate(template)
```

---

## Syntax Customization

Modify delimiters to avoid conflicts with other systems:

```python
from dynamicprompts.generators import RandomPromptGenerator
from dynamicprompts.parser.config import ParserConfig

parser_config = ParserConfig(
    variant_start="<",
    variant_end=">",
    wildcard_wrap="**"
)
generator = RandomPromptGenerator(parser_config=parser_config)

# Now use: <red|green|blue> and **colours**
```

---

## Wildcard Collections

Pre-existing wildcard collections are available with ~80,000 entries across 1,900 files. These can be used with the sd-dynamic-prompts extension for Automatic1111.

---

## Related Projects

- **sd-dynamic-prompts**: Extension for Automatic1111's Stable Diffusion WebUI
- **Lexica.art**: Semantic search for prompt inspiration
- **MagicPrompt**: Model for automatic prompt enhancement
