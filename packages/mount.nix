{ pkgs }:

pkgs.python3Packages.buildPythonPackage rec {
  pname = "mount";
  version = "1.0.0";
  pyproject = true;
  build-system = [ pkgs.python3Packages.poetry-core ];

  src = pkgs.fetchPypi {
    inherit pname version;
    sha256 = "sha256-RRDq9CgqljSs6ZgnBdp8cIV9Gwn3P1iRGPWgxkjnHs4=";
  };

  # ctypes.util.find_library("c") returns None on NixOS because ldconfig is not
  # in the standard search path. Patch the module to use the absolute glibc path.
  postPatch = ''
    substituteInPlace mount/core.py \
      --replace-fail 'find_library("c")' '"${pkgs.glibc}/lib/libc.so.6"'
  '';
}
