import hashlib
from dataclasses import dataclass
from typing import Tuple

# Lightweight placeholder Ed25519 using pynacl if available; else mock (NOT secure).
try:
    from nacl import signing
except ImportError:
    signing = None

CHAIN_ID = "Lab01Chain"
CTX_TX = f"TX:{CHAIN_ID}"
CTX_HEADER = f"HEADER:{CHAIN_ID}"
CTX_VOTE = f"VOTE:{CHAIN_ID}"

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def encode_kv_state(state: dict) -> bytes:
    # Deterministic: sort keys, length-prefix key/value
    out = bytearray()
    for k in sorted(state.keys()):
        v = state[k]
        kb = k.encode()
        vb = v.encode()
        out += len(kb).to_bytes(4, 'big') + kb + len(vb).to_bytes(4, 'big') + vb
    return bytes(out)

def state_hash(state: dict) -> str:
    return sha256(encode_kv_state(state)).hex()

def encode_fields(fields: Tuple[str, ...]) -> bytes:
    # Simple deterministic encoding: count + each length-prefixed utf-8
    out = bytearray()
    out += len(fields).to_bytes(2, 'big')
    for f in fields:
        b = f.encode()
        out += len(b).to_bytes(4, 'big') + b
    return bytes(out)

@dataclass
class KeyPair:
    sk: object
    pk: bytes

def generate_keypair() -> KeyPair:
    if not signing:
        # Insecure fallback deterministic bytes for test only
        fake = hashlib.sha256(b"seed").digest()
        return KeyPair(sk=fake, pk=fake)
    sk = signing.SigningKey.generate()
    pk = sk.verify_key.encode()
    return KeyPair(sk=sk, pk=pk)

def sign(context: str, fields: Tuple[str, ...], sk) -> bytes:
    msg = context.encode() + b":" + encode_fields(fields)
    if signing and isinstance(sk, signing.SigningKey):
        return sk.sign(msg).signature
    return sha256(msg + sk)  # fallback mock

def verify(context: str, fields: Tuple[str, ...], pk: bytes, sig: bytes) -> bool:
    msg = context.encode() + b":" + encode_fields(fields)
    if signing:
        try:
            vk = signing.VerifyKey(pk)
            vk.verify(msg, sig)
            return True
        except Exception:
            return False
    return sha256(msg + pk) == sig
