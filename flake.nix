{
  description = "IIP Dev Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        python = pkgs.python314;
        py = python.withPackages (ps: with ps; [
        ]);
      in {
        devShells.default = pkgs.mkShell {
          name = "camara-2026";

          packages = [
            py
          ];

          # Make sure CPython always resolves THIS python
          PYTHONPATH="${py}/${python.sitePackages}";

          shellHook = ''
            echo "[camara-2026] Python: $(python --version)"
            echo "Using Nix-provided scientific stack (no wheel builds)"
          '';
        };
      });
}