import os
import hashlib
import base58
import ecdsa
import binascii
from six import b
from fastecdsa import asn1 as fasn1
from fastecdsa import point as fpoint
from fastecdsa import ecdsa as fecdsa
from fastecdsa import curve as fcurve

def priv2pub(priv=None, wif=None):
    pk = b(priv) if isinstance(priv,str) else priv
    wiff = b(wif) if isinstance(wif,str) else wif
    if pk == None:
        assert wiff is not None, "no keys given!"
        privkey = _wif2priv(wiff)
    else:
        privkey = binascii.unhexlify(pk)
    s = ecdsa.SigningKey.from_string(privkey, curve=ecdsa.SECP256k1)
    k = s.get_verifying_key()
    pubkey = b"04" + binascii.hexlify(k.to_string())
    return str(pubkey, 'ascii')

def priv2addr(priv=None, wif=None, main=True):
    pk = b(priv) if isinstance(priv,str) else priv
    wiff = b(wif) if isinstance(wif,str) else wif
    if pk == None:
        assert wiff is not None, "no keys given!"
        privkey = _wif2priv(wiff)
    else:
        privkey = binascii.unhexlify(pk)
    s = ecdsa.SigningKey.from_string(privkey, curve=ecdsa.SECP256k1)
    k = s.get_verifying_key()
    pubkey = b"04" + binascii.hexlify(k.to_string())
    addr = _pub2addr(pubkey,main)
    return str(addr, 'ascii')

def pub2addr(key, main=True):
    pubkey = b(key) if isinstance(key,str) else key
    if len(pubkey) == 128:
        pubkey = b"04" + pubkey
    addr = _pub2addr(pubkey,main=main)      
    return str(addr, 'ascii')

def wif2priv(wif):
    wiff = b(wif) if isinstance(wif,str) else wif
    p = _wif2priv(wiff)
    return str(binascii.hexlify(p), 'ascii')

def _wif2priv(wif):
        ad = base58.b58decode_check(wif)
        if str(wif,'ascii')[0]=='K' or str(wif,'ascii')[0]=='L':
            return ad[1:-1]
        else:
            return ad[1:]

def _pub2addr(key, main=True):
    def enc(key, ad):
        key = ad + binascii.hexlify(key)
        hash_key = binascii.unhexlify(key)
        checksum = hashlib.sha256(hashlib.sha256(hash_key).digest()).digest()[:4]
        key = key + binascii.hexlify(checksum)
        return base58.b58encode(binascii.unhexlify(key))

    ripemd = hashlib.new('ripemd160')
    ripemd.update(hashlib.sha256(binascii.unhexlify(key)).digest())
    key = ripemd.digest()
    ad = b"00" if main else b"6F"
    addr = enc(key,ad)
    return addr

def signdata(priv=None, wif=None, data=None):
    def priv2pemlong(priv):
        skey = ecdsa.SigningKey.from_string(priv,curve=ecdsa.SECP256k1)
        skey = skey.to_pem()
        d = b("").join([l.strip() for l in skey.split(b("\n")) if l and not l.startswith(b("-----"))])
        raw_data = binascii.a2b_base64(d)
        p, Q = fasn1.decode_key(raw_data)
        return p

    assert data is not None, "no data given!"
    pk = b(priv) if isinstance(priv,str) else priv
    wiff = b(wif) if isinstance(wif,str) else wif
    if pk == None:
        assert wiff is not None, "no keys given!"
        privkey = _wif2priv(wiff)
    else:
        privkey = binascii.unhexlify(pk)
    s = priv2pemlong(privkey)
    
    order = 'FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFE BAAEDCE6 AF48A03B BFD25E8C D0364141'
    (r, s) = fecdsa.sign(data, s, fcurve.secp256k1)
    signed = ecdsa.util.sigencode_der(r,s,order)
    return str(binascii.hexlify(signed), 'ascii')

def verifydata(pub=None, verkey=None, sigdata=None, origdata=None):
    def pub2vkey(pub):
        key = pub[2:]
        l = len(key)
        assert l==128, "key length wrong: %i" % l
        x = int(key[:int(l/2)],16)
        y = int(key[int(l/2):],16)
        return fpoint.Point(x,y,curve=fcurve.secp256k1)
    
    assert sigdata is not None, "no signed data given!"
    assert origdata is not None, "no original data given!"
    if pub is not None:
        verkey = pub2vkey(pub)

    sigdata = binascii.unhexlify(sigdata)
    order = 'FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFE BAAEDCE6 AF48A03B BFD25E8C D0364141'
    r,s = ecdsa.util.sigdecode_der(sigdata, order)
    return fecdsa.verify((r,s), origdata, verkey, fcurve.secp256k1)



if __name__ == "__main__":
    priv = '164C0EA5314F63D2BF5FD7DCD387E66ABD0B0DB360032A9E2232E71E51F8565A'
    w = '5JsyQainyFU5CXJsGcdpRArcggbHTUbfmcqXcTUfU62v56VK5La'
    vk = priv2pub(wif=w)
    print("testing priv2pub with priv:", priv2pub(priv=priv))
    print("testing priv2pub with wif:", priv2pub(wif=w))
    print("testing priv2addr with priv:", priv2addr(priv=priv))
    print("testing priv2addr with wif:", priv2addr(wif=w))
    print("testing pub2addr with 0x04:", pub2addr(vk))
    data = "I want to go to disneyland."
    signed1 = signdata(data=data, wif=w)
    result = verifydata(sigdata=signed1, origdata=data, pub=vk)
    print("Result: %s" %(result))