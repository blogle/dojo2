# ExecPlan Skill

Use this skill for complex implementation work in `dojo`.

An ExecPlan is a self-contained, living implementation plan. It must contain enough context, concrete steps, validation instructions, and decision history for a stateless coding agent or novice human to complete the task using only the current repository and the ExecPlan file.

ExecPlans are not lightweight TODO lists. They are executable specifications for non-trivial work.

## When to use an ExecPlan

Create or update an ExecPlan before starting work when the task involves any of the following:

- multi-file feature work
- schema, database, or migration work
- significant refactoring
- changes to public API behavior
- changes to persistent data or import logic
- changes to Nix, direnv, CI, container, or developer tooling
- changes to architecture or product behavior
- work expected to span more than one focused coding session
- work where another agent may need to resume from partial progress

An ExecPlan is usually unnecessary for typo fixes, tiny documentation edits, formatting-only changes, or isolated one-line fixes.

## Where ExecPlans live

Store task-specific ExecPlans in:

    plans/

Name plans like:

    plans/YYYY-MM-DD-short-task-name.md

If `plans/` does not exist, create it with a short `plans/README.md` explaining that these are task-scoped living implementation plans.

Do not create broad prompt libraries or generic workflow directories. Keep this repository's permanent agent guidance small.

## How to author an ExecPlan

An ExecPlan must be self-contained. Do not assume the reader remembers previous conversations, previous plans, or unstated repository conventions. Repeat any assumption the task depends on.

Start by reading the relevant repository files. At minimum, check:

    AGENTS.md
    SPEC.md
    ARCHITECTURE.md
    DECISIONS.md
    CHANGELOG.md
    README.md

Then inspect the files directly involved in the task.

The ExecPlan must explain what the user or developer can do after the change that they could not do before. It must describe how to observe the behavior working.

Prefer prose over long checklists. The `Progress` section is the exception and must use checkboxes.

Do not outsource important decisions to the reader. Resolve ambiguity in the plan and explain the rationale. If the ambiguity is genuinely product-level and cannot safely be resolved, record the question explicitly and stop before implementation.

## How to execute an ExecPlan

When implementing from an ExecPlan, keep the plan current as work proceeds.

At every meaningful stopping point:

- update `Progress`
- record unexpected findings in `Surprises & Discoveries`
- record implementation decisions in `Decision Log`
- update validation status
- update docs and changelog if behavior or architecture changed

Do not ask for next steps when the next milestone is already specified. Proceed through the plan.

If reality diverges from the plan, revise the plan first, record why, then continue.

## Required ExecPlan sections

Every ExecPlan must contain these sections, in this order:

    # <Short action-oriented title>

    This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current as work proceeds.

    ## Purpose / Big Picture

    Explain why the work matters from a user or developer perspective. Describe the behavior that will exist after the change and how to observe it.

    ## Progress

    Use checkboxes with timestamps. This section must always reflect the actual current state.

    Example:

    - [x] 2026-06-10 14:30Z — Inspected current API health endpoint structure.
    - [ ] Add failing tests for the new behavior.
    - [ ] Implement the behavior.
    - [ ] Run validation commands.

    ## Surprises & Discoveries

    Record unexpected facts found during implementation.

    Use this shape:

    - Observation: ...
      Evidence: ...

    Examples of useful discoveries include failing assumptions, library behavior, Nix/linker issues, CI differences, test-order sensitivity, or hidden coupling.

    ## Decision Log

    Record decisions made while executing the plan.

    Use this shape:

    - Decision: ...
      Rationale: ...
      Date/Author: ...

    If a decision is durable architecture or product policy, also append it to `DECISIONS.md`.

    ## Outcomes & Retrospective

    Summarize results at completion or major milestones. Compare the final state against the original purpose. Note remaining risks or follow-up work.

    ## Context and Orientation

    Explain the relevant current repository state as if the reader is new to the project.

    Name repository-relative paths explicitly. Define any non-obvious term the plan uses. Do not say "as discussed previously" or rely on prior chat context.

    ## Plan of Work

    Describe the implementation sequence in prose. For each step, name the files and modules to change and what kind of change is expected.

    The plan should be concrete enough to execute but not so overfit that it prevents simpler correct implementations.

    ## Concrete Steps

    State exact commands to run and where to run them.

    For `dojo`, routine commands should generally be run from the repository root through `just`, inside the Nix dev shell loaded by direnv.

    Include expected output or success criteria when useful.

    Example:

        just test-api

    Expected result:

        pytest exits 0

    ## Validation and Acceptance

    Validation is mandatory.

    State how to prove the change works. Include tests, commands, and observable behavior.

    Prefer behavior-based acceptance criteria over implementation-only criteria.

    Good:

        Starting the API and requesting GET /api/app/status returns HTTP 200 with app = dojo.

    Bad:

        Added a status function.

    If a new test is part of the change, explain what would fail before the change and pass after it.

    ## Idempotence and Recovery

    Explain whether steps can be safely repeated. For risky operations, explain rollback or retry behavior.

    For Dojo, destructive commands must not remove source files, lockfiles, docs, or user data.

    ## Interfaces and Dependencies

    Name libraries, modules, endpoints, commands, environment variables, or public interfaces that must exist after the change.

    Be explicit about paths and names.

    ## Artifacts and Notes

    Include concise evidence snippets, terminal output, or small excerpts that prove important points.

    Do not paste large generated files.

## Dojo-specific rules

Do not bypass Nix for native or compiled dependencies. If a binary, linker, OpenSSL, libffi, DuckDB, Python, Node, or package-manager issue appears, fix the Nix flake or project config rather than relying on host-installed tools.

Use `just` commands for routine work. If a needed command does not exist, add or update the `justfile` and document it.

Keep documentation synchronized. Update:

    ARCHITECTURE.md

when current system structure changes.

Update:

    DECISIONS.md

when a durable technical decision is made.

Update:

    SPEC.md

when scope or acceptance criteria change.

Update:

    CHANGELOG.md

for meaningful user-visible or developer-significant changes.

Do not create ADR or RFC directories.

Do not add large speculative prompt or skill libraries.

## Completion report

When finishing work from an ExecPlan, report:

- what changed
- which files changed
- which docs changed
- which commands were run
- which commands passed
- which commands failed or were skipped, with reasons
- remaining risks or follow-up work
