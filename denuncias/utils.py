import hmac
import hashlib
import time
from typing import Optional

def _int_to_bytes(value: int) -> bytes:
    return value.to_bytes(8, 'big')

def hotp(secret: bytes, counter: int, digits: int=8) -> str:
    h = hmac.new(secret, _int_to_bytes(counter), hashlib.sha1).digest()
    offset = h[-1] & 15
    code = (h[offset] & 127) << 24 | (h[offset + 1] & 255) << 16 | (h[offset + 2] & 255) << 8 | h[offset + 3] & 255
    token = code % 10 ** digits
    return str(token).zfill(digits)

def totp(secret: str, timestep: int=60, digits: int=8, for_time: Optional[int]=None) -> str:
    if for_time is None:
        for_time = int(time.time())
    counter = for_time // timestep
    secret_bytes = secret.encode('utf-8')
    return hotp(secret_bytes, counter, digits)

def validate_totp_token(token: str, secret: str, timestep: int=60, digits: int=8, window: int=1) -> bool:
    now = int(time.time())
    for offset in range(-window, window + 1):
        if totp(secret, timestep=timestep, digits=digits, for_time=now + offset * timestep) == token:
            return True
    return False
