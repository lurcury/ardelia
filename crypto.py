"""
    Provides crypto conversions for peerManager and peers.
    All input/output are strings
    Functions:
        - priv2addr
        - pub2addr
"""
import os
import hashlib
import base58
import ecdsa
import binascii
from six import b


def priv2addr(key):
    k = _priv2addr(key)
    return str(k,'ascii')

def pub2addr(key):
    k = _pub2addr(b(key))
    return str(k,'ascii')

def priv2pub(key):
    k = _priv2pub(key)
    return str(k,'ascii')

def priv2wif(key):
    return _encrypt(b(key), b"80") if key else None

def wif2priv(key):
    return base58.b58decode_check(b(key))[1:] if key else None

# private functions
def _priv2addr(key):
    k = _priv2pub(key)
    return _pub2addr(k)

def _priv2pub(key):
    s = ecdsa.SigningKey.from_string(key, curve=ecdsa.SECP256k1)
    v = s.get_verifying_key()
    return binascii.hexlify(v.to_string())

def _pub2addr(key):
    pub = b"04" + key
    ripemd = hashlib.new('ripemd160')
    ripemd.update(hashlib.sha256(binascii.unhexlify(pub)).digest())
    key = ripemd.digest()
    return _encrypt(key, b"00")

def _encrypt(key, ad):
    key = ad + binascii.hexlify(key)
    hash_key = binascii.unhexlify(key)
    checksum = hashlib.sha256(hashlib.sha256(hash_key).digest()).digest()[:4]
    key = key + binascii.hexlify(checksum)
    return base58.b58encode(binascii.unhexlify(key))


if __name__ == "__main__":
    priv = 'L1uyy5qTuGrVXrmrsvHWHgVzW9kKdrp27wBC7Vs6nZDTF2BRUVwy'
    addr = priv2addr(priv)
    print("wif:", addr)