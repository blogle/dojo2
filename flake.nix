{
  description = "dojo bootstrap repository";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    airship = {
      url = "github:0xnyn/airship/1063ba0002e33b2e19de586f2330b4356e51e8f5";
      flake = false;
    };
  };

  outputs = { self, flake-utils, nixpkgs, airship }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        suppliedBuildSha = builtins.getEnv "DOJO_BUILD_SHA";
        # CI supplies the revision explicitly. "local" keeps flake evaluation and
        # non-deployable local images usable without relying on .git in the image.
        buildSha = if suppliedBuildSha != "" then suppliedBuildSha else "local";
        validBuildSha = buildSha == "local" || builtins.match "[0-9a-f]{40}" buildSha != null;
        python = pkgs.python312;
        apiPython = python.withPackages (ps: [
          ps.duckdb
          ps.fastapi
          ps.httpx
          ps.authlib
          ps.itsdangerous
          ps.pydantic
          ps.pydantic-settings
          ps.pytz
          ps.uvicorn
          ps.tenacity
        ]);
        apiSource = pkgs.runCommand "dojo-api-source" { } ''
          mkdir -p "$out/app"
          cp -r ${./api/src}/dojo "$out/app/dojo"
        '';
        apiLauncher = pkgs.writeShellScriptBin "dojo-api" ''
          export PYTHONPATH=${apiSource}/app
          exec ${apiPython}/bin/uvicorn dojo.api.main:app --host 0.0.0.0 --port 8000
        '';
        migrationLauncher = pkgs.writeShellScriptBin "dojo-migrate" ''
          export PYTHONPATH=${apiSource}/app
          exec ${apiPython}/bin/python -m dojo.migrations "$@"
        '';
         backupLauncher = pkgs.writeShellScriptBin "dojo-backup" ''
           export PYTHONPATH=${apiSource}/app
           exec ${apiPython}/bin/python -m dojo.backup "$@"
         '';
         backupUploadLauncher = pkgs.writeShellScriptBin "dojo-backup-upload" ''
           export PYTHONPATH=${apiSource}/app
           exec ${apiPython}/bin/python -m dojo.drive_uploader "$@"
         '';
        snapshotBackupLauncher = pkgs.writeShellScriptBin "dojo-snapshot-backup" ''
          exec ${pkgs.bash}/bin/bash ${./ops/k8s/snapshot-backup.sh} "$@"
        '';
        backupStatusLauncher = pkgs.writeShellScriptBin "dojo-backup-status" ''
          export PYTHONPATH=${apiSource}/app
          exec ${apiPython}/bin/python -m dojo.backup_status "$@"
        '';
        backupTriggerLauncher = pkgs.writeShellScriptBin "dojo-backup-trigger" ''
          export PYTHONPATH=${apiSource}/app
          exec ${apiPython}/bin/uvicorn dojo.backup_trigger_server:app --host 127.0.0.1 --port 8001
        '';
        airshipLauncher = pkgs.writeShellScriptBin "dojo-airship" ''
          set -euo pipefail

          commit="1063ba0002e33b2e19de586f2330b4356e51e8f5"
          state_dir="''${DOJO_AIRSHIP_STATE_DIR:-$PWD/.airship-state}"
          build_dir="$state_dir/build/$commit"
          source_commit_file="$build_dir/.dojo-airship-source-commit"

          mkdir -p "$state_dir"
          if [[ -L "$HOME/.airship" ]]; then
            :
          elif [[ -e "$HOME/.airship" ]]; then
            if [[ ! -e "$state_dir/history" && -d "$HOME/.airship/history" ]]; then
              cp -a "$HOME/.airship/history" "$state_dir/"
            fi
            legacy_home="$state_dir/legacy-home"
            if [[ ! -e "$legacy_home" ]]; then
              mv "$HOME/.airship" "$legacy_home"
            else
              rm -rf "$HOME/.airship"
            fi
            ln -s "$state_dir" "$HOME/.airship"
          else
            ln -s "$state_dir" "$HOME/.airship"
          fi

          if [[ ! -x "$build_dir/apps/cli/dist/index.js" || ! -f "$source_commit_file" ]]; then
            if [[ -e "$build_dir" ]]; then
              chmod -R u+w "$build_dir" || true
            fi
            rm -rf "$build_dir"
            mkdir -p "$build_dir"
            cp -a ${airship}/. "$build_dir/"
            chmod -R u+w "$build_dir"
            (cd "$build_dir" && ${pkgs.nodejs_22}/bin/node ${pkgs.pnpm}/libexec/pnpm/bin/pnpm.cjs install --frozen-lockfile && ${pkgs.nodejs_22}/bin/node ${pkgs.pnpm}/libexec/pnpm/bin/pnpm.cjs --filter './packages/*' build && ${pkgs.nodejs_22}/bin/node ${pkgs.pnpm}/libexec/pnpm/bin/pnpm.cjs --filter @airshiplabs/cli build)
            printf '%s\n' "$commit" > "$source_commit_file"
          fi

          printf 'dojo-airship source commit: %s\n' "$commit" >&2
          printf 'dojo-airship history: %s\n' "$HOME/.airship/history" >&2
          exec ${pkgs.nodejs_22}/bin/node "$build_dir/apps/cli/dist/index.js" "$@"
        '';
      in
      assert validBuildSha;
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            cypress
            chromium
            python
            uv
            nodejs_22
            pnpm
            airshipLauncher
            just
            ruff
            duckdb
            ffmpeg
            mdbook
            restic
            rclone
            kubectl
            yq-go
            opentofu
            google-cloud-sdk
            git
            pkg-config
            openssl
            libffi
            zlib
            stdenv.cc.cc
          ];
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc
            pkgs.zlib
          ];
          CYPRESS_INSTALL_BINARY = 0;
          DOJO_CYPRESS_APP_DIR = "${pkgs.cypress}/opt/cypress";
          DOJO_E2E_BROWSER = "${pkgs.chromium}/bin/chromium";
          GSETTINGS_SCHEMA_DIR = "${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}/glib-2.0/schemas";
        };

        packages.container = pkgs.dockerTools.buildLayeredImage {
          name = "dojo";
          tag = "latest";
          contents = [
            pkgs.bash
            pkgs.coreutils
            pkgs.cacert
            apiPython
            apiSource
            apiLauncher
            migrationLauncher
            backupLauncher
            backupUploadLauncher
            snapshotBackupLauncher
            backupStatusLauncher
            backupTriggerLauncher
            pkgs.restic
            pkgs.rclone
            pkgs.kubectl
            pkgs.gnused
          ];
          config = {
            Cmd = [ "/bin/dojo-api" ];
            Env = [ "DOJO_BUILD_SHA=${buildSha}" ];
            ExposedPorts = {
              "8000/tcp" = { };
            };
            Labels = {
              "org.opencontainers.image.revision" = buildSha;
            };
          };
        };
      });
}
