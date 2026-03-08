{ flake, ... }:
{
  lib,
  config,
  pkgs,
  ...
}:

let
  cfg = config.services.btr-backup;

  mkOptFlag = flag: value: lib.optionalString (value != null) "${flag} ${value}";
  mkListFlag = flag: values: lib.concatMapStringsSep " " (value: "${flag} ${value}") values;

  mkSnapshotService =
    {
      name,
      device,
      chdir,
      include,
      exclude,
    }:
    {
      "${name}-snapshot" = {
        description = "btr-backup ${name}: check and snapshot";
        serviceConfig.Type = "oneshot";
        after = [ "local-fs.target" ];
        requires = [ "local-fs.target" ];
        path = [ cfg.package ];
        script = ''
          btr-backup -v --dev ${device} ${mkOptFlag "--chdir" chdir} check ${mkListFlag "--include" include} ${mkListFlag "--exclude" exclude}
          btr-backup -v --dev ${device} ${mkOptFlag "--chdir" chdir} snapshot ${mkListFlag "--include" include} ${mkListFlag "--exclude" exclude}
        '';
      };
    };

  mkUploadService =
    {
      name,
      device,
      chdir,
      destinationDevice,
      destinationChdir,
      include,
      exclude,
    }:
    {
      "${name}-upload" = {
        description = "btr-backup ${name}: check and upload";
        serviceConfig.Type = "oneshot";
        after = [ "local-fs.target" ];
        requires = [ "local-fs.target" ];
        path = [
          cfg.package
          pkgs.btrfs-progs
        ];
        script = ''
          btr-backup -v --dev ${device} ${mkOptFlag "--chdir" chdir} check ${mkListFlag "--include" include} ${mkListFlag "--exclude" exclude}
          btr-backup -v --dev ${destinationDevice} ${mkOptFlag "--chdir" destinationChdir} check
          btr-backup -v --dev ${device} ${mkOptFlag "--chdir" chdir} upload ${mkListFlag "--include" include} ${mkListFlag "--exclude" exclude} --dest-dev ${destinationDevice} ${mkOptFlag "--dest-chdir" destinationChdir}
        '';
      };
    };

  mkRemoveService =
    {
      name,
      device,
      chdir,
      include,
      exclude,
      keepLatest,
    }:
    {
      "${name}-remove" = {
        description = "btr-backup ${name}: check and remove";
        serviceConfig.Type = "oneshot";
        after = [ "local-fs.target" ];
        requires = [ "local-fs.target" ];
        path = [ cfg.package ];
        script = ''
          btr-backup -v --dev ${device} ${mkOptFlag "--chdir" chdir} check ${mkListFlag "--include" include} ${mkListFlag "--exclude" exclude}
          btr-backup -v --dev ${device} ${mkOptFlag "--chdir" chdir} remove ${mkListFlag "--include" include} ${mkListFlag "--exclude" exclude} --keep-latest ${toString keepLatest}
        '';
      };
    };

  mkServices =
    name: instanceCfg:
    lib.optionalAttrs instanceCfg.snapshot.enable (mkSnapshotService {
      inherit name;
      inherit (instanceCfg)
        device
        chdir
        include
        exclude
        ;
    })
    // lib.optionalAttrs instanceCfg.upload.enable (mkUploadService {
      inherit name;
      inherit (instanceCfg)
        device
        chdir
        include
        exclude
        ;
      inherit (instanceCfg.upload) destinationDevice destinationChdir;
    })
    // lib.optionalAttrs instanceCfg.remove.enable (mkRemoveService {
      inherit name;
      inherit (instanceCfg)
        device
        chdir
        include
        exclude
        ;
      inherit (instanceCfg.remove) keepLatest;
    });

  mkTimer =
    {
      name,
      type,
      onCalendar,
    }:
    {
      "${name}-${type}" = {
        description = "btr-backup ${name}: ${type} timer";
        wantedBy = [ "timers.target" ];
        timerConfig = {
          OnCalendar = onCalendar;
          Persistent = true;
        };
      };
    };

  mkTimers =
    name: instanceCfg:
    lib.optionalAttrs instanceCfg.snapshot.enable (mkTimer {
      inherit name;
      inherit (instanceCfg.snapshot) onCalendar;
      type = "snapshot";
    })
    // lib.optionalAttrs instanceCfg.upload.enable (mkTimer {
      inherit name;
      inherit (instanceCfg.upload) onCalendar;
      type = "upload";
    })
    // lib.optionalAttrs instanceCfg.remove.enable (mkTimer {
      inherit name;
      inherit (instanceCfg.remove) onCalendar;
      type = "remove";
    });
in
{
  options.services.btr-backup = {
    enable = lib.mkEnableOption "btr-backup service";

    package = lib.mkOption {
      type = lib.types.package;
      default = flake.packages.${pkgs.system}.default;
      defaultText = lib.literalExpression "btr-backup.packages.\${pkgs.system}.default";
      description = "The btr-backup package to use.";
    };

    config = lib.mkOption {
      type = lib.types.attrsOf (
        lib.types.submodule {
          options = {
            enable = lib.mkEnableOption "btr-backup instance";

            device = lib.mkOption {
              type = lib.types.path;
              description = "Block device containing the source Btrfs filesystem (passed as --dev).";
              example = "/dev/sda1";
            };

            chdir = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = ''
                Subdirectory on the mounted device that contains the logical backup
                directories (passed as --chdir). Defaults to the root of the device.
              '';
              example = "backups";
            };

            include = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = [ ];
              description = ''
                Subvolume directories to include. Mutually exclusive with exclude.
              '';
            };

            exclude = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = [ ];
              description = ''
                Subvolume directories to exclude. Mutually exclusive with include.
              '';
            };

            snapshot = {
              enable = lib.mkEnableOption "btr-backup snapshot job";

              onCalendar = lib.mkOption {
                type = lib.types.str;
                description = ''
                  Systemd OnCalendar expression defining how often this job runs.
                  See systemd.time(7) for the syntax.
                '';
                example = "weekly";
              };
            };

            upload = {
              enable = lib.mkEnableOption "btr-backup upload job";

              onCalendar = lib.mkOption {
                type = lib.types.str;
                description = ''
                  Systemd OnCalendar expression defining how often this job runs.
                  See systemd.time(7) for the syntax.
                '';
                example = "weekly";
              };

              destinationDevice = lib.mkOption {
                type = lib.types.path;
                description = "Block device of the destination Btrfs filesystem (passed as --dest-dev).";
                example = "/dev/sdb1";
              };

              destinationChdir = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = ''
                  Subdirectory on the destination device where snapshots will be stored (passed as --dest-chdir).
                '';
                example = "backups";
              };
            };

            remove = {
              enable = lib.mkEnableOption "btr-backup remove job";

              onCalendar = lib.mkOption {
                type = lib.types.str;
                description = ''
                  Systemd OnCalendar expression defining how often this job runs.
                  See systemd.time(7) for the syntax.
                '';
                example = "weekly";
              };

              keepLatest = lib.mkOption {
                type = lib.types.ints.positive;
                description = "Number of most-recent snapshots to keep per subvolume (passed as --keep-latest).";
                example = 7;
              };
            };
          };
        }
      );
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ cfg.package ];

    systemd.services = lib.mkMerge (lib.attrsets.mapAttrsToList mkServices cfg.config);
    systemd.timers = lib.mkMerge (lib.attrsets.mapAttrsToList mkTimers cfg.config);
  };
}
