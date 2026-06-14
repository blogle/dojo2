# Create Skill Template

Use this template when adding a new repository skill or workflow-specific agent guide under `agents/`.

## When To Add A Skill

Add a skill only when all of the following are true:

- the workflow is recurring or high-error
- the workflow is not already obvious from `CONTRIBUTING.md` and canonical `just` commands
- a self-contained file can explain the task without relying on prior chat context

Do not add a skill just to restate general repository policy.

## Required Skill Contents

Every skill file must explain:

- where the skill lives
- the exact problem the skill solves
- when the skill should be used
- when the skill should not be used
- the canonical `just` commands it invokes
- the authoritative repository documents it references
- the tests or validation used to verify the work
- one or more concrete examples
- non-goals
- how to update or retire the skill

## Required Constraints

- A skill must not assume external conversation context.
- A skill must remain understandable from its files alone.
- A skill must not hide destructive actions.
- A skill must use canonical `just` commands where available.
- A skill must name exact repository paths, commands, and tests instead of saying "follow the usual pattern".

## Suggested File Shape

```text
# <Skill name>

## Purpose
## Use When
## Do Not Use When
## Required Inputs
## Commands
## Validation
## Examples
## Non-Goals
## Maintenance
```
