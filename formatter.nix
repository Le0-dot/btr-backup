{ pkgs, ... }:

pkgs.treefmt.withConfig {
  runtimeInputs = [
    pkgs.nixfmt
    pkgs.ruff
  ];
  settings = {
    on-unmatched = "info";
    tree-root-file = "flake.nix";
    formatter = {
      nixfmt = {
        command = "nixfmt";
        includes = [ "*.nix" ];
      };
      ruff-check = {
        command = "ruff";
        options = [
          "check"
          "--fix"
        ];
        includes = [ "*.py" ];
      };
      ruff-format = {
        command = "ruff";
        options = [ "format" ];
        includes = [ "*.py" ];
      };
    };
  };
}
