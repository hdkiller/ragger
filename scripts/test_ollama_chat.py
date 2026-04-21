import argparse
import os

from langchain_ollama import ChatOllama


DEFAULT_MODEL = "gemma4:26b"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Minimal ChatOllama smoke test for a local Ollama model."
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL),
        help="Ollama model tag to use. Defaults to gemma4:26b.",
    )
    parser.add_argument(
        "--prompt",
        default="Say hello in one short sentence.",
        help="Prompt to send to the local model.",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama server base URL.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for the smoke test.",
    )
    args = parser.parse_args()

    llm = ChatOllama(
        model=args.model,
        base_url=args.base_url,
        temperature=args.temperature,
    )
    response = llm.invoke(args.prompt)
    print(response.content)


if __name__ == "__main__":
    main()
