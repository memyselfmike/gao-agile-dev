"""
Basic usage example for AIAnalysisService.

This example demonstrates:
- Creating an AIAnalysisService instance
- Making a simple analysis request
- Accessing response and metadata

Epic: 21 - AI Analysis Service & Brian Provider Abstraction
"""
import asyncio
import os
from gao_dev.core.services import AIAnalysisService


async def main():
    """Basic AIAnalysisService usage example."""

    # Ensure API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='sk-ant-...'")
        return

    print("=" * 60)
    print("AIAnalysisService - Basic Usage Example")
    print("=" * 60)

    # Create service (uses ANTHROPIC_API_KEY from environment)
    print("\n1. Creating AIAnalysisService...")
    service = AIAnalysisService(
        default_model="claude-sonnet-4-5-20250929"
    )
    print(f"   Service created: {service}")

    # Analyze a simple prompt
    print("\n2. Analyzing project complexity...")
    result = await service.analyze(
        prompt="""
        Analyze the complexity of building a todo application with:
        - User authentication
        - CRUD operations for tasks
        - Task filtering and search

        Return JSON with:
        {
            "complexity_score": 1-10,
            "estimated_hours": number,
            "key_challenges": ["challenge1", "challenge2"]
        }
        """,
        response_format="json",
        max_tokens=1024,
        temperature=0.7
    )

    # Display results
    print("\n3. Results:")
    print(f"   Response: {result.response}")
    print(f"   Model used: {result.model_used}")
    print(f"   Tokens used: {result.tokens_used}")
    print(f"   Duration: {result.duration_ms}ms")

    # Parse JSON response
    print("\n4. Parsed JSON:")
    import json
    try:
        data = json.loads(result.response)
        print(f"   Complexity Score: {data.get('complexity_score', 'N/A')}")
        print(f"   Estimated Hours: {data.get('estimated_hours', 'N/A')}")
        print(f"   Key Challenges: {', '.join(data.get('key_challenges', []))}")
    except json.JSONDecodeError as e:
        print(f"   Warning: Could not parse JSON: {e}")
        print(f"   Raw response: {result.response}")

    # Estimate cost
    print("\n5. Cost Estimate:")
    # Rough estimate: $3 per million tokens for Sonnet 4.5
    cost = result.tokens_used * 0.000003
    print(f"   Estimated cost: ${cost:.6f}")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
