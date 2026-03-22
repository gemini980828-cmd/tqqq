---
description: Pre-work tool consideration checklist — evaluate which installed power tools to leverage before starting any task
---

# /toolcheck — Power Tools Consideration

Before starting work, evaluate which of the following tools would benefit the current task.
Go through each tool and decide: **USE**, **SKIP**, or **MAYBE**. State your reasoning briefly.

## Step 1: Sequential Thinking (MCP)

Consider whether the task has enough complexity to benefit from structured multi-step reasoning.

**USE when**: complex debugging, architectural decisions, multi-step planning, ambiguous requirements
**SKIP when**: simple edits, direct questions, routine changes

→ If USE: invoke `mcp_sequential-thinking_sequentialthinking` to break down the problem before acting.

## Step 2: Context7 (MCP)

Consider whether you need up-to-date documentation or code examples for any library/framework involved.

**USE when**: unfamiliar APIs, version-specific behavior questions, framework best practices needed
**SKIP when**: well-known patterns, project-internal logic, no external library involved

→ If USE: call `mcp_context7_resolve-library-id` → `mcp_context7_query-docs` to pull relevant docs.

## Step 3: Serena (MCP)

Consider whether LSP-powered semantic code analysis would help (symbol search, references, type info).

**USE when**: navigating unfamiliar codebase areas, refactoring, finding all references to a symbol, understanding type hierarchies
**SKIP when**: working on files you already understand, simple text edits, non-code tasks

→ If USE: leverage Serena's `find_symbol`, `find_referencing_symbols`, `get_symbols_overview` tools.

## Step 4: Superpowers Skills

Consider whether a structured workflow from superpowers would improve quality.

| Skill | Use When |
|-------|----------|
| `writing-plans` | Feature design, multi-file changes, architecture work |
| `brainstorming` | Open-ended problems, exploring approaches |
| `test-driven-development` | New features that need tests first |
| `systematic-debugging` | Bugs with unclear root cause |
| `dispatching-parallel-agents` | Large tasks that can be parallelized |
| `executing-plans` | A plan exists and needs structured execution |
| `requesting-code-review` | Finished implementation needing review |
| `verification-before-completion` | Before marking any task as done |

→ If USE: read the relevant `~/.agents/skills/superpowers/{skill}/SKILL.md` and follow its workflow.

## Step 5: Announce Decision

State your tool selection summary in this format:

```
🔧 Toolcheck:
- Sequential Thinking: [USE/SKIP] — [reason]
- Context7: [USE/SKIP] — [reason]
- Serena: [USE/SKIP] — [reason]
- Superpowers: [skill name or SKIP] — [reason]
```

Then proceed with the task.
