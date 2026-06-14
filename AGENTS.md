# dojo

dojo is a local-first personal finance repository with a FastAPI API in `api/`, a Vue 3 frontend in `web/`, and repository-wide checks routed through the root `justfile`.

## First Commands

- `just setup`
- `just check`
- `just architecture-check`

## Authoritative Documents

- Overview: `README.md`
- Development workflow: `CONTRIBUTING.md`
- Product behavior: `SPEC.md`
- Current implementation: `ARCHITECTURE.md`
- Durable technical tradeoffs: `DECISIONS.md`

## Update Guide

| Change type | Update |
| --- | --- |
| Product behavior or acceptance criteria | `SPEC.md` |
| Runtime structure, persistence model, SQL organization, testing architecture | `ARCHITECTURE.md` |
| Durable technical decision or tradeoff | `DECISIONS.md` |
| Workflow, commands, repository policy guidance | `CONTRIBUTING.md` |
| Meaningful shipped or architectural change | `CHANGELOG.md` |

Agents must use canonical `just` commands where they exist. Repository checks are authoritative.
