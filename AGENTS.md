### Workflow Orchestration

### 1. Plan Node Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One tack per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fizing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimat Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

## Response Recommendation Protocol

When answering future task requests, first recommend the best OMX workflow before executing. The recommendation should be explicit about **which skill/mode/tool to use, why, and whether to start immediately**.

### Default Answer Format

For non-trivial requests, answer in this order:

1. **작업 분류** — what kind of task this is
2. **추천 실행 방식** — recommended skill/mode chain
3. **추천 도구** — concrete tools to use
4. **추천 이유** — why this is the best fit
5. **바로 진행할 내용** — what will happen next if execution starts now

Use this response template:

```md
## 추천
- 작업 분류: <bugfix / feature / refactor / planning / parallel-work / explanation>
- 추천 실행 방식: <example: $plan → $ralph>
- 추천 도구: <LSP diagnostics, AST grep, tests, tmux team, MCP memory/state ...>
- 추천 이유: <1-3 short bullets or sentences>
- 바로 진행: <next concrete action>
```

For simple requests, use a short form:

```md
## 추천
- 실행 방식: <direct / $plan / $ralph / $team / $autopilot>
- 이유: <short reason>
- 바로 진행: <next action>
```

### Task-Type Routing Rules

#### 1. Explanation / advisory / comparison requests
- Use **plain conversational response**
- No execution mode by default
- Use web lookup only when freshness/verification matters
- Suggested wording:
  - `작업 분류: 설명/가이드`
  - `추천 실행 방식: 실행 없음`

#### 2. Small, clear, single-scope changes
- Preferred: **direct execution** or `/prompts:executor`
- Use lightweight local tools first: file reads, focused edits, targeted tests
- Do **not** over-upgrade to `$team` or `$autopilot`
- Suggested wording:
  - `작업 분류: 단일 수정`
  - `추천 실행 방식: direct executor`

#### 3. Bug fixes or unclear failures
- Preferred: **`$plan → $ralph`**
- Add **`$ultraqa`** when repeated test/fix cycling is expected
- Use diagnostics first: `lsp_diagnostics`, `find_references`, logs, failing tests
- Suggested wording:
  - `작업 분류: 버그 수정 / RCA`
  - `추천 실행 방식: $plan → $ralph`

#### 4. New features or behavior changes
- Preferred: **`$brainstorming` first**, then **`$plan`** (or `$ralplan` for higher-stakes work), then execution
- Use design-first workflow before editing code
- If the user wants full hands-off delivery, recommend **`$autopilot`**
- Suggested wording:
  - `작업 분류: 기능 추가`
  - `추천 실행 방식: $brainstorming → $plan → $ralph`

#### 5. Large multi-area implementation with strong autonomy requested
- Preferred: **`$autopilot`**
- Best when requirements are sufficiently concrete and the user wants end-to-end execution
- Use when planning, coding, QA, and validation should be driven automatically
- Suggested wording:
  - `작업 분류: 자율 다단계 구현`
  - `추천 실행 방식: $autopilot`

#### 6. Parallelizable independent workstreams
- Preferred: **`$ultrawork`** for in-session parallelism
- Preferred: **`$team` / `omx team`** when tmux workers, longer-running coordination, or worktree isolation are justified
- Use only when tasks are genuinely independent
- Suggested wording:
  - `작업 분류: 병렬 작업`
  - `추천 실행 방식: $ultrawork` or `$team`

#### 7. Long-running or must-finish tasks
- Preferred: **`$ralph`**
- Use when completion must be proven with verification, not just attempted
- End with explicit verification evidence before claiming completion
- Suggested wording:
  - `작업 분류: 완료 보장형 작업`
  - `추천 실행 방식: $ralph`

### Tool Recommendation Rules

- Prefer **local code-intel tools** first for codebase facts:
  - `lsp_diagnostics`
  - `lsp_find_references`
  - `lsp_hover`
  - `ast_grep_search`
  - `ast_grep_replace`
- Prefer **state/memory tools** for long or multi-step work:
  - `state_write`, `state_read`, `state_clear`
  - `notepad_write_*`, `notepad_read`
- Prefer **subagents** when analysis and execution can be separated cleanly
- Prefer **`omx team`** only when pane-based workers or worktree isolation adds real value
- Prefer **tests/build/lint/typecheck** as final proof before saying work is done

### Recommendation Style Rules

- Be decisive: recommend one primary path, not a vague menu dump
- If the user explicitly names a skill/mode, honor it and explain any adjustment briefly
- If the task is ambiguous, recommend the smallest safe workflow that can clarify it
- If a workflow is overkill, say so explicitly
- For future execution-oriented requests, begin the response with the recommendation block before implementation details

### Preferred Korean Lead-In

Use this style by default when the user is asking what to do next:

```md
## 추천
- 작업 분류: ...
- 추천 실행 방식: ...
- 추천 도구: ...
- 추천 이유: ...
- 바로 진행: ...
```
