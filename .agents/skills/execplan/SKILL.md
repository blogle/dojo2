---
name: execplan
description: Create and execute self-contained, living implementation plans (ExecPlans) for complex coding work. ExecPlans follow the canonical OpenAI ExecPlan discipline but persist their specification, milestones, progress, discoveries, decisions, and retrospective in Lific rather than repository-side plan files. Use before non-trivial multi-file, schema, migration, infrastructure, or refactoring work; do not use for trivial edits.
license: MIT
metadata:
  audience: agents
  workflow: planning
---

# Execution Plans (ExecPlans)

An ExecPlan is a self-contained, living implementation specification that a coding agent can follow to deliver a working feature or system change.

Follow the canonical OpenAI ExecPlan principles from:

https://developers.openai.com/cookbook/articles/codex_exec_plans

This skill adapts that planning discipline to Lific.

Lific is the persistent system of record for ExecPlans. Do not create, maintain, or update repository-side Markdown ExecPlan files unless project-local instructions explicitly override this rule.

Use the companion `lific` skill for the mechanics and semantics of reading and modifying Lific.

## The central rule

An ExecPlan is a planning protocol, not a Markdown file.

For this repository, the persistent representation of an ExecPlan is:

* one anchor Lific issue containing the durable outcome specification;
* one Lific Plan containing milestones and executable steps;
* linked Lific issues for independently meaningful deliverables when useful;
* comments recording progress, discoveries, decisions, evidence, and retrospective material.

Together these objects form the ExecPlan.

Do not create a second mutable representation under `docs/plans`, `plans`, or another repository directory. Two living copies create divergence.

Source-controlled documents remain authoritative for permanent product and architecture knowledge. If an ExecPlan discovers information future contributors must know independent of this execution effort, promote that information into the appropriate repository document, code comment, test, ADR, specification, or runbook.

## When an ExecPlan is required

Use an ExecPlan before beginning work that has meaningful execution complexity, such as:

* changes spanning several subsystems or files;
* schema or data migrations;
* architectural changes;
* significant refactoring;
* infrastructure or deployment changes;
* features requiring coordinated frontend and backend work;
* changes with non-trivial rollback or data-safety concerns;
* work with important unknowns that should be de-risked through prototypes;
* tasks likely to outlive one agent context;
* tasks containing several independently verifiable milestones.

Do not create an ExecPlan for typo fixes, obvious one-file changes, tiny styling adjustments, mechanical dependency bumps, or similarly trivial edits.

When uncertain, prefer an ExecPlan if loss of reasoning or execution state would make a stateless agent meaningfully less likely to complete the task safely.

## Required properties

Every ExecPlan must remain:

* self-contained;
* self-sufficient;
* understandable by a contributor unfamiliar with the repository;
* explicit about purpose and user-visible outcome;
* executable without access to prior conversation context;
* living and updated throughout implementation;
* outcome-focused rather than code-change-focused;
* independently verifiable at meaningful milestones;
* explicit about validation and recovery.

A stateless agent must be able to reconstruct the current implementation state by reading the anchor issue, Lific Plan, relevant linked issues, and execution comments.

Do not rely on conversational memory.

## Persistence model

### Anchor issue

Every ExecPlan must have an anchor issue.

The anchor issue contains the durable contract for the initiative. It should remain relatively stable while implementation history accumulates elsewhere.

The anchor issue should contain, as appropriate:

## Purpose / Big Picture

Explain what becomes possible after the work and how someone can observe that outcome.

## Context and Orientation

Explain the relevant current architecture as if the reader is new to the repository.

Name repository-relative paths, major modules, important functions, APIs, data stores, and services.

Define non-obvious terminology immediately.

## Scope

Describe the behavior and system changes required to achieve the outcome.

## Validation and Acceptance

Describe observable acceptance behavior and the commands, tests, UI flows, API calls, or other checks that prove completion.

## Idempotence and Recovery

Document retry behavior, migration safety, rollback or recovery expectations, and any destructive operations.

## Interfaces and Dependencies

Name important libraries, services, interfaces, functions, types, routes, schemas, or external systems the implementation must use.

## Constraints

Record architecture, compatibility, UX, data-integrity, terminology, design-system, performance, security, or deployment constraints that materially limit implementation choices.

## References

Link relevant repository documentation, designs, external references, issues, commits, PRs, or other evidence.

Do not use the anchor issue as a chronological development log.

### Lific Plan

Every ExecPlan must also have a Lific Plan attached to or associated with the anchor issue.

The Lific Plan replaces the repository-side `Progress` checklist and milestone hierarchy.

Its tree expresses the current executable decomposition.

Top-level steps should normally be meaningful milestones.

Nested steps may represent concrete implementation or validation work.

Each milestone must explain:

