"""Command-line interface for Sage."""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List

import click

from . import __version__
from .tagger import AsyncMarkdownTagger
from .utils import truncate_text


def print_success(message: str) -> None:
    """Print success message in green."""
    click.echo(click.style(f"✓ {message}", fg="green"))


def print_error(message: str) -> None:
    """Print error message in red."""
    click.echo(click.style(f"✗ {message}", fg="red"))


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    click.echo(click.style(f"⚠ {message}", fg="yellow"))


def print_info(message: str) -> None:
    """Print info message in blue."""
    click.echo(click.style(f"ℹ {message}", fg="blue"))


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """Sage - Intelligent semantic tagging for markdown files.

    Analyze your markdown content and automatically add relevant semantic tags.
    """
    if version:
        click.echo(f"sage {__version__}")
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--force", is_flag=True, help="Force retag even if already tagged")
@click.option("--quiet", is_flag=True, help="Minimal output")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
@click.option("--timeout", default=120, help="Timeout in seconds for Claude API calls")
def file(
    file_path: Path, force: bool, quiet: bool, json_output: bool, timeout: int
) -> None:
    """Tag a single markdown file."""
    if not file_path.suffix.lower() == ".md":
        print_error(f"File must be a markdown file (.md): {file_path}")
        sys.exit(1)

    async def process():
        tagger = AsyncMarkdownTagger(timeout=timeout)
        success, error_msg, tags = await tagger.process_file(file_path, force)

        if json_output:
            result = {
                "file": str(file_path),
                "success": success,
                "error": error_msg,
                "tags": tags,
            }
            click.echo(json.dumps(result, indent=2))
        elif quiet:
            if not success:
                sys.exit(1)
        else:
            if success:
                if tags:
                    print_success(f"Tagged {file_path.name} with: {', '.join(tags)}")
                else:
                    print_info(f"No new tags added to {file_path.name}")
            else:
                print_error(f"Failed to tag {file_path.name}: {error_msg}")
                sys.exit(1)

    asyncio.run(process())


@main.command()
@click.argument(
    "file_paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path)
)
@click.option("--force", is_flag=True, help="Force retag even if already tagged")
@click.option(
    "--concurrent/--sequential",
    default=True,
    help="Enable/disable concurrent processing",
)
@click.option("--workers", default=5, help="Number of concurrent workers")
@click.option("--quiet", is_flag=True, help="Minimal output")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
@click.option("--timeout", default=120, help="Timeout in seconds for Claude API calls")
def files(
    file_paths: List[Path],
    force: bool,
    concurrent: bool,
    workers: int,
    quiet: bool,
    json_output: bool,
    timeout: int,
) -> None:
    """Tag multiple markdown files."""
    # Filter to only markdown files
    markdown_files = [f for f in file_paths if f.suffix.lower() == ".md"]

    if not markdown_files:
        print_error("No markdown files found in the provided paths")
        sys.exit(1)

    if len(markdown_files) != len(file_paths):
        skipped = len(file_paths) - len(markdown_files)
        if not quiet:
            print_warning(f"Skipped {skipped} non-markdown files")

    async def process():
        max_concurrent = 1 if not concurrent else workers
        tagger = AsyncMarkdownTagger(max_concurrent=max_concurrent, timeout=timeout)

        start_time = time.time()
        success_count, error_count, errors = await tagger.process_files(
            markdown_files, force
        )
        elapsed_time = time.time() - start_time

        if json_output:
            result = {
                "total_files": len(markdown_files),
                "success_count": success_count,
                "error_count": error_count,
                "elapsed_time": elapsed_time,
                "errors": [
                    {"file": str(path), "error": error} for path, error in errors
                ],
            }
            click.echo(json.dumps(result, indent=2))
        elif quiet:
            if error_count > 0:
                sys.exit(1)
        else:
            print_info(f"Processed {len(markdown_files)} files in {elapsed_time:.2f}s")
            print_success(f"Successfully tagged: {success_count}")

            if error_count > 0:
                print_error(f"Errors: {error_count}")
                for file_path, error in errors:
                    print_error(f"  {file_path.name}: {error}")
                sys.exit(1)

    asyncio.run(process())


@main.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option("--force", is_flag=True, help="Force retag even if already tagged")
@click.option(
    "--recursive", "-r", is_flag=True, help="Process subdirectories recursively"
)
@click.option(
    "--concurrent/--sequential",
    default=True,
    help="Enable/disable concurrent processing",
)
@click.option("--workers", default=5, help="Number of concurrent workers")
@click.option("--quiet", is_flag=True, help="Minimal output")
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
@click.option("--timeout", default=120, help="Timeout in seconds for Claude API calls")
def dir(
    directory: Path,
    force: bool,
    recursive: bool,
    concurrent: bool,
    workers: int,
    quiet: bool,
    json_output: bool,
    timeout: int,
) -> None:
    """Tag all markdown files in a directory."""

    async def process():
        max_concurrent = 1 if not concurrent else workers
        tagger = AsyncMarkdownTagger(max_concurrent=max_concurrent, timeout=timeout)

        try:
            start_time = time.time()
            success_count, error_count, errors = await tagger.process_directory(
                directory, force, recursive
            )
            elapsed_time = time.time() - start_time

            total_files = success_count + error_count

            if json_output:
                result = {
                    "directory": str(directory),
                    "recursive": recursive,
                    "total_files": total_files,
                    "success_count": success_count,
                    "error_count": error_count,
                    "elapsed_time": elapsed_time,
                    "errors": [
                        {"file": str(path), "error": error} for path, error in errors
                    ],
                }
                click.echo(json.dumps(result, indent=2))
            elif quiet:
                if error_count > 0:
                    sys.exit(1)
            else:
                if total_files == 0:
                    print_info(f"No markdown files found in {directory}")
                else:
                    mode = "recursively" if recursive else "directly"
                    print_info(
                        f"Processed {total_files} files {mode} in {directory} ({elapsed_time:.2f}s)"
                    )
                    print_success(f"Successfully tagged: {success_count}")

                    if error_count > 0:
                        print_error(f"Errors: {error_count}")
                        for file_path, error in errors[:5]:  # Show first 5 errors
                            print_error(
                                f"  {file_path.name}: {truncate_text(error, 60)}"
                            )
                        if len(errors) > 5:
                            print_error(f"  ... and {len(errors) - 5} more errors")
                        sys.exit(1)

        except (FileNotFoundError, NotADirectoryError) as e:
            print_error(str(e))
            sys.exit(1)

    asyncio.run(process())


if __name__ == "__main__":
    main()
