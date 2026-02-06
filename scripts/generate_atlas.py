#!/usr/bin/env python3
"""
Atlas generator — works for any repository.

Regenerates auto-generated atlas files:
  - docs/atlas/repo-map.md              (directory tree, entrypoints, file stats)
  - docs/atlas/08_CHANGELOG_LAST_14_DAYS.md  (git log summary)

Usage:
  python3 scripts/atlas/generate_atlas.py --write   # Write files (default)
  python3 scripts/atlas/generate_atlas.py --check    # Exit non-zero if stale

Customization:
  Edit the CONFIGURATION section below to match your repository.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ATLAS_DIR = REPO_ROOT / "docs" / "atlas"
REPO_NAME = REPO_ROOT.name

# ============================================================================
# CONFIGURATION — Customize this section for your repository
# ============================================================================

# Directories/files to exclude (matched by exact path segment, NOT substring).
# Each entry is compared against individual directory names in the path.
IGNORE_NAMES = {
    ".git", "node_modules", "__pycache__", ".build", "DerivedData",
    ".DS_Store", "Pods", "build", "dist", ".next", ".nuxt", ".output",
    ".venv", "venv", ".env", ".tox", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "coverage", ".nyc_output", ".turbo", ".cache",
    "target", "obj", ".gradle", ".idea", ".vscode",
    ".beads", ".swiftpm", "Assets.xcassets",
}

# Directory annotations — map directory names to short descriptions.
# Set value to None to skip annotation. Add your own for key directories.
TREE_ANNOTATIONS: dict[str, str | None] = {
    # Example: "src": "Main source code",
    # Example: "lib": "Core library",
    # Example: "tests": "Test suite",
}

# Entrypoint file names to detect (matched by filename only)
ENTRYPOINT_NAMES = {
    # Python
    "main.py", "app.py", "manage.py", "wsgi.py", "asgi.py", "__main__.py",
    "cli.py", "server.py",
    # JavaScript/TypeScript
    "index.js", "index.ts", "index.tsx", "main.js", "main.ts", "main.tsx",
    "app.js", "app.ts", "app.tsx", "server.js", "server.ts",
    # Go
    "main.go",
    # Rust
    "main.rs", "lib.rs",
    # Swift
    "main.swift",
    # Ruby
    "config.ru", "Rakefile",
    # Java/Kotlin
    "Application.java", "App.java", "Main.java", "Application.kt", "App.kt",
    # C/C++
    "main.c", "main.cpp", "main.cc",
    # C#
    "Program.cs",
    # PHP
    "index.php", "artisan",
    # Elixir
    "mix.exs",
    # Dart
    "main.dart",
}

# Entrypoint path patterns — match against relative path (e.g., "cmd/*/main.go")
# Uses simple fnmatch-style matching against the relative path from repo root.
ENTRYPOINT_PATH_PATTERNS: dict[str, str] = {
    "cmd/*/main.go": "Go command entry point",
    "cmd/main.go": "Go command entry point",
    "src/main.rs": "Rust binary entry point",
    "src/lib.rs": "Rust library entry point",
}

# Patterns to search for in file content (for annotation-based entrypoint detection)
ENTRYPOINT_CONTENT_MARKERS = {
    "@main": "Entry point (@main)",                       # Swift
    "@SpringBootApplication": "Spring Boot entry point",  # Java/Kotlin
    "func main()": "Go entry point",                      # Go
    "fn main()": "Rust entry point",                      # Rust
}

# Conventional commit prefixes → category names (supports `feat!:` breaking syntax)
CONVENTIONAL_COMMITS = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "ci": "CI/CD",
    "build": "Build",
    "chore": "Chores",
    "test": "Tests",
    "perf": "Performance",
    "style": "Style",
}

# Max tree depth (increase for flatter repos, decrease for deep nesting)
MAX_TREE_DEPTH = 3

# Changelog window in days (fallback: last 20 commits if none in window)
CHANGELOG_DAYS = 14

# ============================================================================
# END CONFIGURATION
# ============================================================================


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _is_ignored(path: Path) -> bool:
    """Check if any path segment matches an ignored name (exact segment match)."""
    return any(part in IGNORE_NAMES for part in path.relative_to(REPO_ROOT).parts)


# ---------------------------------------------------------------------------
# Directory tree generation
# ---------------------------------------------------------------------------

def _collect_root_files() -> list[str]:
    """Collect notable files at the repo root for the tree."""
    notable_extensions = {
        ".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini",
        ".swift", ".py", ".js", ".ts", ".go", ".rs", ".java", ".kt", ".rb",
        ".c", ".cpp", ".cs", ".php", ".ex", ".exs", ".dart",
    }
    notable_names = {
        "Makefile", "Dockerfile", "Gemfile", "Rakefile", "Procfile",
        "Vagrantfile", "Jenkinsfile", "LICENSE", "LICENCE",
    }
    files = []
    try:
        for entry in sorted(REPO_ROOT.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_file() or entry.name in IGNORE_NAMES:
                continue
            if entry.name.startswith("."):
                continue
            if entry.suffix in notable_extensions or entry.name in notable_names:
                files.append(entry.name)
    except PermissionError:
        pass
    return files


def generate_tree(root: Path, prefix: str = "", depth: int = 0) -> list[str]:
    """Generate a directory tree up to MAX_TREE_DEPTH levels."""
    if depth > MAX_TREE_DEPTH:
        return []

    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return []

    dirs = [e for e in entries if e.is_dir() and e.name not in IGNORE_NAMES]

    for i, entry in enumerate(dirs):
        is_last = i == len(dirs) - 1
        connector = "└── " if is_last else "├── "
        annotation = TREE_ANNOTATIONS.get(entry.name)
        suffix = f"  # {annotation}" if annotation else ""
        lines.append(f"{prefix}{connector}{entry.name}/{suffix}")
        extension = "    " if is_last else "│   "
        lines.extend(generate_tree(entry, prefix + extension, depth + 1))

    return lines


# ---------------------------------------------------------------------------
# Entrypoints detection
# ---------------------------------------------------------------------------

def find_entrypoints() -> list[tuple[str, str]]:
    """Detect entry files by name, path pattern, and content markers."""
    entrypoints = []
    seen_paths: set[str] = set()

    SOURCE_EXTENSIONS = {
        ".swift", ".py", ".ts", ".tsx", ".js", ".jsx",
        ".go", ".rs", ".java", ".kt", ".rb", ".c", ".cpp", ".cc",
        ".cs", ".php", ".ex", ".exs", ".dart",
    }

    # Single pass over the repo for filename + content marker detection
    from fnmatch import fnmatch

    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or _is_ignored(path):
            continue
        rel = str(path.relative_to(REPO_ROOT))

        # 1a. Match by filename
        if path.name in ENTRYPOINT_NAMES and rel not in seen_paths:
            entrypoints.append((rel, f"Entry point ({path.name})"))
            seen_paths.add(rel)
            continue

        # 1b. Match by path pattern
        for pattern, description in ENTRYPOINT_PATH_PATTERNS.items():
            if fnmatch(rel, pattern) and rel not in seen_paths:
                entrypoints.append((rel, description))
                seen_paths.add(rel)
                break
        if rel in seen_paths:
            continue

        # 2. Match by content markers (source files only)
        if path.suffix not in SOURCE_EXTENSIONS:
            continue
        try:
            content = path.read_text(errors="ignore")[:8000]
            for marker, description in ENTRYPOINT_CONTENT_MARKERS.items():
                if marker in content:
                    entrypoints.append((rel, description))
                    seen_paths.add(rel)
                    break
        except (OSError, UnicodeDecodeError):
            pass

    # 3. Build config files
    build_files = [
        ("Makefile", "Build commands"),
        ("package.json", "Node.js package config"),
        ("Cargo.toml", "Rust package config"),
        ("go.mod", "Go module config"),
        ("pyproject.toml", "Python project config"),
        ("setup.py", "Python package config"),
        ("setup.cfg", "Python package config"),
        ("build.gradle", "Gradle build config"),
        ("build.gradle.kts", "Gradle build config (Kotlin)"),
        ("pom.xml", "Maven build config"),
        ("project.yml", "XcodeGen project definition"),
        ("Package.swift", "Swift Package Manager"),
        ("Gemfile", "Ruby dependencies"),
        ("docker-compose.yml", "Docker Compose"),
        ("docker-compose.yaml", "Docker Compose"),
        ("compose.yml", "Docker Compose"),
        ("compose.yaml", "Docker Compose"),
        ("Dockerfile", "Docker build"),
        ("CMakeLists.txt", "CMake build config"),
        ("BUILD", "Bazel build config"),
        ("WORKSPACE", "Bazel workspace"),
        ("Tiltfile", "Tilt dev environment"),
        ("Earthfile", "Earthly build config"),
    ]
    for name, desc in build_files:
        if (REPO_ROOT / name).exists() and name not in seen_paths:
            entrypoints.append((name, desc))

    # 4. CI files
    ci_patterns = [
        (".github/workflows", "GitHub Actions"),
        (".gitlab-ci.yml", "GitLab CI"),
        (".circleci/config.yml", "CircleCI"),
        ("Jenkinsfile", "Jenkins"),
        (".travis.yml", "Travis CI"),
        ("azure-pipelines.yml", "Azure Pipelines"),
        ("bitbucket-pipelines.yml", "Bitbucket Pipelines"),
        ("cloudbuild.yaml", "Google Cloud Build"),
        ("buildspec.yml", "AWS CodeBuild"),
    ]
    for pattern, desc in ci_patterns:
        ci_path = REPO_ROOT / pattern
        if ci_path.exists():
            if ci_path.is_dir():
                for f in ci_path.iterdir():
                    if f.suffix in {".yml", ".yaml"}:
                        entrypoints.append((str(f.relative_to(REPO_ROOT)), desc))
            else:
                entrypoints.append((pattern, desc))

    return sorted(set(entrypoints))


# ---------------------------------------------------------------------------
# File statistics
# ---------------------------------------------------------------------------

def file_stats() -> dict[str, int]:
    """Count files by extension (includes extensionless files like Dockerfile)."""
    counts: Counter = Counter()
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or _is_ignored(path):
            continue
        ext = path.suffix if path.suffix else f"(no ext: {path.name})"
        counts[ext] += 1
    # Group extensionless files and keep top 15
    return dict(counts.most_common(15))


# ---------------------------------------------------------------------------
# Changelog generation
# ---------------------------------------------------------------------------

def parse_commit(line: str) -> tuple[str, str, str]:
    """Parse a git log line into (hash, category, message).

    Supports conventional commits including breaking change syntax (feat!:).
    """
    parts = line.split(" ", 1)
    if len(parts) < 2:
        return parts[0] if parts else "", "Other", ""

    commit_hash, message = parts
    msg_lower = message.lower()
    for prefix, category in CONVENTIONAL_COMMITS.items():
        if (msg_lower.startswith(prefix + ":")
                or msg_lower.startswith(prefix + "(")
                or msg_lower.startswith(prefix + "!:")
                or msg_lower.startswith(prefix + "!(")):
            return commit_hash, category, message
    return commit_hash, "Other", message


def generate_changelog() -> str:
    """Generate changelog from git log."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"--since={CHANGELOG_DAYS} days ago", "--no-merges"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    except (subprocess.SubprocessError, FileNotFoundError):
        lines = []

    if not lines:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-20", "--no-merges"],
                capture_output=True, text=True, cwd=REPO_ROOT
            )
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        except (subprocess.SubprocessError, FileNotFoundError):
            lines = []

    categories: dict[str, list[tuple[str, str]]] = {}
    for line in lines:
        if not line.strip():
            continue
        commit_hash, category, message = parse_commit(line.strip())
        categories.setdefault(category, []).append((commit_hash, message))

    today = datetime.now().strftime("%Y-%m-%d")

    output = [
        "<!-- AUTO-GENERATED by scripts/atlas/generate_atlas.py -- do not edit manually -->",
        f"# Changelog -- Last {CHANGELOG_DAYS} Days",
        "",
        f"*Generated: {today}*",
        "",
        "## Summary",
        "",
        f"{len(lines)} commits in the last {CHANGELOG_DAYS} days.",
        "",
        "## Changes by Category",
        "",
    ]

    ordered_categories = list(CONVENTIONAL_COMMITS.values()) + ["Other"]
    for category in dict.fromkeys(ordered_categories):
        commits = categories.get(category, [])
        if not commits:
            continue
        output.append(f"### {category}")
        for commit_hash, message in commits:
            output.append(f"- `{commit_hash}` {message}")
        output.append("")

    return "\n".join(output)


