# Repository Guidelines

## Project Structure & Module Organization
This repository is currently in bootstrap state (no committed source files yet). Use this layout as code is added:
- `src/`: application code, organized by feature (`src/<feature>/...`).
- `tests/`: automated tests mirroring `src` paths.
- `assets/`: static files, fixtures, and sample inputs.
- `docs/`: architecture notes, plans, and operational docs.
- `scripts/`: local automation for setup, linting, and release tasks.

Prefer feature-first modules over large technical-layer folders, and keep shared utilities in `src/shared/`.

## Build, Test, and Development Commands
No build tooling is committed yet. In the first tooling PR, expose stable command names so contributors have a consistent workflow:
- `npm run dev`: start local development environment.
- `npm run build`: create a production build.
- `npm run test`: run the automated test suite.
- `npm run lint`: run static analysis.
- `npm run format`: apply formatter rules.

If you use another ecosystem, provide equivalent commands (for example via `make dev`, `make test`) and document them in `README.md`.

## Coding Style & Naming Conventions
Use a formatter and linter from day one, and run them before every PR. Baseline conventions:
- Indentation: 2 spaces for YAML/JSON/Markdown; follow language defaults elsewhere.
- Naming: `kebab-case` for files/directories, `camelCase` for functions/variables, `PascalCase` for types/classes.
- Keep functions focused, avoid long files, and prefer explicit imports.

## Testing Guidelines
Every feature and bugfix must include tests in `tests/` (or colocated tests if the stack requires it). Keep test names behavior-oriented, such as `creates_invoice_when_payload_is_valid`.

Target at least 80% line coverage once coverage tooling is configured. Ensure tests are deterministic and runnable locally with a single command.

## Commit & Pull Request Guidelines
Because this repo has no established Git history yet, use Conventional Commits:
- `feat: add claim parsing service`
- `fix: handle empty reimbursement response`
- `docs: update onboarding steps`

PRs should include: concise summary, linked issue (if any), test evidence, and screenshots for UI changes. Keep PRs scoped to one logical change.
