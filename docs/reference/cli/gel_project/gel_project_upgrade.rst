.. _ref_cli_gel_project_upgrade:


===================
gel project upgrade
===================

Upgrade |Gel| instance used for the current project

.. cli:synopsis::

    gel project upgrade [<options>]


Description
===========

This command has two modes of operation.

1) Upgrade instance to a version specified in :ref:`ref_reference_gel_toml`.
   This happens when the command is invoked without any explicit target
   version.
2) Update |gel.toml| to a new version and upgrade the instance.
   Which happens when one of the options for providing the target
   version is used.

In all cases your data is preserved and converted using dump/restore
mechanism. This might fail if lower version is specified (for example
if upgrading from nightly to the stable version).

.. note::

    The :gelcmd:`project upgrade` command is not intended for use with
    self-hosted instances.


Options
=======

:cli:synopsis:`--force`
    Force upgrade process even if there is no new version.

:cli:synopsis:`--to-latest`
    Upgrade to a latest stable version.

:cli:synopsis:`--to-nightly`
    Upgrade to a latest nightly version.

:cli:synopsis:`--to-version=<version>`
    Upgrade to a specified major version.

:cli:synopsis:`--project-dir=<project-dir>`
    The project directory can be specified explicitly. Defaults to the
    current directory.

:cli:synopsis:`-v, --verbose`
    Verbose output.
