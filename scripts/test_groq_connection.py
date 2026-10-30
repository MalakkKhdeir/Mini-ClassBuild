import sys

from classbuild.llm import GroqClient, GroqClientError

def main():
    try:
        print("Testing connection to Groq...")
        client = GroqClient()
        response = client.generate(
            "Explain a Python variable to a beginner in 3 bullet points."
        )
        print(response)
        print("[OK] Connection test succeeded.")

    except GroqClientError as exc:
        print(f"[FAILED] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()




