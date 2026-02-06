# Repo Atlas

A [Claude Code](https://claude.ai/code) skill that builds a **persistent context system** for any git repository — so engineers and LLM agents can understand your codebase fast with minimal searching.

Built by [@cathrynlavery](https://twitter.com/cathrynlavery) at [founder.codes](https://founder.codes)

## What It Does

Run `/repo-atlas` in any project and it will:

1. **Auto-generate** a repo map with directory tree, entrypoints, file stats, and changelog
2. **Guide you** through writing architecture, domain model, critical flows, state sources, gotchas, and test docs
3. **Add an agent on-ramp** to your `CLAUDE.md` with a two-agent workflow (plan + verify)
4. **Create build targets** (`make atlas-generate` / `make atlas-check`) for CI integration

The result is a `docs/atlas/` folder with 10 structured docs that any engineer or AI agent can load for instant context.

## Supports

**Languages:** Python, JavaScript/TypeScript, Go, Rust, Swift, Java, Kotlin, C/C++, C#, PHP, Elixir, Dart

**Build systems:** npm, Cargo, Go modules, pip/pyproject, Gradle, Maven, XcodeGen, SPM, Bundler, CMake, Bazel, Earthly

**CI:** GitHub Actions, GitLab CI, CircleCI, Jenkins, Travis, Azure Pipelines, Bitbucket Pipelines, Cloud Build, CodeBuild

## Install

Copy the skill into your Claude Code skills directory:

```bash
# Clone and copy
git clone https://github.com/cathrynlavery/repo-atlas.git
cp -r repo-atlas ~/.agents/skills/repo-atlas

# Or just copy the directory manually
```

Then in any project, say `/repo-atlas` or "map this repo" or "create atlas docs".

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill definition — 7-phase workflow |
| `scripts/generate_atlas.py` | Generator script (Python 3.7+, stdlib only) |
| `references/atlas-templates.md` | Structure templates for manual docs |

## License

MIT

---

Made with Claude Code by [@cathrynlavery](https://twitter.com/cathrynlavery) | [founder.codes](https://founder.codes)
