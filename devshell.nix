{ pkgs }:

pkgs.mkShell {
  packages = [
    pkgs.git
    pkgs.python313
    pkgs.direnv

    pkgs.uv
    pkgs.ruff
    pkgs.ty
    pkgs.nil

    pkgs.btrfs-progs
  ];
  shellHook = ''
    eval "$(direnv hook $SHELL)"
  '';
}
