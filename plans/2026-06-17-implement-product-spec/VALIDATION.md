# Validation Record

This file records validation results for each completed work item. Work items must be validated before they are considered done.

## Validation Commands

The following commands are used for validation throughout the project:

| Command | Purpose |
|---------|---------|
| `just check` | Full quality gate |
| `just api` | Start backend server |
| `just web` | Start frontend dev server |
| `just test-unit` | Backend unit tests |
| `just test-property` | Backend property tests |
| `just test-integration` | Backend integration tests |
| `just test-web` | Frontend tests |
| `just architecture-check` | Repository policy checks |
| `just migration-check` | Fresh database provisioning check |
| `just lint` | Linters |
| `just typecheck` | Type checking |
| `just format-check` | Formatting check |

## Validation Checklist (per work item)

For each completed work item, record:

1. **Commands run**: Exact commands executed
2. **Test results**: Pass/fail counts, any failures
3. **Type-check results**: Pass/fail details
4. **Lint results**: Any warnings/errors
5. **API checks**: Any API verification performed
6. **Data-invariant checks**: Any data correctness verification
7. **Manual interaction checks**: Steps performed manually
8. **Browser viewport/screenshots**: Sizes checked, screenshot paths
9. **Regressions considered**: What was checked for regressions
10. **Validation gaps**: What could not be validated

---

## Work Item 1.1: Token System and Global Stylesheet

*Not yet completed.*

## Work Item 1.2: Contributor Documentation Update

*Not yet completed.*

---

*Add new work items above as they are completed.*
