# Sage

An intelligent semantic tagging CLI tool for markdown files using the Claude Code SDK.

Sage analyzes your markdown content and automatically adds relevant semantic tags, making your notes more discoverable and organized.

## Prerequisites

Before installing sage, you'll need:

- **Python 3.10+**
- **[Claude Code SDK](https://claude.ai/code)** - Get access at [claude.ai/code](https://claude.ai/code)

### Setting up Claude Code SDK

1. Sign up for Claude Code access at [claude.ai/code](https://claude.ai/code)
2. The Claude Code SDK will be automatically installed as a dependency
3. Ensure you have proper authentication set up for Claude Code

## Privacy & Data Considerations

**⚠️ Important Privacy Notice**

Sage sends your markdown file content to Claude (Anthropic's AI service) for analysis and tag generation. This means:

- **Your content leaves your local machine** and is processed by Claude's AI service
- **Consider the sensitivity of your content** before processing files with Sage
- **Rule of thumb**: Don't use Sage on any markdown files you wouldn't want your mom to see
- **Review your content** before running Sage on files containing personal, confidential, or sensitive information

**What Sage does:**
- Sends file content to Claude for semantic analysis
- Receives suggested tags back from the service
- Does not permanently store your content (processing is transient)

**What you should do:**
- Be mindful of what content you're processing
- Avoid using Sage on files with personal information, passwords, API keys, or confidential data
- Consider your organization's data handling policies before use

By using Sage, you acknowledge that your markdown content will be sent to and processed by Claude's AI service.

## Installation

### Via Homebrew (Recommended)

```bash
brew tap marhaasa/tools
brew install marhaasa/tools/sage
```

### Development Installation

```bash
git clone https://github.com/marhaasa/sage.git
cd sage
pip install -e ".[dev]"
```

## Quick Start

1. **Install sage** (see installation options above)
2. **Test your setup:**
   ```bash
   sage --version
   ```
3. **Tag your first file:**
   ```bash
   sage file my-notes.md
   ```
4. **Tag all files in a directory:**
   ```bash
   sage dir notes/
   ```

## Usage

### Tag a Single File

```bash
sage file my-notes.md
```

### Tag Multiple Files

```bash
sage files notes1.md notes2.md notes3.md
```

### Tag All Markdown Files in a Directory

```bash
sage dir notes/
```

### Advanced Options

```bash
# Concurrent processing with custom worker count
sage dir notes/ --concurrent --workers 10

# Force retag files that already have tags
sage dir notes/ --force

# Quiet mode (minimal output)
sage file notes.md --quiet

# JSON output for integration
sage file notes.md --json
```

## Features

- **Intelligent Analysis**: Uses Claude Code SDK to understand content and suggest relevant tags
- **Safe Processing**: Verifies content integrity and provides automatic rollback
- **Concurrent Processing**: Fast batch processing with configurable concurrency
- **Format Validation**: Ensures tags follow proper format (lowercase, single words)
- **Code-Aware**: Avoids tagging code blocks and handles technical content appropriately
- **Neovim Integration**: JSON output mode for editor integration

## Tag Format

Sage adds tags at the end of your markdown files:

```markdown
# My Great Article

Content goes here...

[[programming]]
[[python]]
[[cli]]
[[sage]]
```

## Requirements

- Python 3.10+
- Claude Code SDK (automatically installed as dependency)

## Troubleshooting

### Common Issues

**"No tags added" or empty results**
- Verify your markdown file has substantive content (not just headers)
- Check that Claude Code SDK is properly authenticated
- Ensure you have proper access to Claude Code services

**Timeout errors**
- Increase timeout with `--timeout 300` (5 minutes)
- Check your internet connection
- Retry with `--force` if the file was partially processed

**Permission errors**
- Ensure you have write permissions to the markdown files
- Check that files aren't locked by another application

### Getting Help

- Check the [issues page](https://github.com/marhaasa/sage/issues) for known problems
- Create a new issue with your error message and system info
- Include the output of `sage --version` and your Python version

## Integration

### Neovim

Add this function to your Neovim config for quick tagging:

```lua
vim.api.nvim_create_user_command('SageTag', function()
    local file = vim.fn.expand('%:p')
    vim.fn.system('sage file --quiet "' .. file .. '"')
    vim.cmd('edit')  -- Reload the file
end, {})
```

### Shell Alias

```bash
alias st='sage file'
```

## License

MIT License - see [LICENSE](LICENSE) for details.
