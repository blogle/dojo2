---
name: lific-issue-management
description: Manage software-project issues, plans, and project knowledge through Lific exposed by Nexus MCP. Use for creating, triaging, updating, selecting, or closing Lific work; do not apply project-specific conventions unless they are supplied by the active project.
---

# Lific Issue Management

Use Lific through Nexus MCP as the system of record for issue state, execution coordination, and durable lightweight project knowledge. This is a generic skill: project-local instructions, repository documentation, and explicit user direction take precedence. Do not transfer conventions, taxonomy, or workflow rules from one project into another.

## Discover the Nexus tools first

Lific is accessed through Nexus, whose exposed tool names and schemas may change. Before an operation when its exact Nexus tool and arguments are not known in this conversation:

1. Search Nexus for the specific capability.
2. Inspect the returned schema.
3. Call that exact tool with its documented arguments.

Use focused searches such as `lific create issue`, `lific update issue`, `lific issue comments`, `lific dependencies`, `lific plans`, `lific pages`, `lific search`, or `lific bulk update`. Do not assume Lific has an operation just because another tracker does.

Read operations are safe when relevant to the request. Create or modify work only when the user asks for it or the mutation is an obvious, narrow part of the authorized task. Do not cancel, delete, bulk-change, or substantially rewrite unrelated items without explicit authorization.

## Model work deliberately

An issue is a coherent, independently testable outcome—not a vague activity. Its body is the durable specification: context, required behavior, acceptance criteria, constraints, and references. Keep execution history in comments: progress, material discoveries, testing, commits, PRs, blockers, and handoffs. Do not turn the issue body into a development log.

Use structured fields for their actual purpose:

- Status expresses authorization and execution state.
- Priority expresses ordering pressure, not issue type.
- Dependencies express real sequencing constraints.
- Modules express stable product or architectural areas.
- Labels express orthogonal, recurring classification.
- Plans express useful multi-step execution state.
- Pages preserve durable project-operational knowledge that does not belong to one issue.

Do not add metadata merely to make an issue look complete. Discover and reuse the project’s existing module and label taxonomy; do not invent one-off categories.

## Lifecycle defaults

Unless project-local rules say otherwise, treat the statuses this way:

- `backlog`: identified but not yet authorized or adequately specified for implementation.
- `todo`: specified and authorized; an implementation agent can begin without further product clarification.
- `active`: claimed and materially underway.
- `done`: acceptance criteria and the applicable definition of done have been met.
- `cancelled`: intentionally no longer being pursued; retain a short reason when useful.

Move work to `active` when substantial implementation begins; do not leave it silently claimed in `todo`. Do not mark work `done` merely because code, a branch, or a PR exists. Verify the relevant tests, review/merge/deployment state, and any requested user validation.

When selecting agent work, prefer the highest-priority issue that is both `todo` and `workable=true`, then account for real dates and the requested scope. Inspect the full chosen issue and its linked blockers before recommending or starting work. Do not select blocked, unresolved, or cancelled work unless the user explicitly requests it.

## Dependencies, priority, dates

Use `blocks` only when another item genuinely cannot or should not proceed first. Use `relates_to` for meaningful shared context without a hard dependency, and `duplicate` to preserve one canonical specification rather than competing copies. Dependency links should capture the sequencing Lific needs to determine `workable=true`; do not force agents to infer it from prose.

Suggested priority meaning:

- `urgent`: delay is actively harmful or time-critical.
- `high`: should outrank normal work.
- `medium`: normal meaningful work.
- `low`: worthwhile but deliberately later.
- `none`: not prioritized or priority is irrelevant.

When no priority is expressed or clearly implied, use `none`. Add start or target dates only for real scheduling constraints, not guesses.

## Creating a substantive issue

Before filing a plausible duplicate, search Lific using the underlying concept as well as likely title words. If existing work captures the same outcome, update or link it instead of creating a parallel specification. Skip exhaustive duplicate research when the request is clearly unique or the user explicitly directs creation.

Write a ticket another competent developer or agent can execute without reconstructing the conversation. Use this shape when it fits:

```markdown
## Context

Why this matters and what currently happens.

## Scope

- Required behavior or change
- Important edge case or interaction rule

## Acceptance Criteria

- Observable outcome
- Focused automated or manual verification
- Relevant regression check

## Constraints

- Compatibility, architecture, design, or terminology constraints
- Explicit non-goals

## References

- Relevant source paths, URLs, related issues, designs, or evidence
```

Use an outcome-oriented title, such as “Prevent stale due dates after changing goal type,” rather than “Goal bug.” Acceptance criteria must be observable. Resolve product seams that affect UX, data semantics, compatibility, security, or expensive architecture before moving work to `todo`; do not delegate those decisions accidentally to the implementer.

Specify the smallest useful verification set. Capture constraints that prevent expensive mistakes—such as bypassing canonical logic, changing audit semantics, adding unnecessary infrastructure, or diverging from a design system—but do not invent constraints without evidence.

## Plans and pages

Create a Plan only when ordered or nested execution state is useful: large features, migrations, infrastructure work, multi-stage refactors, or work likely to exceed a single agent context. Link independently meaningful plan steps to issues rather than duplicating their specifications. Do not use a Plan for a trivial one-step issue.

Use Pages for durable coordination material: workflow, triage rules, definition of done, runbooks, roadmap, release checklist, or architecture-decision summaries. Prefer a small number of high-value pinned pages. Link source-controlled specifications rather than copying them into Lific, which creates drift.

## Comments and concurrent work

Keep comments concise and durable. At meaningful points, record:

- start context and initial approach;
- material discoveries or a clearly stated blocker;
- completion summary, verification, PR/commit links, and remaining concerns.

If the tool exposes `expected_seq`, a version, or another optimistic-concurrency value, pass the version from the most recent read when modifying a potentially shared issue or page. On conflict, re-read and reconcile before retrying; never overwrite newer human or agent work blindly.

## Triage and completion

When asked to triage, prioritize changes that improve execution clarity: ready backlog items, blocked `todo` items missing dependency links, stale `active` work, duplicates, missing acceptance criteria, obsolete priorities, and completed work left open. Do not reorganize a project merely for aesthetics.

Before closing an issue:

1. Verify its acceptance criteria and relevant checks.
2. Make hidden follow-up work explicit as a separate, linked issue.
3. Add a concise completion or handoff comment when it helps continuity.
4. Set the issue to `done`.

Keep project-specific issue templates, workflow definitions, repository paths, release requirements, labels, and modules in project-local context—not in this skill.
