#!/usr/bin/env python3
"""
Claude Code Stop Hook: Auto-open URLs and file paths from responses.

Opens URLs in Chrome and reveals file paths in Finder automatically
after each Claude response.

Setup:
  1. Copy this file to ~/.claude/hooks/open_links.py
  2. chmod +x ~/.claude/hooks/open_links.py
  3. Add to ~/.claude/settings.json:
     {
       "hooks": {
         "Stop": [{
           "hooks": [{
             "type": "command",
             "command": "python3 ~/.claude/hooks/open_links.py"
           }]
         }]
       }
     }

Requirements: Python 3.7+, macOS (uses `open` command)
Dependencies: None (stdlib only)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys


# --- Configuration (edit these to taste) ---

# Skip URLs matching these patterns
SKIP_URL_PATTERNS = [
    r"localhost",
    r"127\.0\.0\.1",
    r"example\.com",
    r"schema\.org",
    r"json-schema\.org",
    r"anthropic\.com",
    r"github\.com/anthropics/claude-code/issues",
]

# Only open paths under these prefixes (safety: won't open system paths)
ALLOWED_PATH_PREFIXES = [
    os.path.expanduser("~/"),
    "/tmp/",
]

# Browser to open URLs in (macOS app name)
BROWSER = "Google Chrome"

# Set to True to write debug info to /tmp/claude-open-links.log
DEBUG = False


# --- Core logic ---

def strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks to avoid extracting paths/URLs from code examples."""
    return re.sub(r"```[\s\S]*?```", "", text)


def extract_urls(text: str) -> list[str]:
    """Extract HTTP(S) URLs from text."""
    pattern = r'https?://[^\s\)\]>\"\'\,\`]+'
    urls = re.findall(pattern, text)

    cleaned = []
    for url in urls:
        url = url.rstrip(".")
        if any(re.search(p, url) for p in SKIP_URL_PATTERNS):
            continue
        cleaned.append(url)

    return list(dict.fromkeys(cleaned))  # dedupe, preserve order


def extract_file_paths(text: str, cwd: str | None = None) -> list[str]:
    """Extract file paths that actually exist on disk.

    Matches absolute paths (/Users/..., ~/...) and relative paths
    (lib/foo.py, src/components/App.tsx) resolved against cwd.
    """
    candidates: list[str] = []

    # 1. Absolute paths and ~/paths
    abs_pattern = r'(?:/Users/\S+|~/\S+)'
    candidates.extend(re.findall(abs_pattern, text))

    # 2. Relative paths with file extension (requires at least one slash)
    if cwd:
        rel_pattern = r'(?<![/\w])([a-zA-Z0-9_\-\.]+(?:/[a-zA-Z0-9_\-\.]+)+\.\w+)'
        for rel in re.findall(rel_pattern, text):
            full = os.path.join(cwd, rel)
            if os.path.exists(full):
                candidates.append(full)

        # 3. Relative directory paths (no extension, must be a real directory)
        rel_dir_pattern = r'(?<![/\w])([a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-]+)+)/?(?=[\s\)\]>,`\'".]|$)'
        for rel in re.findall(rel_dir_pattern, text):
            full = os.path.join(cwd, rel)
            if os.path.isdir(full):
                candidates.append(full)

    valid = []
    for path_str in candidates:
        path_str = path_str.rstrip(".,;:)]\"\'>}")
        expanded = os.path.expanduser(path_str)

        if not any(expanded.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES):
            continue

        if os.path.exists(expanded):
            valid.append(expanded)

    return list(dict.fromkeys(valid))  # dedupe, preserve order


def open_url(url: str) -> None:
    """Open a URL in the configured browser."""
    subprocess.Popen(
        ["open", "-a", BROWSER, url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def reveal_in_finder(path: str) -> None:
    """Reveal a file/directory in Finder."""
    if os.path.isdir(path):
        subprocess.Popen(["open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["open", "-R", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def log_debug(msg: str) -> None:
    """Append a debug line to the log file (only when DEBUG=True)."""
    if not DEBUG:
        return
    try:
        with open("/tmp/claude-open-links.log", "a") as f:
            f.write(msg + "\n")
    except OSError:
        pass


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    cwd = hook_input.get("cwd")

    # Use last_assistant_message directly from hook input
    text = hook_input.get("last_assistant_message")
    if not text:
        log_debug("No assistant text in hook input")
        return

    log_debug(f"Text ({len(text)} chars): {text[:200]}")

    clean_text = strip_code_blocks(text)

    urls = extract_urls(clean_text)
    paths = extract_file_paths(clean_text, cwd=cwd)

    log_debug(f"URLs: {urls}")
    log_debug(f"Paths: {paths}")

    for url in urls:
        open_url(url)

    for path in paths:
        reveal_in_finder(path)


if __name__ == "__main__":
    main()
