---
name: dojo-nix-boundaries
description: Rules for working within the dojo project's Nix-based hermetic build environment. Use when encountering build failures, linker errors, missing dependencies, or when setting up the development environment.
license: MIT
metadata:
  scope: dojo
  environment: nix
---

# Dojo Nix Boundaries

1. Always enter the Nix dev shell before running repo commands.
2. Native dependencies come from Nix.
3. Do not install host-level packages to fix repo issues.
4. Do not bypass `just` workflows for routine verification.
5. If a linker or binary error occurs, fix `flake.nix`, not the host machine.
6. CI must mirror local commands.
