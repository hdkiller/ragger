import argparse
import os

from huggingface_hub import hf_hub_download
from langchain_community.llms import LlamaCpp

DEFAULT_REPO = "ggml-org/gemma-4-26B-A4B-it-GGUF"
DEFAULT_FILE = "gemma-4-26B-A4B-it-Q4_K_M.gguf"


def resolve_model_path(repo_id: str, filename: str, local_only: bool) -> str:
    if os.path.isdir(repo_id):
        return os.path.join(repo_id, filename)

    return hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_files_only=local_only,
    )


def build_llm(
    model_path: str,
    n_ctx: int,
    n_gpu_layers: int,
    temperature: float,
) -> LlamaCpp:
    return LlamaCpp(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        temperature=temperature,
        max_tokens=128,
        verbose=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Minimal LangChain smoke test for Gemma 4 GGUF via llama.cpp."
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GEMMA_GGUF_REPO", DEFAULT_REPO),
        help=(
            "Hugging Face GGUF repo id or local directory. "
            "Defaults to ggml-org/gemma-4-26B-A4B-it-GGUF."
        ),
    )
    parser.add_argument(
        "--file",
        default=os.environ.get("GEMMA_GGUF_FILE", DEFAULT_FILE),
        help="GGUF filename to load from the repo or local directory.",
    )
    parser.add_argument(
        "--prompt",
        default="Say hello in one short sentence.",
        help="Prompt to send to the model.",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only use locally cached Hugging Face files and never hit the network.",
    )
    parser.add_argument(
        "--n-ctx",
        type=int,
        default=4096,
        help="Context window to allocate in llama.cpp.",
    )
    parser.add_argument(
        "--n-gpu-layers",
        type=int,
        default=-1,
        help="How many layers to place on GPU. Use 0 for CPU only, -1 for all.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for the smoke test.",
    )
    args = parser.parse_args()

    model_path = resolve_model_path(args.repo, args.file, args.local_only)
    print(f"Loading GGUF from: {model_path}")
    llm = build_llm(
        model_path=model_path,
        n_ctx=args.n_ctx,
        n_gpu_layers=args.n_gpu_layers,
        temperature=args.temperature,
    )
    response = llm.invoke(args.prompt)
    print(response)


if __name__ == "__main__":
    main()