* what will exist afterward that does not exist beforehand;
* the implementation area involved;
* how to execute the work;
* how to validate it;
* what evidence demonstrates success.

Milestones must incrementally advance the overall feature and be independently verifiable where practical.

Do not decompose every command or edit into a plan node. Use enough structure to make state and next actions obvious.

### Linked issues

Create or link separate issues only for work that is independently meaningful.

A plan step is a good candidate for a linked issue when it is independently:

* assignable;
* schedulable;
* reviewable;
* blockable;
* prioritizable;
* testable;
* useful to track outside this one plan.

Do not create tickets merely to mirror every subsection of the ExecPlan.

The ExecPlan remains the canonical cross-cutting implementation model. Linked issues add independently meaningful work tracking; they must not become competing mini-specifications.

### Comments

Use comments as the living chronological record.

Prefer clearly recognizable prefixes:

`[Progress]`

Record meaningful execution progress, stopping points, milestone completion, and the immediate next state.

`[Discovery]`

Record surprising implementation facts, unexpected behavior, library behavior, test evidence, architectural discoveries, performance observations, or other findings that materially affect execution.

Use the shape:

Observation: ...

Evidence: ...

Implication: ...

`[Decision]`

Record implementation or design decisions made during execution.

Use the shape:

Decision: ...

Rationale: ...

Alternatives considered: ...

Author/date: ...

`[Retrospective]`

At major milestones and final completion, record outcomes, remaining gaps, lessons learned, and whether the original purpose was achieved.

Important terminal output, test results, logs, or evidence may also be recorded in comments when they materially help a future agent resume the work.

Do not copy large irrelevant transcripts into Lific.

## Creating a new ExecPlan

Before writing code for qualifying work:

1. Read the relevant repository documentation and implementation thoroughly.
2. Search Lific for an existing issue or active Plan covering the same outcome.
3. If one exists, resume or extend it rather than creating a parallel ExecPlan.
4. Identify unresolved product or architectural seams.
5. Resolve material product decisions from authoritative project context or explicit user direction rather than silently delegating them to implementation.
6. Create or identify the anchor issue.
7. Create the Lific Plan and associate it with the anchor issue.
8. Populate the milestone tree sufficiently for another stateless agent to execute it.
9. Add linked implementation issues only where independently useful.
10. Ensure validation, recovery, and observable outcomes are explicit before substantial implementation begins.

Do not create a repository-side ExecPlan file.

## Research before planning

Be thorough before committing to an implementation path.

Read:

* authoritative product specifications;
* architecture documentation;
* design documentation;
* relevant implementation code;
* tests;
* migrations;
* project-local skills and agent instructions;
* related Lific issues and plans.

When a requirement depends on a library or system whose behavior is uncertain, investigate before prescribing the implementation.

For difficult unknowns, create an explicit prototype or proof-of-concept milestone.

A prototype milestone must define:

* what uncertainty it tests;
* the smallest implementation needed to test it;
* the commands or behavior used as evidence;
* the criteria for adopting or discarding the approach.

Do not bury unresolved architectural uncertainty inside a later implementation step.

## Writing milestones

Milestones are narrative implementation units, not administrative buckets.

A good milestone tells the next agent:

* what the system currently does;
* what this milestone changes;
* which files and components are involved;
* the intended implementation;
* exact or sufficiently prescriptive commands;
* expected observable behavior;
* relevant tests;
* what completion means.

Prefer prose explaining why the work is done in a particular order.

Do not leave meaningful design decisions to the implementing agent merely to keep the Plan shorter.

At the same time, do not prescribe incidental syntax when several equivalent implementations satisfy the same proven architecture.

Be prescriptive about semantics and expensive-to-reverse decisions.

## Concrete execution instructions

Plan step descriptions should contain concrete implementation instructions where necessary.

Name repository-relative files and relevant functions, modules, types, routes, tables, schemas, or components.

When commands matter, include:

* expected working directory;
* exact command;
* meaningful expected output or success condition.

For example:

From the repository root run:

```
just test-api
```

Expect the focused API test suite to succeed. The new regression test covering the failure mode must fail before the implementation and pass afterward.

Do not use vague instructions such as:

* update backend;
* fix tests;
* wire frontend;
* make it work;
* verify manually.

## Validation

Validation is mandatory.

An ExecPlan must prove working behavior, not merely compilation or implementation existence.

Prefer the smallest comprehensive validation set that covers:

* focused unit or component tests;
* relevant integration tests;
* migration or persistence checks;
* lint/type/build checks where applicable;
* user-visible or end-to-end behavior when the change affects user interaction.

For UI behavior, require an actual local interactive validation flow where project conventions expect it.

When the user must inspect or interact with the application, reach a locally runnable state first and explicitly record the human validation gate.

