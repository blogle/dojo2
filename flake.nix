{
  description = "dojo bootstrap repository";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, flake-utils, nixpkgs }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        python = pkgs.python312;
        apiPython = python.withPackages (ps: [
          ps.duckdb
          ps.fastapi
          ps.httpx
          ps.itsdangerous
          ps.pydantic
          ps.pydantic-settings
          ps.pytz
          ps.uvicorn
        ]);
        apiSource = pkgs.runCommand "dojo-api-source" { } ''
          mkdir -p "$out/app"
          cp -r ${./api/src}/dojo "$out/app/dojo"
        '';
        apiLauncher = pkgs.writeShellScriptBin "dojo-api" ''
          export PYTHONPATH=${apiSource}/app
          exec ${apiPython}/bin/uvicorn dojo.api.main:app --host 0.0.0.0 --port 8000
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python
            uv
            nodejs_22
            pnpm
            just
            ruff
            duckdb
            mdbook
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
        };

        packages.container = pkgs.dockerTools.buildLayeredImage {
          name = "dojo-api";
          tag = "latest";
          contents = [
            pkgs.bash
            apiPython
            apiSource
            apiLauncher
          ];
          config = {
            Cmd = [ "/bin/dojo-api" ];
            ExposedPorts = {
              "8000/tcp" = { };
            };
          };
        };
      });
}
