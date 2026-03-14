"""Format and output results to JSON and Markdown."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def write_results(
    results: list[Any],
    output_folder: str | Path,
    jd_file_name: str,
    model: str,
    provider: str,
    top_n: int | None = None
) -> tuple[Path, Path]:
    """Write results to JSON and Markdown files.

    Args:
        results: List of CandidateResult objects, sorted by total_score descending
        output_folder: Output directory path
        jd_file_name: Original JD filename for reference
        model: Model name used
        provider: Provider name used
        top_n: If set, only include top N candidates in output

    Returns:
        Tuple of (json_path, md_path) - paths to created files
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Apply top_n limit
    output_results = results[:top_n] if top_n else results
    total_evaluated = len(results)

    # Write JSON
    json_path = output_folder / f"results_{timestamp}.json"
    _write_json(json_path, output_results, jd_file_name, model, provider, total_evaluated)

    # Write Markdown
    md_path = output_folder / f"results_{timestamp}.md"
    _write_markdown(md_path, output_results, jd_file_name, model, provider, total_evaluated)

    logger.info(f"Results written to {json_path} and {md_path}")
    return json_path, md_path


def _write_json(
    path: Path,
    results: list[Any],
    jd_file_name: str,
    model: str,
    provider: str,
    total_evaluated: int
) -> None:
    """Write JSON output file."""
    output = {
        "job_description_file": jd_file_name,
        "run_timestamp": datetime.now().isoformat(),
        "model": model,
        "provider": provider,
        "total_candidates_evaluated": total_evaluated,
        "candidates": []
    }

    for rank, result in enumerate(results, 1):
        candidate = {
            "rank": rank,
            "candidate_name": result.candidate_name,
            "file_name": result.file_name,
            "total_score": result.total_score,
            "recommendation": result.recommendation,
            "summary": result.summary,
            "dimensions": result.dimensions,
            "parse_error": result.parse_error
        }
        output["candidates"].append(candidate)

    with open(path, "w") as f:
        json.dump(output, f, indent=2)


def _write_markdown(
    path: Path,
    results: list[Any],
    jd_file_name: str,
    model: str,
    provider: str,
    total_evaluated: int
) -> None:
    """Write Markdown output file."""
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        "# StackRank Results",
        f"**Role:** {jd_file_name}",
        f"**Date:** {date_str}",
        f"**Candidates Evaluated:** {total_evaluated}",
        f"**Model:** {model} ({provider})",
        "",
        "---",
        "",
        "## Shortlist",
        "",
        "| Rank | Candidate | Score | Recommendation |",
        "|------|-----------|-------|----------------|"
    ]

    emoji_map = {
        "STRONG_YES": "✅ STRONG_YES",
        "YES": "✅ YES",
        "MAYBE": "⚠️ MAYBE",
        "NO": "❌ NO"
    }

    for rank, result in enumerate(results, 1):
        rec = emoji_map.get(result.recommendation, result.recommendation)
        lines.append(f"| {rank} | {result.candidate_name} | {result.total_score} | {rec} |")

    lines.extend(["", "---", "", "## Detailed Assessments", ""])

    for rank, result in enumerate(results, 1):
        lines.append(f"### {rank}. {result.candidate_name} — {result.total_score}/100 {rec}")
        lines.append(f">{result.summary}")
        lines.append("")
        lines.append("| Dimension | Score | Notes |")
        lines.append("|-----------|-------|-------|")

        for dim_name, dim_data in result.dimensions.items():
            score = dim_data.get("score", "N/A")
            rationale = dim_data.get("rationale", "")
            display_name = dim_name.replace("_", " ").title()
            lines.append(f"| {display_name} | {score}/25 | {rationale} |")

        lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))