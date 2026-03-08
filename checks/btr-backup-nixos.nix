{
  pkgs,
  flake,
  pname,
  ...
}:

pkgs.testers.nixosTest {
  name = pname;

  nodes.machine =
    { ... }:
    {
      imports = [ flake.nixosModules.btr-backup ];

      services.btr-backup = {
        enable = true;
        config.myBackup = {
          enable = true;

          device = "/dev/sda1";
          chdir = "data";
          include = [
            "home"
            "srv"
          ];

          snapshot = {
            enable = true;
            onCalendar = "daily";
          };

          upload = {
            enable = true;
            onCalendar = "weekly";
            destinationDevice = "/dev/sdb1";
            destinationChdir = "backups";
          };

          remove = {
            enable = true;
            onCalendar = "monthly";
            keepLatest = 30;
          };
        };
      };
    };

  testScript = ''
    config = "myBackup"

    def read_service_script(service_name):
        exec_start = machine.succeed(f"systemctl show {service_name} -P ExecStart")
        argv = exec_start.split(";")[1].strip()

        assert argv.startswith("argv[]="), argv
        script_path = argv.removeprefix("argv[]=")
        return machine.succeed(f"cat {script_path}")

    # serives and timers exists

    machine.wait_for_unit("multi-user.target")

    for type in ["snapshot", "upload", "remove"]:
        machine.succeed(f"systemctl show {config}-{type}.service")
        assert machine.succeed(f"systemctl is-enabled {config}-{type}.timer").strip() == "enabled"

    # snapshot service

    snapshot_script = read_service_script(f"{config}-snapshot.service").splitlines()
    check, snapshot = [line for line in snapshot_script if line.startswith("btr-backup")]

    assert "--dev /dev/sda1" in check, "snapshot: missing --dev"
    assert "--chdir data" in check, "snapshot: missing --chdir"
    assert "--include home" in check, "snapshot: missing --include"
    assert "--include srv" in check, "snapshot: missing --include"
    assert "check" in check, "snapshot: missing 'check' subcommand"

    assert "--dev /dev/sda1" in snapshot, "snapshot: missing --dev"
    assert "--chdir data" in snapshot, "snapshot: missing --chdir"
    assert "--include home" in snapshot, "snapshot: missing --include"
    assert "--include srv" in snapshot, "snapshot: missing --include"
    assert "snapshot" in snapshot, "snapshot: missing 'snapshot' subcommand"

    # snapshot timer 

    snapshot_timer = machine.succeed(f"systemctl cat {config}-snapshot.timer")
    assert "OnCalendar=daily" in snapshot_timer, "snapshot timer: missing OnCalendar"

    # upload service 

    upload_script = read_service_script(f"{config}-upload.service").splitlines()
    check, check_dest, upload = [line for line in upload_script if line.startswith("btr-backup")]

    assert "--dev /dev/sda1" in check, "upload: missing --dev"
    assert "--chdir data" in check, "upload: missing --chdir"
    assert "--include home" in check, "upload: missing --include"
    assert "--include srv" in check, "upload: missing --include"
    assert "check" in check, "upload: missing 'check' subcommand"

    assert "--dev /dev/sdb1" in check_dest, "upload: missing --dev"
    assert "--chdir backups" in check_dest, "upload: missing --chdir"
    assert "check" in check_dest, "upload: missing 'check' subcommand"

    assert "--dev /dev/sda1" in upload, "upload: missing --dev"
    assert "--chdir data" in upload, "upload: missing --chdir"
    assert "--include home" in upload, "upload: missing --include"
    assert "--include srv" in upload, "upload: missing --include"
    assert "--dest-dev /dev/sdb1" in upload, "upload: missing --dest-dev"
    assert "--dest-chdir backups" in upload, "upload: missing --dest-chdir"
    assert "upload" in upload, "upload: missing 'upload' subcommand"

    # upload timer 

    upload_timer = machine.succeed(f"systemctl cat {config}-upload.timer")
    assert "OnCalendar=weekly" in upload_timer, "upload timer: missing OnCalendar"

    # --- remove service script contains expected options ---

    remove_script = read_service_script(f"{config}-remove.service").splitlines()
    check, remove = [line for line in remove_script if line.startswith("btr-backup")]

    assert "--dev /dev/sda1" in check, "upload: missing --dev"
    assert "--chdir data" in check, "upload: missing --chdir"
    assert "--include home" in check, "upload: missing --include"
    assert "--include srv" in check, "upload: missing --include"
    assert "check" in check, "upload: missing 'check' subcommand"

    assert "--dev /dev/sda1" in remove, "upload: missing --dev"
    assert "--chdir data" in remove, "upload: missing --chdir"
    assert "--include home" in remove, "upload: missing --include"
    assert "--include srv" in remove, "upload: missing --include"
    assert "--keep-latest 30" in remove, "upload: missing --keep-latest"
    assert "remove" in remove, "upload: missing 'remove' subcommand"

    # remove timer 

    remove_timer = machine.succeed(f"systemctl cat {config}-remove.timer")
    assert "OnCalendar=monthly" in remove_timer, "remove timer: missing OnCalendar"

    # btr-backup in PATH

    machine.succeed("which btr-backup")
    machine.succeed("btr-backup --help")
  '';
}
