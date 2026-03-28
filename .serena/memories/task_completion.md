# Task completion checklist
When a task is finished:
1. Run affected tests (and broader suite when appropriate).
2. Run frontend build/lint for web changes.
3. Run `py_compile` or equivalent lightweight syntax validation for changed Python files.
4. Use Playwright/browser verification for UI changes when relevant.
5. Read command output before claiming success.
6. Update `tasks/todo.md` review section with what changed and how it was verified.
7. Update `tasks/lessons.md` after user corrections or repeated mistakes.
8. Final reports should include changed files, simplifications made, and remaining risks.