Do not declare a human gate passed without the human performing it.

## Incremental progress

Execute milestones sequentially unless the Plan explicitly identifies safe parallel work.

At every meaningful stopping point:

1. update the Lific Plan step state;
2. record new discoveries;
3. record decisions made;
4. update affected issue states;
5. record validation evidence;
6. ensure the next unfinished step is unambiguous.

Do not wait until the end of the task to reconstruct plan state from memory.

The persistent ExecPlan must reflect reality continuously.

## Commits

Commit at coherent implementation checkpoints unless project-local instructions say otherwise.

A commit should normally correspond to an independently understandable piece of working or safely transitional state.

Do not bundle unrelated milestones solely to reduce commit count.

When useful, reference the Lific Plan or issue in the commit message, PR, or completion comment.

## Surprises and discoveries

Unexpected information is first-class plan state.

Examples include:

* an API behaving differently than documented;
* an existing invariant not previously visible;
* migration ordering constraints;
* generated code changing unexpected files;
* a dependency lacking a required capability;
* test behavior revealing hidden coupling;
* performance characteristics affecting architecture;
* an existing bug discovered during implementation.

Record these promptly as `[Discovery]` comments with evidence.

If the discovery permanently affects how the repository should be understood, also update the appropriate repository documentation or tests.

Lific preserves the history of how the discovery affected this ExecPlan; repository documentation preserves the resulting durable truth.

## Decisions

Every material change in implementation direction must be recorded.

A decision is material when a future contributor could reasonably ask:

“Why was it done this way instead of the obvious alternative?”

Record those decisions as `[Decision]` comments.

Do not rely on commit history alone to explain architectural intent.

If the decision is a durable architecture rule that applies beyond this implementation effort, also promote it to the repository's canonical architectural documentation or ADR mechanism.

## Resuming an ExecPlan

A stateless agent resuming work must:

1. read the anchor issue in full;
2. rehydrate the entire Lific Plan tree;
3. inspect linked issues relevant to unfinished steps;
4. read material `[Decision]`, `[Discovery]`, `[Progress]`, and `[Retrospective]` comments;
5. inspect the current repository state;
6. verify that completed steps still correspond to repository reality;
7. identify the first unfinished executable milestone;
8. continue without asking the user merely what comes next.

Ask the user only when an actual unresolved product decision, missing credential, permission gate, destructive action, human-validation requirement, or other necessary external input blocks progress.

Do not ask for routine “next steps.”

## Completion

Before completing an ExecPlan:

1. verify every acceptance condition;
2. run the required test and validation suite;
3. complete any required human validation;
4. ensure no hidden unfinished work remains inside comments;
5. create linked follow-up issues for independently meaningful deferred work;
6. update permanent repository documentation where discoveries or decisions created durable knowledge;
7. record a final `[Retrospective]`;
8. mark all completed Plan steps appropriately;
9. close the relevant implementation issues;
10. close the anchor issue according to project workflow;
11. mark/archive the Lific Plan according to project workflow.

The final retrospective must compare the outcome to the original purpose and capture:

* what was delivered;
* what changed from the original plan;
* significant discoveries;
* remaining gaps;
* follow-up work;
* lessons useful to future implementation.

## Repository-side plans

Do not create new repository-side ExecPlan files.

Do not maintain a repository Markdown file in parallel with a Lific ExecPlan.

If an existing repository-side ExecPlan is being migrated:

* preserve its active implementation state in a Lific anchor issue and Plan;
* preserve important decisions and discoveries as Lific comments;
* preserve its final retrospective when completed;
* promote permanent architecture/product knowledge into canonical repository documentation;
* retain the old file only until migration is verified;
* then remove it from the current tree.

Git history remains the historical copy of removed plan files.

For completed historical plans, do not mechanically reproduce every checkbox and command. Preserve valuable purpose, major milestones, decisions, discoveries, outcome, and references, then archive the Lific representation.

For obsolete or superseded plans with no enduring execution value, promote any durable knowledge and allow Git history to remain the historical record.

## Relationship to repository documentation

ExecPlans do not replace product specifications, architecture documentation, design systems, ADRs, runbooks, or tests.

Use this rule:

Repository documentation describes enduring truth.

Lific issues describe tracked outcomes.

Lific relationships describe dependencies.

Lific Plans describe execution structure.

Lific comments describe execution history and reasoning.

ExecPlan is the discipline binding those Lific objects into a resumable implementation process.

## Non-negotiable standard

A single stateless agent must be able to start with:

* the current repository;
* the anchor Lific issue;
* the Lific Plan;
* relevant linked issues;
* the execution comments;

and complete the remaining work without access to the original conversation.

If it cannot, the ExecPlan is incomplete.

