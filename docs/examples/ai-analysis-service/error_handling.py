"""
Error handling example for AIAnalysisService.

This example demonstrates:
- Handling different error types
- Implementing retry logic
- Graceful error recovery
- Fallback strategies

Epic: 21 - AI Analysis Service & Brian Provider Abstraction
"""
import asyncio
import os
from gao_dev.core.services import AIAnalysisService
from gao_dev.core.providers.exceptions import (
    AnalysisError,
    AnalysisTimeoutError,
    InvalidModelError
)


async def basic_error_handling():
    """Basic error handling example."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Error Handling")
    print("=" * 60)

    service = AIAnalysisService()

    try:
        # This will work if API key is set
        result = await service.analyze(
            prompt="Analyze: def add(a, b): return a + b",
            response_format="json"
        )
        print(f"Success: {result.response[:50]}...")

    except AnalysisTimeoutError as e:
        print(f"ERROR: Analysis timed out: {e}")

    except InvalidModelError as e:
        print(f"ERROR: Invalid model: {e}")

    except AnalysisError as e:
        print(f"ERROR: Analysis failed: {e}")

    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")


async def retry_with_smaller_tokens():
    """Retry on timeout with smaller max_tokens."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Retry on Timeout with Smaller max_tokens")
    print("=" * 60)

    service = AIAnalysisService()
    prompt = "Analyze this complex system architecture..."

    max_tokens_attempts = [4096, 2048, 1024, 512]

    for max_tokens in max_tokens_attempts:
        print(f"\nAttempting with max_tokens={max_tokens}...")
        try:
            result = await service.analyze(
                prompt=prompt,
                max_tokens=max_tokens
            )
            print(f"Success! Response length: {len(result.response)}")
            print(f"Tokens used: {result.tokens_used}")
            break

        except AnalysisTimeoutError:
            print(f"Timed out with max_tokens={max_tokens}")
            if max_tokens == max_tokens_attempts[-1]:
                print("All retry attempts exhausted")
                raise

        except AnalysisError as e:
            print(f"Failed: {e}")
            raise


async def fallback_to_different_model():
    """Fallback to cheaper model on error."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Fallback to Different Model")
    print("=" * 60)

    service = AIAnalysisService()
    prompt = "Rate complexity 1-10: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"

    # Try expensive model first, fallback to cheaper
    models = [
        "claude-sonnet-4-5-20250929",  # Best quality
        "claude-3-sonnet-20240229",     # Good quality
        "claude-3-haiku-20240307"       # Fast & cheap
    ]

    for model in models:
        print(f"\nTrying model: {model}...")
        try:
            result = await service.analyze(
                prompt=prompt,
                model=model,
                response_format="json"
            )
            print(f"Success with {model}!")
            print(f"Response: {result.response[:50]}...")
            break

        except InvalidModelError:
            print(f"Model {model} not available, trying next...")
            if model == models[-1]:
                print("All models exhausted")
                raise

        except AnalysisError as e:
            print(f"Error with {model}: {e}")
            if model == models[-1]:
                raise


async def json_validation_fallback():
    """Handle invalid JSON responses with fallback."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: JSON Validation with Fallback")
    print("=" * 60)

    service = AIAnalysisService()

    prompt_attempts = [
        # Attempt 1: Regular request
        "Analyze complexity and return JSON",

        # Attempt 2: Stronger instructions
        """
        Analyze complexity and return ONLY valid JSON.
        Format: {"complexity": 1-10}
        NO markdown, NO explanations outside JSON.
        """,

        # Attempt 3: Explicit format
        """
        Return exactly this format:
        {"complexity": 5}
        Replace 5 with your analysis. ONLY JSON, nothing else.
        """
    ]

    import json

    for i, prompt in enumerate(prompt_attempts, 1):
        print(f"\nAttempt {i}...")
        try:
            result = await service.analyze(
                prompt=prompt,
                response_format="json",
                max_tokens=100
            )

            # Try to parse JSON
            data = json.loads(result.response)
            print(f"Success! Valid JSON: {data}")
            break

        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            print(f"Response was: {result.response}")

            if i == len(prompt_attempts):
                print("All attempts to get valid JSON failed")
                # Last resort: use text response
                result = await service.analyze(
                    prompt="Analyze complexity in plain text",
                    response_format="text"
                )
                print(f"Fallback to text: {result.response}")
                break


async def comprehensive_error_recovery():
    """Comprehensive error handling with all strategies."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Comprehensive Error Recovery")
    print("=" * 60)

    service = AIAnalysisService()
    prompt = "Analyze project complexity"

    # Configuration
    max_retries = 3
    fallback_models = ["claude-sonnet-4-5-20250929", "claude-3-haiku-20240307"]
    max_tokens_options = [2048, 1024, 512]

    for retry in range(max_retries):
        print(f"\n--- Retry {retry + 1}/{max_retries} ---")

        for model in fallback_models:
            for max_tokens in max_tokens_options:
                print(f"Trying: model={model}, max_tokens={max_tokens}")

                try:
                    result = await service.analyze(
                        prompt=prompt,
                        model=model,
                        max_tokens=max_tokens,
                        response_format="json"
                    )

                    print("SUCCESS!")
                    print(f"  Model: {result.model_used}")
                    print(f"  Tokens: {result.tokens_used}")
                    print(f"  Duration: {result.duration_ms}ms")
                    return result

                except AnalysisTimeoutError:
                    print(f"  Timeout - trying smaller max_tokens")
                    continue

                except InvalidModelError:
                    print(f"  Model invalid - trying different model")
                    break  # Try next model

                except AnalysisError as e:
                    print(f"  Error: {e}")
                    continue

        # Wait before retry
        if retry < max_retries - 1:
            print("Waiting before retry...")
            await asyncio.sleep(2)

    print("\nAll retry attempts exhausted - analysis failed")


async def main():
    """Run all error handling examples."""

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("=" * 60)
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("=" * 60)
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'")
        print("\nNote: Some examples may fail without valid API key")
        print("=" * 60)
        return

    print("=" * 60)
    print("AIAnalysisService - Error Handling Examples")
    print("=" * 60)

    try:
        # Run examples
        await basic_error_handling()
        await retry_with_smaller_tokens()
        await fallback_to_different_model()
        await json_validation_fallback()
        await comprehensive_error_recovery()

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")

    except Exception as e:
        print(f"\n\nUnexpected error in examples: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Error handling examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
