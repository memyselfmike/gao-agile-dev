"""
Custom model usage example for AIAnalysisService.

This example demonstrates:
- Using different models for different tasks
- Comparing model performance
- Choosing right model for the job

Epic: 21 - AI Analysis Service & Brian Provider Abstraction
"""
import asyncio
import os
import time
from gao_dev.core.services import AIAnalysisService


async def analyze_with_model(service: AIAnalysisService, prompt: str, model: str):
    """Analyze prompt with specific model and return metrics."""
    start_time = time.time()

    result = await service.analyze(
        prompt=prompt,
        model=model,
        response_format="json",
        max_tokens=512
    )

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "model": result.model_used,
        "response": result.response,
        "tokens": result.tokens_used,
        "duration_ms": result.duration_ms,
        "total_elapsed_ms": elapsed_ms,
        "cost_estimate": result.tokens_used * 0.000003  # $3 per million tokens
    }


async def main():
    """Compare different models for same task."""

    # Ensure API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='sk-ant-...'")
        return

    print("=" * 80)
    print("AIAnalysisService - Custom Model Selection Example")
    print("=" * 80)

    # Create service
    service = AIAnalysisService()

    # Define test prompt
    prompt = """
    Rate the code complexity from 1-10:

    def calculate_fibonacci(n):
        if n <= 1:
            return n
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

    Return JSON: {"complexity": 1-10, "rationale": "brief explanation"}
    """

    # Models to test
    models = [
        ("claude-3-haiku-20240307", "Fast & Cheap"),
        ("claude-3-sonnet-20240229", "Balanced"),
        ("claude-sonnet-4-5-20250929", "Latest & Best"),
    ]

    print("\nComparing models for same analysis task:")
    print("-" * 80)

    results = []
    for model_id, description in models:
        print(f"\nTesting: {description} ({model_id})")
        print("  Analyzing...")

        try:
            result = await analyze_with_model(service, prompt, model_id)
            results.append(result)

            print(f"  Response: {result['response'][:60]}...")
            print(f"  Tokens: {result['tokens']}")
            print(f"  Duration: {result['duration_ms']:.0f}ms")
            print(f"  Cost: ${result['cost_estimate']:.6f}")

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    # Summary comparison
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    if results:
        print(f"\n{'Model':<45} {'Tokens':<10} {'Duration (ms)':<15} {'Cost':<12}")
        print("-" * 80)

        for result in results:
            model_name = result['model'][:44]
            tokens = result['tokens']
            duration = result['duration_ms']
            cost = result['cost_estimate']

            print(f"{model_name:<45} {tokens:<10} {duration:<15.0f} ${cost:<11.6f}")

        # Find fastest and cheapest
        fastest = min(results, key=lambda r: r['duration_ms'])
        cheapest = min(results, key=lambda r: r['cost_estimate'])

        print("\nRecommendations:")
        print(f"  Fastest: {fastest['model']} ({fastest['duration_ms']:.0f}ms)")
        print(f"  Cheapest: {cheapest['model']} (${cheapest['cost_estimate']:.6f})")

    # Model selection strategy
    print("\n" + "=" * 80)
    print("MODEL SELECTION STRATEGY")
    print("=" * 80)

    strategies = [
        ("Simple tasks (yes/no, basic classification)", "claude-3-haiku-20240307"),
        ("General analysis (complexity, code review)", "claude-3-sonnet-20240229"),
        ("Complex reasoning (architecture, design)", "claude-sonnet-4-5-20250929"),
        ("Production critical decisions", "claude-sonnet-4-5-20250929"),
        ("Development/testing (use local models)", "deepseek-r1:8b via Ollama"),
    ]

    print("\nTask Type → Recommended Model:")
    for task, model in strategies:
        print(f"  {task:<50} → {model}")

    print("\n" + "=" * 80)
    print("Example complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
