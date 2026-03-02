{
  pkgs,
  inputs,
  perSystem,
}:

let
  python = pkgs.python313;
  project = inputs.pyproject.lib.project.loadUVPyproject { projectRoot = ./..; };
  attrs = project.renderers.buildPythonPackage {
    inherit python;
    pythonPackages = python.pkgs // {
      mount = perSystem.self.mount;
    };
  };
in
python.pkgs.buildPythonPackage (attrs // { propagatedBuildInputs = [ pkgs.btrfs-progs ]; })
