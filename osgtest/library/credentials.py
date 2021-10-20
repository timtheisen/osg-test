# credentials.py
# Library for dealing with credentials
import base64
import json
import os
import pwd
import time
from urllib import request

from . import core, files


# Headers so that heroku doesn't block us
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko)' +
                         'Chrome/35.0.1916.47 Safari/537.36',
           'Content-Type': 'application/json'}


def download_demo_scitoken(scope: str, subject='osg-test', audience='ANY') -> bytes:
    """Request a token with 'scope' from the demo SciTokens issuer
    """

    payload_dict = {'aud': audience,
                    'ver': 'scitokens:2.0',
                    'scope': scope,
                    'exp': int(time.time() + 3600),
                    'sub': subject}
    payload = json.dumps({'payload': payload_dict,
                          'algorithm': 'ES256'}).encode()
    req = request.Request('https://demo.scitokens.org/issue',
                          data=payload,
                          headers=HEADERS)
    try:
        return request.urlopen(req).read()
    except Exception:
        core.log_message("Error requesting scitoken\n"
                         f"    URL: {req.full_url}\n"
                         f"    Headers: {req.headers}\n"
                         f"    Payload: {req.data}\n")
        raise


def parse_scitoken(token_string: str):
    """Parse a scitoken string and return the header, payload, and signature
    :param token_string: A scitoken as 3 '.'-separated base64 strings
    :return: header (dict), payload (dict), signature (str)
    :raises: ValueError if there is an error decoding the token
    """
    def prettytime(attr):
        return time.strftime("%F %T %z", time.localtime(int(payload[attr])))
    try:
        # b64decode errors if there's not enough padding; OTOH, no harm in too much padding
        header_b64, payload_b64, signature_b64 = [x + "==" for x in token_string.split(".")]
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        signature = base64.urlsafe_b64decode(signature_b64)
        payload['exp'] = prettytime('exp')
        if 'nbf' in payload:
            payload['nbf'] = prettytime('nbf')
        if 'iat' in payload:
            payload['iat'] = prettytime('iat')

        return header, payload, signature
    except (AttributeError, TypeError, ValueError, json.JSONDecodeError) as err:
        raise ValueError(f"invalid token: {err}") from err


def reserve_scitoken(token_name: str, token_file: str = None):
    """Create the global dictionary entries used for storing/referencing scitokens"""
    if token_file is None:
        token_file = f"/tmp/{token_name}.scitoken"
    core.state[f'token.{token_name}_created'] = False
    core.state[f'token.{token_name}_contents'] = ""
    core.config[f'token.{token_name}'] = token_file


def request_scitoken(token_name: str, scope: str, subject='osg-test', audience="ANY", overwrite=False, log=False):
    """Request a scitoken; set the appropriate entries in core.config and core.state

    :param token_name: A name for the token; will also be used as part of the file name.
    :param scope: "scope" field in the requested token.
    :param subject: "sub" field in the requested token.
    :param audience: "aud" field in the requested token.
    :param overwrite: overwrite an existing token file. If False, the token will be loaded from the existing file.
    :param log: pretty-print the received token to the log

    """
    token_file = core.config[f'token.{token_name}']
    if os.path.exists(token_file):
        if overwrite:
            files.remove(token_file, force=True)
        else:
            core.log_message(f"SciToken {token_name} already exists; loading from file")
            core.state[f'token.{token_name}_contents'] = files.read(token_file, as_single_string=True)
            return

    token_contents = core.to_str(download_demo_scitoken(scope, subject, audience))

    ids = (0, 0)
    if core.state['user.verified']:
        user = pwd.getpwnam(core.options.username)
        ids = (user.pw_uid, user.pw_gid)

    core.state[f'token.{token_name}_contents'] = token_contents

    files.write(token_file, token_contents, backup=False, chown=ids)
    core.state[f'token.{token_name}_created'] = True

    parsed = parse_scitoken(token_contents)

    if log:
        core.log_message(f"{token_name} scitoken:\n"
                         f"  header: {parsed[0]}\n"
                         f"  payload: {parsed[1]}\n")
