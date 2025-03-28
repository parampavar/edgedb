.. _ref_cli_gel_instance_reset_auth:


===========================
gel instance reset-password
===========================

Reset password for a user in the |Gel| instance.

.. cli:synopsis::

     gel instance reset-password [<options>] <name>


Description
===========

:gelcmd:`instance reset-password` is a terminal command for resetting
or updating the password for a user of a |Gel| instance.

.. note::

    The :gelcmd:`instance reset-password` command is not intended for use with
    self-hosted instances.


Options
=======

:cli:synopsis:`<name>`
    The name of the |Gel| instance.

:cli:synopsis:`--user=<user>`
    User to change password for. Defaults to the user in the
    credentials file.

:cli:synopsis:`--password`
    Read the password from the terminal rather than generating a new one.

:cli:synopsis:`--password-from-stdin`
    Read the password from stdin rather than generating a new one.

:cli:synopsis:`--save-credentials`
    Save new user and password into a credentials file. By default
    credentials file is updated only if user name matches.

:cli:synopsis:`--no-save-credentials`
    Do not save generated password into a credentials file even if
    user name matches.

:cli:synopsis:`--quiet`
    Do not print any messages, only indicate success by exit status.
