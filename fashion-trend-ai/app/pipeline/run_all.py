from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STEPS = ["apify", "detection", "segmentation", "gemini"]

STEP_MODULES = {
    "apify": "app.pipeline.run_apify",
    "detection": "app.pipeline.run_detection",
    "segmentation": "app.pipeline.run_segmentation",
    "gemini": "app.pipeline.run_gemini",
    "gigachat": "app.pipeline.run_gigachat_analysis",
}


def parse_steps(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_STEPS

    steps = [item.strip().lower() for item in value.split(",") if item.strip()]
    unknown = [step for step in steps if step not in STEP_MODULES]

    if unknown:
        raise ValueError(f"Unknown pipeline steps: {unknown}. Available: {list(STEP_MODULES)}")

    return steps


def build_command(step: str, args: argparse.Namespace, run_date: str) -> list[str]:
    command = [sys.executable, "-m", STEP_MODULES[step]]

    if step == "apify":
        if args.apify_limit is not None:
            command.extend(["--limit", str(args.apify_limit)])
        return command

    command.extend(["--run-date", run_date])

    if step == "detection":
        if args.detection_limit is not None:
            command.extend(["--limit", str(args.detection_limit)])
        command.extend(["--box-threshold", str(args.box_threshold)])
        command.extend(["--text-threshold", str(args.text_threshold)])
        command.extend(["--nms-iou-threshold", str(args.nms_iou_threshold)])

    if step == "segmentation" and args.segmentation_limit is not None:
        command.extend(["--limit", str(args.segmentation_limit)])

    if step == "gemini":
        if args.gemini_limit is not None:
            command.extend(["--limit", str(args.gemini_limit)])
        if args.force_gemini:
            command.append("--force")

    return command


def run_command(command: list[str], dry_run: bool) -> None:
    print()
    print(" ".join(command))

    if dry_run:
        return

    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", help="Comma-separated steps: apify,detection,segmentation,gemini,gigachat")
    parser.add_argument("--run-date", help="Run date folder, for example 2026-06-19")
    parser.add_argument("--apify-limit", type=int, default=5)
    parser.add_argument("--detection-limit", type=int, default=None)
    parser.add_argument("--segmentation-limit", type=int, default=None)
    parser.add_argument("--gemini-limit", type=int, default=None)
    parser.add_argument("--box-threshold", type=float, default=0.35)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--nms-iou-threshold", type=float, default=0.5)
    parser.add_argument("--force-gemini", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--frame-every-seconds", type=int, default=5)
    parser.add_argument("--max-frames-per-video", type=int, default=1)
    args = parser.parse_args()

    steps = parse_steps(args.steps)
    run_date = args.run_date or date.today().isoformat()

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Run date: {run_date}")
    print(f"Steps: {', '.join(steps)}")

    for step in steps:
        command = build_command(step=step, args=args, run_date=run_date)
        command.extend(["--frame-every-seconds", str(args.frame_every_seconds)])
        command.extend(["--max-frames-per-video", str(args.max_frames_per_video)])
        run_command(command=command, dry_run=args.dry_run)

    print()
    print("Pipeline finished.")


if __name__ == "__main__":
    main()