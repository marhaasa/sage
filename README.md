# Sage

An intelligent semantic tagging CLI tool for markdown files using Claude.

Sage analyzes your markdown content and automatically adds relevant semantic tags, making your notes more discoverable and organized.

## Prerequisites

Before installing sage, you'll need:

- **Python 3.8+**
- **[Claude Code CLI](https://claude.ai/code)** - Get access at [claude.ai/code](https://claude.ai/code)

### Setting up Claude Code CLI

1. Sign up for Claude Code access at [claude.ai/code](https://claude.ai/code)
2. Install the Claude Code CLI following the official documentation
3. Verify installation: `claude --version`

## Installation

### Via Homebrew (Recommended)

```bash
brew tap marhaasa/tools
brew install marhaasa/tools/sage
```

### Via pip

```bash
pip install sage
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
   claude --version
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

- **Intelligent Analysis**: Uses Claude to understand content and suggest relevant tags
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

- Python 3.8+
- Claude Code CLI (claude.ai/code)

## Troubleshooting

### Common Issues

**"claude: command not found"**
- Ensure Claude Code CLI is installed and in your PATH
- Try running `claude --version` to verify installation
- Check the [Claude Code documentation](https://claude.ai/code) for setup help

**"No tags added" or empty results**
- Verify your markdown file has substantive content (not just headers)
- Check that Claude Code CLI is properly authenticated
- Try running `claude "Hello"` to test your Claude Code setup

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
- Include the output of `sage --version` and `claude --version`

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
