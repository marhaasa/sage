"""Core tagging functionality for Sage."""

import asyncio
import re
from pathlib import Path
from typing import List, Optional, Tuple, Union
import aiofiles

from .utils import validate_tags, verify_content_unchanged


class AsyncMarkdownTagger:
    """Asynchronous markdown tagger using Claude Code CLI."""

    def __init__(self, max_concurrent: int = 5, timeout: int = 120):
        """Initialize the tagger.

        Args:
            max_concurrent: Maximum number of concurrent processing tasks
            timeout: Timeout in seconds for Claude API calls
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout

        self.claude_prompt = """Analyze this markdown document and suggest 2-5 relevant one word tags that describe the topic, technology, or type of content.

Requirements:
- Tags must be single words only (no spaces)
- Tags must be lowercase
- Tags should be relevant and descriptive
- Use the same language as the document content (if document is in Norwegian, use Norwegian tags; if in English, use English tags; etc.)
- Examples: 
  - English: python, debugging, react, tutorial, planning
  - Norwegian: programmering, feilsøking, veiledning, planlegging
  - German: programmierung, fehlersuche, anleitung, planung

Open the markdown file and at the end of the file add these tags. Each tag should be on a new line surrounded by [[]] like [[tag]]. Do not remove the existing [[claude]] tag if it exists."""

        self.allowed_tools = "Read,Edit"

    async def check_already_tagged(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Check if file already has tags (excluding [[claude]]).

        Returns:
            Tuple of (has_tags, list_of_non_claude_tags)
        """
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()

        # Find all tags
        tag_pattern = r"\[\[([^\]]+)\]\]"
        tags = re.findall(tag_pattern, content)

        # Filter out 'claude' tag
        non_claude_tags = [tag for tag in tags if tag != "claude"]

        return len(non_claude_tags) > 0, non_claude_tags

    async def process_file(
        self, file_path: Union[str, Path], force: bool = False, retry_count: int = 0
    ) -> Tuple[bool, Optional[str], List[str]]:
        """Process a single markdown file.

        Args:
            file_path: Path to the markdown file
            force: Force retagging even if already tagged
            retry_count: Current retry attempt

        Returns:
            Tuple of (success, error_message, tags_added)
        """
        file_path = Path(file_path)

        # Check if already tagged
        already_tagged, existing_tags = await self.check_already_tagged(file_path)
        if already_tagged and not force:
            return True, None, existing_tags

        try:
            # Store original content for verification
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                original_content = await f.read()

            # Run claude command asynchronously
            cmd = [
                "claude",
                "-p",
                self.claude_prompt,
                f"--allowedTools={self.allowed_tools}",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=original_content.encode()),
                timeout=self.timeout,
            )

            if process.returncode != 0:
                return False, f"Claude error: {stderr.decode()}", []

            # Read updated content and verify integrity
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                updated_content = await f.read()

            # Verify original content wasn't altered
            if not verify_content_unchanged(original_content, updated_content):
                # Restore original content
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(original_content)
                return False, "Content verification failed - restored original", []

            # Validate tags in the updated file
            valid_tags, invalid_tags = validate_tags(updated_content)

            if invalid_tags:
                # Clean up file by removing invalid tags
                await self._cleanup_invalid_tags(file_path, valid_tags)
                return True, f"Cleaned {len(invalid_tags)} invalid tags", valid_tags

            return True, None, valid_tags

        except asyncio.TimeoutError:
            if retry_count < 2:  # Retry up to 2 times
                await asyncio.sleep(2)  # Wait before retry
                return await self.process_file(file_path, force, retry_count + 1)
            else:
                return False, f"Timeout after {retry_count + 1} attempts", []
        except Exception as e:
            if retry_count < 1:  # Retry once for other errors
                await asyncio.sleep(1)
                return await self.process_file(file_path, force, retry_count + 1)
            else:
                return False, f"Error after retry: {e}", []

    async def _cleanup_invalid_tags(
        self, file_path: Path, valid_tags: List[str]
    ) -> None:
        """Remove invalid tags and keep only valid ones."""
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()

        # Remove all existing tags
        tag_pattern = r"\[\[([^\]]+)\]\]\s*\n?"
        content_no_tags = re.sub(tag_pattern, "", content).rstrip()

        # Add back only valid tags
        if valid_tags:
            tag_lines = [f"[[{tag}]]" for tag in valid_tags]
            content_with_valid_tags = content_no_tags + "\n\n" + "\n".join(tag_lines)
        else:
            content_with_valid_tags = content_no_tags

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content_with_valid_tags)

    async def process_files(
        self, file_paths: List[Union[str, Path]], force: bool = False
    ) -> Tuple[int, int, List[Tuple[Union[str, Path], str]]]:
        """Process multiple files concurrently.

        Args:
            file_paths: List of file paths to process
            force: Force retagging even if already tagged

        Returns:
            Tuple of (success_count, error_count, errors_list)
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(file_path):
            async with semaphore:
                return await self.process_file(file_path, force)

        file_paths = [Path(p) for p in file_paths]
        tasks = [process_with_semaphore(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = 0
        error_count = 0
        errors = []

        for file_path, result in zip(file_paths, results):
            if isinstance(result, Exception):
                error_count += 1
                errors.append((file_path, str(result)))
            elif isinstance(result, tuple) and len(result) == 3:
                success, error_msg, tags = result
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append((file_path, error_msg or "Unknown error"))
            else:
                error_count += 1
                errors.append((file_path, "Unexpected result format"))

        return success_count, error_count, errors

    async def process_directory(
        self, directory: Union[str, Path], force: bool = False, recursive: bool = False
    ) -> Tuple[int, int, List[Tuple[Union[str, Path], str]]]:
        """Process all markdown files in a directory.

        Args:
            directory: Directory path to process
            force: Force retagging even if already tagged
            recursive: Process subdirectories recursively

        Returns:
            Tuple of (success_count, error_count, errors_list)
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory}")

        if not directory.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory}")

        # Find all markdown files
        pattern = "**/*.md" if recursive else "*.md"
        markdown_files = list(directory.glob(pattern))

        if not markdown_files:
            return 0, 0, []

        # Convert Path objects to Union[str, Path] for type compatibility
        file_paths: List[Union[str, Path]] = list(markdown_files)
        return await self.process_files(file_paths, force)
