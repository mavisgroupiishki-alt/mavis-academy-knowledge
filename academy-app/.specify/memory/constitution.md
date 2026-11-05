# Mavis Academy Constitution

## Principles

### I. Source-first learning
Every lesson MUST show the instructional content inside Academy from an approved source document. A file title, a folder path, or an external link is not a lesson.

### II. Role-relevant practice
Every learning tile MUST include an in-context knowledge check and a completion state. Manager and expert routes MUST stay separate from the trainee route.

### III. Safe knowledge delivery
Credentials, API keys, passwords, and access instructions MUST never be copied into lessons, browser bundles, logs, or AI context. Server-side access controls MUST use environment variables.

### IV. Reversible, verifiable changes
The course catalogue MUST be declarative, source paths MUST be allow-listed, and affected JavaScript and Python MUST be syntax-checked before publishing.

## Constraints

- Academy is a static browser application served by `server.py`.
- Instructional Markdown comes only from the local Mavis Knowledge repository allow-list.
- Google Drive sources are read-only references; their contents are imported only when safe and needed for a lesson.
- Role passwords are supplied through server environment variables, not source code.

## Working process

Work begins with source mapping, then a learner-visible course design, then implementation and direct route verification.

## Governance

This constitution has priority over implementation choices. An incompatible change requires a version update.

**Version**: 1.0.0 | **Ratified**: 2026-11-05 | **Last Amended**: 2026-11-05
