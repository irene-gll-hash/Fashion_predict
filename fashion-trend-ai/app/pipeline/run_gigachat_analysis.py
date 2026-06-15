from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from app.ai.gigachat_client import GigaChatClient
from app.ai.prompts import build_gigachat_vision_prompt
from app.ai.vision_context import build_vision_context
from app.config import settings

def load_json(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> None:
    if not settings.gigachat_credentials:
        raise RuntimeError("GIGACHAT_CREDENTIALS is not set")
    run_date = date.today().isoformat()
    run_dir = Path(f"data/processed/runs/{run_date}")
    vision_results = load_json(run_dir / "vision_results.json")
    context = build_vision_context(vision_results)
    prompt = build_gigachat_vision_prompt(context)
    client = GigaChatClient(credentials=settings.gigachat_credentials, scope=settings.gigachat_scope, verify_ssl_certs=settings.gigachat_verify_ssl)
    report_text = client.analyze(prompt)
    report_path = run_dir / "llm_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    print(f"Saved report to: {report_path}")

if __name__ == "__main__":
    main()