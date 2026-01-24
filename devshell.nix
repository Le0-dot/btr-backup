{ pkgs }:

pkgs.mkShell {
  packages = [
    pkgs.uv
    pkgs.ruff
    pkgs.ty
    pkgs.nil

    pkgs.btrfs-progs
  ];
}
