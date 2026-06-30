---
name: terminology-lint
description: Use whenever writing user-facing copy in web/, especially labels, headings, badges, modals, and table copy where product terms can drift from SPEC.md. Enforces confirmed wording distinctions with a small literal phrase-ban list.
---

# Terminology lint

`scripts/terms.yaml` contains only wording that has been explicitly confirmed
wrong against `SPEC.md`. It is intentionally small. Do not pad it out from
memory or vibes.

## When to update it

Add an entry only when a wording rule has actually been confirmed.

- include the banned phrase
- include a reason that explains why the wording is wrong

## Enforcement

```bash
python3 .agents/skills/terminology-lint/scripts/check_terminology.py
```

The check is intentionally literal and case-insensitive. It should stay
trustworthy by only flagging real, pre-confirmed mistakes.
