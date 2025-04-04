#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2019-present MagicStack Inc. and the EdgeDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Authentication code that is shared between HTTP and binary protocols"""

from edgedb import scram

import base64
import hashlib
import json
import logging

from edb import errors
from edb.server.auth import validate_gel_token

cdef object logger = logging.getLogger('edb.server')


cdef extract_token_from_auth_data(auth_data: bytes):
    header_value = auth_data.decode("ascii")
    scheme, _, payload = header_value.partition(" ")
    return scheme.lower(), payload.strip()


cdef auth_jwt(tenant, prefixed_token: str | None, user: str, dbname: str):
    if not prefixed_token:
        raise errors.AuthenticationError(
            'authentication failed: no authorization data provided')

    key = tenant.server.get_jws_key()
    if err := validate_gel_token(key, prefixed_token, user, dbname, tenant.get_instance_name()):
        raise errors.AuthenticationError(str(err))

    # Ensure it's a valid role, but check after the JWT is validated
    role = tenant.get_roles().get(user)
    if role is None:
        raise errors.AuthenticationError('authentication failed')


cdef scram_get_verifier(tenant, user: str):
    roles = tenant.get_roles()

    rolerec = roles.get(user)
    if rolerec is not None:
        verifier_string = rolerec['password']
        if verifier_string is not None:
            try:
                verifier = scram.parse_verifier(verifier_string)
            except ValueError:
                raise errors.AuthenticationError(
                    f'invalid SCRAM verifier for user {user!r}') from None
            is_mock = False
            return verifier, is_mock

    # To avoid revealing the validity of the submitted user name,
    # generate a mock verifier using a salt derived from the
    # received user name and the cluster mock auth nonce.
    # The same approach is taken by Postgres.
    nonce = tenant.get_instance_data('mock_auth_nonce')
    salt = hashlib.sha256(nonce.encode() + user.encode()).digest()

    verifier = scram.SCRAMVerifier(
        mechanism='SCRAM-SHA-256',
        iterations=scram.DEFAULT_ITERATIONS,
        salt=salt[:scram.DEFAULT_SALT_LENGTH],
        stored_key=b'',
        server_key=b'',
    )
    is_mock = True
    return verifier, is_mock


def scram_verify_password(password: str, verifier: object) -> bool:
    """Check the given password against a verifier.

    Returns True if the password is OK, False otherwise.
    """

    # adapted from edgedb-python's scram.verify_password but made to
    # take a verifier object instead of a string

    bpassword = scram.saslprep(password).encode('utf-8')
    salted_password = scram.get_salted_password(
        bpassword, verifier.salt, verifier.iterations)
    computed_key = scram.get_server_key(salted_password)
    return verifier.server_key == computed_key


cdef parse_basic_auth(auth_payload: str):
    try:
        decoded = base64.b64decode(auth_payload).decode('utf-8')
    except ValueError:
        raise errors.AuthenticationError(
            'authentication failed: malformed authentication') from None
    username, colon, password = decoded.partition(':')
    if colon != ':':
        raise errors.AuthenticationError(
            'authentication failed: malformed authentication')
    return username, password


cdef extract_http_user(scheme, auth_payload, params):
    """Extract the username from an HTTP request.

    Raises an AuthenticationError if something is too malformed.

    Returns the username, along with the password, if appropriate.
    (To avoid needing to parse the packet twice.)
    """

    if scheme == 'basic':
        return parse_basic_auth(auth_payload)
    else:
        # Respect X-EdgeDB-User if present, but otherwise default to 'edgedb'
        if params and b'user' in params:
            username = params[b'user'].decode('ascii')
        else:
            username = 'edgedb'
        return username, None


cdef auth_basic(tenant, username: str, password: str):
    verifier, mock_auth = scram_get_verifier(tenant, username)
    if not scram_verify_password(password, verifier) or mock_auth:
        raise errors.AuthenticationError('authentication failed')


cdef auth_mtls(transport):
    sslobj = transport.get_extra_info('ssl_object')
    if sslobj is None:
        raise errors.AuthenticationError(
            "mTLS authentication is not supported over plaintext transport")
    cert_data = sslobj.getpeercert()
    if not cert_data:  # None or empty dict
        # If --tls-client-ca-file is specified, the SSLContext used here would
        # have done load_verify_locations() in `server/server.py`, and we will
        # have a valid client certificate (non-empty dict) now if one was
        # provided by the client and passed validation; empty dict otherwise.
        # `None` just means the peer didn't send a client certificate.
        raise errors.AuthenticationError(
            "valid client certificate required")
    return cert_data


cdef auth_mtls_with_user(transport, str username):
    cert_data = auth_mtls(transport)
    try:
        for rdn in cert_data["subject"]:
            if rdn[0][0] == 'commonName':
                if rdn[0][1] == username:
                    return
    except Exception as ex:
        raise errors.AuthenticationError(
            "bad client certificate") from ex

    raise errors.AuthenticationError(
        f"Common Name of client certificate doesn't match {username!r}",
    )
