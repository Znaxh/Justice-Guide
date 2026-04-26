"""
Corpus ingestion utility for JusticeGuide.

Usage examples:
  uv run python -m src.ingest --from-dir ./my_legal_docs
  uv run python -m src.ingest ./note1.md ./section302.pdf --rebuild-index
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS_DIR = PROJECT_ROOT / "dataset" / "corpus"


@dataclass
class PlannedCopy:
    source: Path
    target: Path


def _is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def _iter_supported_files(directory: Path) -> list[Path]:
    return sorted([p for p in directory.rglob("*") if p.is_file() and _is_supported(p)])


def _safe_target(base_dir: Path, rel_path: Path) -> Path:
    """
    Generate a deterministic target path and avoid collisions by suffixing with hash.
    """
    candidate = base_dir / rel_path
    if not candidate.exists():
        return candidate
    digest = hashlib.sha1(str(rel_path).encode("utf-8")).hexdigest()[:8]
    return candidate.with_name(f"{candidate.stem}_{digest}{candidate.suffix}")


def _plan_import(files: list[Path], from_dirs: list[Path], destination: Path) -> list[PlannedCopy]:
    plans: list[PlannedCopy] = []

    for file_path in files:
        rel = Path("manual") / file_path.name
        target = _safe_target(destination, rel)
        plans.append(PlannedCopy(source=file_path, target=target))

    for source_dir in from_dirs:
        for file_path in _iter_supported_files(source_dir):
            rel = Path(source_dir.name) / file_path.relative_to(source_dir)
            target = _safe_target(destination, rel)
            plans.append(PlannedCopy(source=file_path, target=target))

    return plans


def _copy_plans(plans: list[PlannedCopy], dry_run: bool) -> None:
    for plan in plans:
        if dry_run:
            print(f"[dry-run] {plan.source} -> {plan.target}")
            continue
        plan.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan.source, plan.target)
        print(f"imported: {plan.source} -> {plan.target}")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest IPC corpus files into dataset/corpus.")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Individual files to import (.pdf/.md/.txt).",
    )
    parser.add_argument(
        "--from-dir",
        dest="from_dirs",
        action="append",
        type=Path,
        default=[],
        help="Directory to recursively import supported files from. Can be passed multiple times.",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_CORPUS_DIR,
        help="Destination corpus directory (default: dataset/corpus).",
    )
    parser.add_argument(
        "--clear-destination",
        action="store_true",
        help="Delete destination directory before import (use with caution).",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rebuild FAISS index after import.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned operations without writing files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])

    destination = args.dest.resolve()
    file_inputs = [p.resolve() for p in args.files]
    dir_inputs = [p.resolve() for p in args.from_dirs]

    for file_path in file_inputs:
        if not file_path.exists() or not file_path.is_file():
            print(f"invalid file input: {file_path}")
            return 1
        if not _is_supported(file_path):
            print(f"unsupported extension (allowed: .pdf/.md/.txt): {file_path}")
            return 1

    for directory in dir_inputs:
        if not directory.exists() or not directory.is_dir():
            print(f"invalid directory input: {directory}")
            return 1

    if not file_inputs and not dir_inputs:
        print("no inputs provided. pass files and/or --from-dir.")
        return 1

    if args.clear_destination and destination.exists():
        if args.dry_run:
            print(f"[dry-run] would delete: {destination}")
        else:
            shutil.rmtree(destination)
            print(f"deleted destination: {destination}")

    plans = _plan_import(file_inputs, dir_inputs, destination)
    if not plans:
        print("no supported files found to import.")
        return 1

    print(f"planned imports: {len(plans)}")
    _copy_plans(plans, dry_run=args.dry_run)

    if args.rebuild_index:
        if args.dry_run:
            print("[dry-run] would rebuild index.")
        else:
            from src.retrieval import rebuild_index

            print("rebuilding retrieval index...")
            rebuild_index()
            print("index rebuild completed.")

    print("ingestion completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
