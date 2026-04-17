# claude-code-hook-open

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) hook that automatically opens URLs in your browser and reveals file paths in Finder whenever Claude mentions them in a response.

No extra tokens. No API calls. Just a local script that fires after each response.

## Install via Claude Code

Paste this into any Claude Code session:

```
Install this Claude Code hook for me: https://github.com/dani-interappy/hook-open

1. Download https://raw.githubusercontent.com/dani-interappy/hook-open/main/open_links.py to ~/.claude/hooks/open_links.py
2. chmod +x ~/.claude/hooks/open_links.py
3. Add the Stop hook to ~/.claude/settings.json — merge it without touching any existing keys:
   "hooks": { "Stop": [{ "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/open_links.py" }] }] }
4. Show me the hooks section of settings.json to confirm it looks right
```

Then restart Claude Code.

## Manual setup

### 1. Download the script

```bash
curl -o ~/.claude/hooks/open_links.py https://raw.githubusercontent.com/dani-interappy/hook-open/main/open_links.py
chmod +x ~/.claude/hooks/open_links.py
```

### 2. Add the hook to your settings

Open `~/.claude/settings.json` in any text editor:

```bash
open ~/.claude/settings.json
```

Add a `"hooks"` key at the top level of the JSON object. If your file currently looks like this:

```json
{
  "permissions": { ... }
}
```

Add the hooks block so it looks like this:

```json
{
  "permissions": { ... },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/open_links.py"
          }
        ]
      }
    ]
  }
}
```

If you already have a `"hooks"` key, add `"Stop"` as a new entry inside it.

### 3. Restart Claude Code

The new hook loads on startup.

## What it catches

| Pattern | Example | Action |
|---------|---------|--------|
| URLs | `https://news.ycombinator.com` | Opens in Chrome |
| Absolute paths | `/Users/you/project/src/app.py` | Reveals in Finder |
| Home paths | `~/Documents/notes.md` | Reveals in Finder |
| Relative paths | `src/components/App.tsx` | Resolves against cwd, reveals in Finder |

Paths must actually exist on disk to trigger. Code blocks are ignored to avoid false positives.

## Configuration

Edit the top of `open_links.py` to customize:

```python
# Change browser (default: Google Chrome)
BROWSER = "Arc"

# Add domains to skip
SKIP_URL_PATTERNS = [
    r"localhost",
    r"example\.com",
    # add your own...
]

# Restrict which paths can be opened (safety)
ALLOWED_PATH_PREFIXES = [
    os.path.expanduser("~/"),
    "/tmp/",
]

# Enable debug logging to /tmp/claude-open-links.log
DEBUG = True
```

## How it works

1. Claude Code fires a `Stop` hook after every response
2. The hook receives `last_assistant_message` (the response text) via JSON on stdin
3. The script strips code blocks, then extracts URLs and file paths with regex
4. URLs open in your browser via `open -a`; files are revealed in Finder via `open -R`
5. Runs in the background — zero latency added to your workflow

**Zero token cost.** Hooks are local shell commands that run outside the conversation. Claude never sees that the hook fired.

## Requirements

- macOS (uses the `open` command)
- Python 3.7+
- Claude Code

## Troubleshooting

Enable debug logging by setting `DEBUG = True` in the script, then check:

```bash
cat /tmp/claude-open-links.log
```

## License

MIT
