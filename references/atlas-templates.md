# Atlas Document Templates

Structure guidance for each manual atlas document. Each doc should be 50-150 lines with **real** repo paths and code references.

---

## 00_README.md

```markdown
# Atlas — [Repo Name]

## What Is This?

The `docs/atlas/` folder is a persistent context system — structured documentation
that helps engineers and LLM coding agents understand this codebase quickly.

## Files

| File | Purpose | Auto-generated? |
|------|---------|----------------|
| `00_README.md` | This file — how to use the atlas | No |
| `01_ARCHITECTURE.md` | System overview, modules, layers | No |
| `02_DOMAIN_MODEL.md` | Core entities, vocabulary, state machines | No |
| `03_CRITICAL_FLOWS.md` | Happy-path call chains for top flows | No |
| `04_STATE_SOURCES_OF_TRUTH.md` | Where state lives + reconciliation rules | No |
| `05_EXTERNAL_DEPENDENCIES.md` | External systems/APIs | No |
| `06_GOTCHAS.md` | Known traps, race conditions, fragile zones | No |
| `07_TEST_MATRIX.md` | Test structure + how to prove correctness | No |
| `08_CHANGELOG_LAST_14_DAYS.md` | Recent changes summary | Yes |
| `repo-map.md` | Directory tree, router table, entrypoints | Partially |

## How to Use

1. Start with `repo-map.md` to orient yourself
2. Read the domain-specific doc for your task area
3. Check `06_GOTCHAS.md` before modifying fragile areas
4. Only then dive into source files

## Maintenance

- Run `make atlas-generate` (or `python3 scripts/atlas/generate_atlas.py --write`) after structural changes
- Update manual docs when architecture, flows, or state management changes
- `make atlas-check` in CI to catch stale auto-generated files
```

---

## 01_ARCHITECTURE.md

Include:
- **System overview**: One paragraph describing what the system does and how it's structured
- **Component diagram** (text): Show modules/services/targets and how they communicate
- **Layer breakdown**: For each major component, describe its responsibility and boundaries
- **Communication patterns**: How components talk to each other (HTTP, IPC, events, shared files, message queues)
- **Key design decisions**: Why the architecture is the way it is (with tradeoffs noted)

Example structure:
```markdown
# Architecture

## Overview
[1-2 paragraphs: what the system does, high-level structure]

## Components

### [Component A]
- **Purpose**: [what it does]
- **Location**: `path/to/component/`
- **Communicates with**: [other components] via [mechanism]

### [Component B]
...

## Communication Patterns
[How data flows between components]

## Key Decisions
- [Decision]: [Why] (tradeoff: [what was sacrificed])
```

---

## 02_DOMAIN_MODEL.md

Include:
- **Core entities**: The main "nouns" in the system with their key fields
- **Canonical vocabulary**: Terms used in the codebase and what they mean
- **State machines**: For entities with lifecycle states, diagram the transitions
- **Relationships**: How entities relate to each other

Example structure:
```markdown
# Domain Model

## Core Entities

### [Entity]
- **Defined in**: `path/to/model.ext`
- **Key fields**: field1, field2, field3
- **Lifecycle**: created → active → [archived|deleted]

## Vocabulary

| Term | Meaning | Where Used |
|------|---------|-----------|
| [term] | [definition] | [files/modules] |

## State Machines

### [Entity] Lifecycle
```
[state diagram using ASCII/mermaid]
```
```

---

## 03_CRITICAL_FLOWS.md

Include:
- Top 3-5 user-facing flows traced through the code
- For each flow: trigger → sequence of calls → side effects → end state
- Use file:function notation for each step

Example structure:
```markdown
# Critical Flows

## Flow 1: [Name]

**Trigger**: [user action or system event]

1. `path/file.ext:functionA()` — [what happens]
2. `path/file.ext:functionB()` — [what happens]
3. `path/file.ext:functionC()` — [side effect: writes to X]

**End state**: [what's true when this flow completes]
**Gotchas**: [link to 06_GOTCHAS.md if relevant]
```

---

## 04_STATE_SOURCES_OF_TRUTH.md

Include:
- Every place state is stored (database, cache, files, in-memory, client-side)
- For each: what it stores, who reads/writes, consistency guarantees
- Reconciliation rules: when two sources disagree, which wins?

Example structure:
```markdown
# State — Sources of Truth

## [State Store 1: e.g., Database / App Group / Redux Store]
- **Location**: [path or URL]
- **Stores**: [what data]
- **Written by**: [component/service]
- **Read by**: [components/services]
- **Consistency**: [guarantees — eventual, strong, etc.]

## Reconciliation Rules
- [Rule 1: e.g., "Server state always wins over cached state"]
- [Rule 2: e.g., "File on disk is the source of truth for blocking rules"]
```

---

## 05_EXTERNAL_DEPENDENCIES.md

Include:
- Package dependencies with their purpose and version constraints
- External APIs/services the system calls
- For each: what happens if it's down or unreachable?

Example structure:
```markdown
# External Dependencies

## Package Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| [name] | [what we use it for] | [constraint] |

## External Services

### [Service Name]
- **Used for**: [purpose]
- **Integration point**: `path/to/integration.ext`
- **If unavailable**: [what happens — graceful degradation? error? offline mode?]
```

---

## 06_GOTCHAS.md

Include:
- Race conditions and timing issues
- Initialization ordering dependencies
- Files that look safe to change but have hidden side effects
- Common mistakes previous developers have made
- Things that break in specific environments (CI, production, etc.)

Example structure:
```markdown
# Gotchas

## [Category: e.g., Initialization / Concurrency / IPC]

### [Gotcha Title]
- **File**: `path/to/file.ext`
- **Risk**: [what goes wrong]
- **Rule**: [what to do / not do]
- **Why**: [explanation of the underlying issue]
```

---

## 07_TEST_MATRIX.md

Include:
- How to run tests (commands)
- Test file organization and naming conventions
- What's covered and what's NOT covered
- How to add a new test
- CI integration notes

Example structure:
```markdown
# Test Matrix

## Running Tests

```bash
[command to run all tests]
[command to run specific test file]
[command to run with coverage]
```

## Test Structure

| Directory | What It Tests | Framework |
|-----------|--------------|-----------|
| `path/to/tests/` | [description] | [framework] |

## Coverage Gaps
- [Area not covered and why]

## Adding Tests
[Brief guide to adding a new test for this codebase]
```
