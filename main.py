"""StackRank CLI - Rank resumes against job descriptions using AI."""

import logging
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from stackrank import config_loader
from stackrank.jd_parser import parse_jd
from stackrank.model_client import ModelClient
from stackrank.output_formatter import write_results
from stackrank.resume_parser import parse_resume
from stackrank.scorer import Scorer

# Load .env file if present
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--jd",
    required=True,
    type=click.Path(exists=True),
    help="Path to the .docx Job Description file"
)
@click.option(
    "--resumes",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path to folder containing resume files (.pdf and/or .docx)"
)
@click.option(
    "--config",
    default="./config.yaml",
    type=click.Path(),
    help="Path to config file (default: ./config.yaml)"
)
@click.option(
    "--output",
    default=None,
    type=click.Path(),
    help="Override output folder"
)
@click.option(
    "--top",
    default=None,
    type=int,
    help="Only include top N candidates in output"
)
def main(jd: str, resumes: str, config: str, output: str | None, top: int | None):
    """Rank resumes against a job description using AI.

    Reads job description from JD file, scores all resumes in the resumes folder,
    and outputs ranked results in JSON and Markdown formats.
    """
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config_data = config_loader.load_config(config, output)
        api_key = config_loader.get_api_key(config_data)

        # Parse job description
        logger.info(f"Parsing job description: {jd}")
        jd_text = parse_jd(jd)
        jd_file_name = Path(jd).name
        logger.info(f"Job description loaded ({len(jd_text)} characters)")

        # Initialize model client
        model_config = config_data["model"]
        client = ModelClient(
            provider=model_config["provider"],
            model_name=model_config["model_name"],
            api_key=api_key,
            endpoint=model_config.get("endpoint")
        )

        # Initialize scorer
        scorer = Scorer(client)

        # Get all resume files
        resume_folder = Path(resumes)
        resume_files = []
        for suffix in [".pdf", ".docx"]:
            resume_files.extend(resume_folder.glob(f"*{suffix}"))

        if not resume_files:
            click.echo(f"No resume files (.pdf or .docx) found in {resumes}", err=True)
            sys.exit(1)

        logger.info(f"Found {len(resume_files)} resume(s) to process")

        # Process each resume
        results = []
        for resume_file in resume_files:
            click.echo(f"Processing: {resume_file.name}")
            resume_data = parse_resume(resume_file)

            if resume_data is None:
                click.echo(f"  ⚠️  Failed to parse, skipping")
                continue

            result = scorer.score(jd_text, resume_data, resume_file.name)
            results.append(result)

            status = "❌ parse error" if result.parse_error else f"{result.total_score}/100 {result.recommendation}"
            click.echo(f"  → {status}")

        # Sort by score descending
        results.sort(key=lambda r: r.total_score, reverse=True)

        # Write output files
        output_folder = config_data["output"]["folder"]
        logger.info(f"Writing results to {output_folder}")

        json_path, md_path = write_results(
            results=results,
            output_folder=output_folder,
            jd_file_name=jd_file_name,
            model=model_config["model_name"],
            provider=model_config["provider"],
            top_n=top
        )

        click.echo(f"\n✅ Complete! Processed {len(results)} candidates")
        click.echo(f"   JSON: {json_path}")
        click.echo(f"   Markdown: {md_path}")

    except config_loader.ConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()