.. _ref_intro_cli:

.. _ref_admin_install:

=======
The CLI
=======

The |gelcmd| command line tool is an integral part of the developer workflow
of building with Gel. Below are instructions for installing it.

Installation
------------

To get started with Gel, the first step is install the |gelcmd| CLI.

**Linux or macOS**

.. code-block:: bash

    $ curl --proto '=https' --tlsv1.2 -sSf https://www.geldata.com/sh | sh

**Windows Powershell**

.. note::

    Gel on Windows requires WSL 2 because the Gel server runs on Linux.

.. code-block:: powershell

    PS> iwr https://www.geldata.com/ps1 -useb | iex

Follow the prompts on screen to complete the installation. The script will
download the |gelcmd| command built for your OS and add a path to it to your
shell environment. Then test the installation:

.. code-block:: bash

    $ gel --version
    Gel CLI x.x+abcdefg

.. note::

  If you encounter a ``command not found`` error, you may need to open a fresh
  shell window.


See ``help`` commands
---------------------

The entire CLI is self-documenting. Once it's installed, run :gelcmd:`--help`
to see a breakdown of all the commands and options.

.. code-block:: bash

  $ gel --help
  Usage: gel [OPTIONS] [COMMAND]

  Commands:
    <list of commands>

  Options:
    <list of options>

  Connection Options (gel --help-connect to see full list):
    <list of connection options>

  Cloud Connection Options:
    <list of cloud connection options>

The majority of CLI commands perform some action against a *particular* Gel
instance. As such, there are a standard set of flags that are used to specify
*which instance* should be the target of the command, plus additional
information like TLS certificates. The following command documents these flags.

.. code-block:: bash

  $ gel --help-connect
  Connection Options (full list):

    -I, --instance <INSTANCE>
            Instance name (use `gel instance list` to list local, remote and
            Cloud instances available to you)

        --dsn <DSN>
            DSN for Gel to connect to (overrides all other options except
            password)

        --credentials-file <CREDENTIALS_FILE>
            Path to JSON file to read credentials from

    -H, --host <HOST>
            Gel instance host

    -P, --port <PORT>
            Port to connect to Gel

        --unix-path <UNIX_PATH>
            A path to a Unix socket for Gel connection

            When the supplied path is a directory, the actual path will be
            computed using the `--port` and `--admin` parameters.
    ...

If you ever want to see documentation for a particular command (
:gelcmd:`migration create`) or group of commands (:gelcmd:`instance`),
just append the ``--help`` flag.

.. code-block:: bash

  $ gel instance --help
  Manage local Gel instances

  Usage: gel instance <COMMAND>

  Commands:
    create          Initialize a new Gel instance
    list            Show all instances
    status          Show status of an instance
    start           Start an instance
    stop            Stop an instance
    ...

Upgrade the CLI
---------------

To upgrade to the latest version:

.. code-block:: bash

  $ gel cli upgrade
