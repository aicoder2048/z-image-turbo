# Feature: Grok LLM Provider Support

## Feature Description
Add support for xAI's Grok API as an additional LLM provider for generating detailed prompts, alongside the existing Ollama support. Since Grok's API is OpenAI-compatible (uses the same endpoint structure as OpenAI), this can be implemented by adding a provider selection mechanism that allows users to choose between Ollama, OpenAI, and Grok via environment variables or CLI arguments.

## User Story
As a **user of generate_prompts**
I want to **use xAI's Grok model for generating detailed prompts**
So that **I can leverage Grok's advanced reasoning and language capabilities, especially when I don't have access to a local Ollama server or prefer cloud-based LLM services**

## Problem Statement
Currently, the `generate_prompts` module only supports Ollama as the LLM backend. Users who:
- Don't have Ollama installed locally
- Prefer cloud-based LLM services
- Want to use Grok's specific capabilities (advanced reasoning, live search)
- Already have xAI API credits

...cannot use the prompt generation feature without setting up Ollama.

## Solution Statement
Implement a provider abstraction that allows users to select between different LLM backends via the `LLM_PROVIDER` environment variable:
- `ollama` (default) - Local Ollama server
- `openai` - OpenAI API
- `grok` - xAI Grok API (OpenAI-compatible)

Since Grok and OpenAI use the same API structure, we can use `OpenAIModel` with different `base_url` configurations. The provider selection will be handled through environment variables with sensible defaults.

## Relevant Files
Use these files to implement the feature:

- `src/generate_prompts/generator.py` - Contains the `generate_detailed_prompt()` function that creates the LLM model. This is where we'll add provider selection logic.
- `src/generate_prompts/cli.py` - CLI module. May need updates to show which provider is being used.
- `tests/test_generate_prompts.py` - Tests for the generator module. We'll add tests for provider creation.
- `README.md` - Documentation. We'll add usage examples for the new providers.

### New Files
- `.env.example` - Example environment file showing all provider configurations

## Implementation Plan

### Phase 1: Foundation
1. Define environment variables for each provider (API key, model, base URL)
2. Create a provider factory function that returns the appropriate model based on configuration
3. Keep Ollama as the default for backward compatibility

### Phase 2: Core Implementation
1. Create `create_llm_model()` function that handles provider selection
2. Support three providers: ollama, openai, grok
3. Add proper error handling for missing API keys

### Phase 3: Integration
1. Update `generate_detailed_prompt()` to use the new provider factory
2. Add provider info to CLI output
3. Update documentation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Environment Variable Constants
- Add constants for LLM_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
- Add constants for GROK_API_KEY, GROK_MODEL, GROK_BASE_URL
- Default LLM_PROVIDER to "ollama" for backward compatibility

### Step 2: Create Provider Factory Function
- Create `create_llm_model()` function in `generator.py`
- Implement logic to create appropriate model based on LLM_PROVIDER
- For "ollama": Use existing OpenAIModel with OLLAMA_URL
- For "openai": Use OpenAIModel with OpenAI defaults
- For "grok": Use OpenAIModel with Grok base URL (https://api.x.ai/v1)
- Raise clear error if required API key is missing

### Step 3: Update generate_detailed_prompt() Function
- Replace direct model creation with call to `create_llm_model()`
- Update log messages to show which provider is being used
- Maintain backward compatibility with existing Ollama setup

### Step 4: Create .env.example File
- Document all environment variables for each provider
- Include examples and comments explaining each option

### Step 5: Add Unit Tests
- Test `create_llm_model()` returns correct model type for each provider
- Test error handling for missing API keys
- Test default provider selection

### Step 6: Update README Documentation
- Add section explaining multi-provider support
- Document environment variables for each provider
- Provide usage examples for Grok and OpenAI

### Step 7: Run Validation Commands
- Run all tests to ensure zero regressions
- Test with mock/stubbed providers

## Testing Strategy

### Unit Tests
- `test_create_llm_model_ollama_default`: Test default provider is Ollama
- `test_create_llm_model_openai`: Test OpenAI provider creation
- `test_create_llm_model_grok`: Test Grok provider creation
- `test_create_llm_model_missing_api_key`: Test error for missing API key
- `test_create_llm_model_invalid_provider`: Test error for unknown provider

### Integration Tests
- Test full prompt generation flow with mocked LLM responses

### Edge Cases
- Missing API key for OpenAI/Grok providers
- Invalid LLM_PROVIDER value
- Empty or whitespace-only API keys
- Network errors (covered by existing retry logic)

## Acceptance Criteria
1. Users can set `LLM_PROVIDER=grok` to use Grok API
2. Users can set `LLM_PROVIDER=openai` to use OpenAI API
3. Default behavior (no LLM_PROVIDER set) uses Ollama (backward compatible)
4. Clear error messages when API keys are missing
5. CLI output shows which provider is being used
6. All existing tests pass without modification
7. New tests cover provider selection logic
8. README.md documents all provider options

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest tests/ -v` - Run all tests to validate zero regressions
- `uv run generate_prompts --help` - Verify CLI still works

## Notes
- Grok API is OpenAI-compatible, so we use `OpenAIModel` with `base_url="https://api.x.ai/v1"`
- OpenAI API uses default base URL, so we only need to set the API key
- Environment variables follow the pattern: `{PROVIDER}_{SETTING}` (e.g., GROK_API_KEY, GROK_MODEL)
- Default models:
  - Ollama: gemma3:27b (existing default)
  - OpenAI: gpt-4o-mini
  - Grok: grok-3-mini
- Future consideration: Add CLI argument `--provider` for per-command override
- Reference: [xAI API Documentation](https://docs.x.ai/docs/api-reference)

## Environment Variables Reference

| Variable | Provider | Description | Default |
|----------|----------|-------------|---------|
| LLM_PROVIDER | All | Provider selection: ollama, openai, grok | ollama |
| OLLAMA_URL | Ollama | Ollama server URL | http://localhost:11434/v1 |
| OLLAMA_MODEL | Ollama | Ollama model name | gemma3:27b |
| OPENAI_API_KEY | OpenAI | OpenAI API key | (required) |
| OPENAI_MODEL | OpenAI | OpenAI model name | gpt-4o-mini |
| OPENAI_BASE_URL | OpenAI | OpenAI base URL | https://api.openai.com/v1 |
| GROK_API_KEY | Grok | xAI API key | (required) |
| GROK_MODEL | Grok | Grok model name | grok-3-mini |
| GROK_BASE_URL | Grok | xAI API base URL | https://api.x.ai/v1 |
