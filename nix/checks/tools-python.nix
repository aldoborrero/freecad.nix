{ pkgs, ... }:
pkgs.runCommand "tools-python"
  {
    nativeBuildInputs = [
      pkgs.python3
      pkgs.git
      pkgs.patch
      pkgs.ruff
    ];
  }
  ''
    cp -r ${../../tools} tools
    chmod -R u+w tools
    export PYTHONDONTWRITEBYTECODE=1
    ruff check --no-cache tools
    ruff format --check --no-cache tools
    python3 -m unittest discover -s tools -p 'test_*.py' -v
    touch $out
  ''
