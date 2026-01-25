{ pkgs }:

pkgs.mkShell {
  packages = [
    pkgs.python313

    pkgs.uv
    pkgs.ruff
    pkgs.ty
    pkgs.nil

    pkgs.btrfs-progs
  ];
}
