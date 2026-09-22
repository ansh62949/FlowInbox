import asyncio
from app.llm.manager import LLMManager


async def main():
    print("=== Step 0 Smoke Check: Verifying Live Groq API Execution ===")
    manager = LLMManager()

    messages = [
        {"role": "user", "content": "Explain in one sentence what FlowInbox AI does."}
    ]

    result = await manager.generate(messages)
    print("\n--- Smoke Check Result ---")
    print(f"Provider: {result.get('provider')}")
    print(f"Model: {result.get('model')}")
    print(f"Response Snippet: {result.get('content')[:200]}")
    print("--------------------------\n")


if __name__ == "__main__":
    asyncio.run(main())
