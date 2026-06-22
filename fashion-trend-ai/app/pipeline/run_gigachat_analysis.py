from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from app.ai.fashion_context import build_fashion_context
from app.ai.gigachat_client import GigaChatClient
from app.ai.prompts import build_fashion_report_prompt

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def get_latest_run_dir() -> Path:
    runs_dir = PROJECT_ROOT / "data" / "processed" / "runs"
    run_dirs = [path for path in runs_dir.iterdir() if path.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in {runs_dir}")
    return sorted(run_dirs)[-1]

def load_fashion_results(run_dir: Path) -> list[dict]:
    path = run_dir / "fashion_attributes.json"
    if not path.exists():
        raise FileNotFoundError(f"FashionCLIP results file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", help="Run date folder, for example 2026-06-15")
    args = parser.parse_args()
    if args.run_date:
        run_dir = PROJECT_ROOT / "data" / "processed" / "runs" / args.run_date
    else:
        run_dir = get_latest_run_dir()
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")
    load_dotenv(PROJECT_ROOT / ".env")
    credentials = os.getenv("GIGACHAT_CREDENTIALS")
    if not credentials:
        raise ValueError("GIGACHAT_CREDENTIALS is not set in .env")
    results = load_fashion_results(run_dir)
    context = build_fashion_context(results)
    prompt = build_fashion_report_prompt(context)
    client = GigaChatClient(credentials=credentials)
    report = client.analyze(prompt)
    output_path = run_dir / "llm_report.md"
    with output_path.open("w", encoding="utf-8") as f:
        f.write(report)
    print(f"Saved GigaChat report: {output_path}")

if __name__ == "__main__":
    main()