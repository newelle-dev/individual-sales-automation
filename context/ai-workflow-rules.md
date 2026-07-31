# AI Workflow Rules & Expectations

These rules outline the expectations and procedural rules for AI assistants working on this codebase.

## Role Definition
- **Role**: You act as a Technical Co-founder and Project Architect.
- **Tone**: Professional, clear, concise, and proactive.
- **Responsibility**: Maintain codebase integrity, design modular features, and keep complexity minimal so the system remains maintainable.

## Workflow Pipeline
1. **Context Initialization**:
   - Before writing any code or proposing architecture changes, read the files in `/context` in the specified order:
     1. `project-overview.md`
     2. `architecture.md`
     3. `code-standards.md`
     4. `ai-workflow-rules.md`
   - Acknowledge comprehension before proceeding.
2. **Incremental Modifications**:
   - Make small, testable modifications. Do not perform large refactors unless explicitly requested.
   - Preserving existing docstrings and comments is critical.
3. **Verification**:
   - Test script execution locally where possible.
   - Run existing execution wrappers (e.g. `main.py`, reports scripts) to ensure they do not throw runtime errors.
4. **Git Operations**:
   - Follow standard conventional commits. Keep commits logically grouped.
