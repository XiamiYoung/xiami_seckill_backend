import jwt
from config.config import global_config
from config.error_dict import error_dict
from exception.restful_exception import RestfulException

from utils.util import (
    datetime_offset_in_milliesec,
    get_now_datetime,
    get_timestamp_in_milli_sec
)

secret = global_config.get('config', 'token_secret')
jwt_idle_expiration = int(global_config.get('config', 'jwt_idle_expiration'))
jwt_hard_expiration = int(global_config.get('config', 'jwt_hard_expiration'))

def encrypt_json(json_obj, secret):
    return jwt.encode(json_obj, secret, algorithm="HS256")

def decrypt_token(token, secret):
    return jwt.decode(token, secret, algorithms=["HS256"])

def generate_token(username):
    now_dt = get_now_datetime()
    now_dt_ts = get_timestamp_in_milli_sec(now_dt)
    idle_exp = get_timestamp_in_milli_sec(datetime_offset_in_milliesec(now_dt, jwt_idle_expiration * 1000))
    hard_exp = get_timestamp_in_milli_sec(datetime_offset_in_milliesec(now_dt, jwt_hard_expiration * 1000))
    token_claims = {
        'sub': username,
        'iat': now_dt_ts,
        'hard_exp': hard_exp,
        'idle_exp': idle_exp
    }
    return jwt.encode(token_claims, secret, algorithm="HS256")

def get_claims_from_token(token):
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        exception = RestfulException(error_dict['USER']['TOKEN_INVALID'])
        raise exception

def get_user_name_from_token(token):
    claims = get_claims_from_token(token)
    return claims['sub']

def is_token_expired(token):
    claims = get_claims_from_token(token)
    idle_exp = claims['idle_exp']
    hard_exp = claims['hard_exp']
    now_ts = get_timestamp_in_milli_sec(get_now_datetime())
    is_expired = now_ts > idle_exp or idle_exp > hard_exp
    return is_expired


def refresh_token(token):
    try:
        claims = get_claims_from_token(token)
        now_dt = get_now_datetime()
        now_dt_ts = get_timestamp_in_milli_sec(now_dt)
        idle_exp = get_timestamp_in_milli_sec(datetime_offset_in_milliesec(now_dt, jwt_idle_expiration * 1000))
        claims['iat'] = now_dt_ts
        claims['idle_exp'] = idle_exp
        return jwt.encode(claims, secret, algorithm="HS256")
    except Exception:
        exception = RestfulException(error_dict['USER']['SESSION_TIMEOUT'])
        raise exception

def expireToken(token):
    claims = get_claims_from_token(token)
    now_dt = get_now_datetime()
    now_dt_ts = get_timestamp_in_milli_sec(now_dt)
    claims['iat'] = now_dt_ts
    claims['idle_exp'] = now_dt_ts
    claims['hard_exp'] = now_dt_ts
    return jwt.encode(claims, secret, algorithm="HS256")


def validate_token(token, header_user_name):
    if not token:
        exception = RestfulException(error_dict['USER']['TOKEN_INVALID'])
        raise exception

    token_username = get_user_name_from_token(token)
    if token_username != header_user_name:
        exception = RestfulException(error_dict['USER']['TOKEN_INVALID'])
        raise exception

    if is_token_expired(token):
        exception = RestfulException(error_dict['USER']['SESSION_TIMEOUT'])
        raise exception

    return True