# ---------------------------------------------------------------------------
# Repo map generation
# ---------------------------------------------------------------------------

def generate_repo_map() -> str:
    """Generate the full repo-map.md content."""
    tree_lines = generate_tree(REPO_ROOT)
    tree = "\n".join(tree_lines)

    # Root-level files
    root_files = _collect_root_files()
    root_files_section = ""
    if root_files:
        root_files_list = "\n".join(f"- `{f}`" for f in root_files)
        root_files_section = f"\n## Root Files\n\n{root_files_list}\n"

    entrypoints = find_entrypoints()
    entrypoints_table = "| File | Role |\n|------|------|\n"
    for path, desc in entrypoints:
        entrypoints_table += f"| `{path}` | {desc} |\n"

    stats = file_stats()
    stats_lines = "\n".join(f"| `{ext}` | {count} |" for ext, count in stats.items())
    stats_table = f"| Extension | Count |\n|-----------|-------|\n{stats_lines}\n"

    return f"""<!-- AUTO-GENERATED by scripts/atlas/generate_atlas.py -- do not edit manually -->
# Repo Map -- {REPO_NAME}

## Directory Tree

```
{REPO_NAME}/
{tree}
```
{root_files_section}
## Entrypoints

{entrypoints_table}

## File Statistics

{stats_table}

## Where to Look for X -- Router Table

<!-- MANUAL: Add 10-15 rows mapping common tasks to files -->
<!-- Example:
| Task | Start Here |
|------|-----------|
| Fix authentication | `src/auth/handler.ts` |
| Add a new API route | `src/routes/`, `src/controllers/` |
-->

| Task | Start Here |
|------|-----------|
| TODO | Add rows for the top tasks in this repo |

## Danger Zones

<!-- MANUAL: Add fragile files/areas and why they're fragile -->
<!-- Example:
| File/Area | Why It's Fragile |
|-----------|-----------------|
| `src/db/migrations/` | Order-dependent, affects production schema |
-->

| File/Area | Why It's Fragile |
|-----------|-----------------|
| TODO | Add fragile areas for this repo |
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate atlas files for this repository")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", default=True, help="Write files (default)")
    group.add_argument("--check", action="store_true", help="Check if files are up to date")
    args = parser.parse_args()

    ATLAS_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        ATLAS_DIR / "repo-map.md": generate_repo_map(),
        ATLAS_DIR / "08_CHANGELOG_LAST_14_DAYS.md": generate_changelog(),
    }

    if args.check:
        stale = []
        for path, content in files.items():
            if not path.exists():
                stale.append(f"MISSING: {path.relative_to(REPO_ROOT)}")
                continue
            existing = path.read_text()
            if existing != content:
                stale.append(f"STALE: {path.relative_to(REPO_ROOT)}")

        if stale:
            print("Atlas files are out of date:")
            for s in stale:
                print(f"  {s}")
            print("\nRun: python3 scripts/atlas/generate_atlas.py --write")
            sys.exit(1)
        else:
            print("Atlas files are up to date.")
            sys.exit(0)
    else:
        for path, content in files.items():
            path.write_text(content)
            print(f"  Wrote {path.relative_to(REPO_ROOT)}")
        print("Atlas generation complete.")


if __name__ == "__main__":
    main()
