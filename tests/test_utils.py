"""Tests for utility functions."""

import pytest
from sage.utils import validate_tags, verify_content_unchanged, format_file_size, truncate_text


class TestValidateTags:
    """Test tag validation functionality."""

    def test_valid_tags(self):
        """Test that valid tags are accepted."""
        content = """# Test File

Some content here.

[[python]]
[[programming]]
[[test-case]]
[[claude]]"""
        
        valid_tags, invalid_tags = validate_tags(content)
        
        assert "python" in valid_tags
        assert "programming" in valid_tags
        assert "test-case" in valid_tags
        assert "claude" in valid_tags
        assert len(invalid_tags) == 0

    def test_invalid_tags_with_spaces(self):
        """Test that tags with spaces are rejected."""
        content = """# Test File

Content here.

[[valid tag]]
[[python]]"""
        
        valid_tags, invalid_tags = validate_tags(content)
        
        assert "python" in valid_tags
        assert "valid tag" in invalid_tags
        assert len(valid_tags) == 1
        assert len(invalid_tags) == 1

    def test_invalid_tags_with_special_chars(self):
        """Test that tags with special characters are rejected."""
        content = """# Test File

Content here.

[[echo "hello"]]
[[ls -la]]
[[python]]
[[$variable]]"""
        
        valid_tags, invalid_tags = validate_tags(content)
        
        assert "python" in valid_tags
        assert "echo \"hello\"" in invalid_tags
        assert "ls -la" in invalid_tags
        assert "$variable" in invalid_tags

    def test_uppercase_tags_rejected(self):
        """Test that uppercase tags are rejected."""
        content = """# Test File

Content here.

[[Python]]
[[JAVASCRIPT]]
[[python]]"""
        
        valid_tags, invalid_tags = validate_tags(content)
        
        assert "python" in valid_tags
        assert "Python" in invalid_tags
        assert "JAVASCRIPT" in invalid_tags

    def test_tags_in_code_blocks_ignored(self):
        """Test that tags within code blocks are ignored."""
        content = """# Test File

Here's some code:

```bash
echo "[[not-a-tag]]"
```

And some more content with [[actual-tag]] at the end.

[[python]]"""
        
        valid_tags, invalid_tags = validate_tags(content)
        
        # Should only find tags at the end, not in code blocks
        assert "python" in valid_tags
        assert "not-a-tag" not in valid_tags
        assert "not-a-tag" not in invalid_tags


class TestVerifyContentUnchanged:
    """Test content verification functionality."""

    def test_only_tags_added(self):
        """Test that content is unchanged when only tags are added."""
        original = """# Test File

Some content here.
More content."""
        
        updated = """# Test File

Some content here.
More content.

[[python]]
[[test]]"""
        
        assert verify_content_unchanged(original, updated) is True

    def test_content_modified(self):
        """Test that content changes are detected."""
        original = """# Test File

Some content here.
More content."""
        
        updated = """# Test File

Some MODIFIED content here.
More content.

[[python]]"""
        
        assert verify_content_unchanged(original, updated) is False

    def test_tags_modified_only(self):
        """Test that only tag changes don't trigger content change detection."""
        original = """# Test File

Content here.

[[old-tag]]"""
        
        updated = """# Test File

Content here.

[[new-tag]]
[[another-tag]]"""
        
        assert verify_content_unchanged(original, updated) is True


class TestFormatFileSize:
    """Test file size formatting."""

    def test_bytes(self):
        """Test byte formatting."""
        assert format_file_size(512) == "512 B"

    def test_kilobytes(self):
        """Test kilobyte formatting."""
        assert format_file_size(1536) == "1.5 KB"

    def test_megabytes(self):
        """Test megabyte formatting."""
        assert format_file_size(2 * 1024 * 1024 + 512 * 1024) == "2.5 MB"

    def test_gigabytes(self):
        """Test gigabyte formatting."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"


class TestTruncateText:
    """Test text truncation."""

    def test_no_truncation_needed(self):
        """Test that short text is not truncated."""
        text = "Short text"
        assert truncate_text(text, 50) == text

    def test_truncation_applied(self):
        """Test that long text is truncated with ellipsis."""
        text = "This is a very long text that should be truncated"
        result = truncate_text(text, 20)
        assert len(result) == 20
        assert result.endswith("...")
        assert result == "This is a very lo..."