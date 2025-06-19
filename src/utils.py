"""Utility functions for Sage."""

import re
from typing import List, Tuple


def validate_tags(text: str) -> Tuple[List[str], List[str]]:
    """Validate that tags follow the required format and extract them.
    Only looks for tags at the end of the file, not within code blocks.

    Args:
        text: The markdown content to validate tags in

    Returns:
        Tuple of (valid_tags, invalid_tags)
    """
    # Only look for tags in the last 20 lines to avoid code blocks
    lines = text.split("\n")
    last_lines = lines[-20:] if len(lines) > 20 else lines

    # Remove code blocks from the search area
    filtered_lines = []
    in_code_block = False

    for line in last_lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            filtered_lines.append(line)

    search_text = "\n".join(filtered_lines)
    tag_pattern = r"\[\[([^\]]+)\]\]"
    tags = re.findall(tag_pattern, search_text)

    valid_tags = []
    invalid_tags = []

    for tag in tags:
        # Always keep the claude tag
        if tag == "claude":
            valid_tags.append(tag)
            continue

        # Skip malformed tags that look like code/commands
        if any(
            char in tag
            for char in ["$", '"', "'", "(", ")", ";", "|", "&", "=", "*", "!", "?"]
        ):
            invalid_tags.append(tag)
            continue

        # Check for spaces
        if " " in tag:
            invalid_tags.append(tag)
            continue

        # Check for uppercase
        if tag != tag.lower():
            invalid_tags.append(tag)
            continue

        # Check for special characters (allow only letters, numbers, hyphens)
        if not re.match(r"^[a-z0-9-]+$", tag):
            invalid_tags.append(tag)
            continue

        valid_tags.append(tag)

    return valid_tags, invalid_tags


def verify_content_unchanged(original_content: str, updated_content: str) -> bool:
    """Verify that only tags were added, not conversation content changed.

    Args:
        original_content: The original file content
        updated_content: The updated file content

    Returns:
        True if only tags were changed, False otherwise
    """
    # Remove all tags from both versions for comparison
    tag_pattern = r"\[\[([^\]]+)\]\]"
    original_no_tags = re.sub(tag_pattern, "", original_content).strip()
    updated_no_tags = re.sub(tag_pattern, "", updated_content).strip()

    return original_no_tags == updated_no_tags


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 KB", "2.3 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
