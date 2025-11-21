from typing import Dict
from .crypto import state_hash, CTX_TX, sign, verify, encode_fields
from .types import Transaction

class State:
    def __init__(self):
        self.kv: Dict[str, str] = {}

    def apply(self, tx: Transaction) -> bool:
        # Ownership: sender can only modify sender/*
        if not tx.key.startswith(tx.sender + "/"):
            return False
        self.kv[tx.key] = tx.value
        return True

    def commit(self) -> str:
        return state_hash(self.kv)

def make_tx(sender: str, key: str, value: str, sk, pk) -> Transaction:
    fields = (sender, key, value)
    sig = sign(CTX_TX, fields, sk).hex()
    return Transaction(sender=sender, key=key, value=value, signature=sig)

def verify_tx(tx: Transaction, pk_map: Dict[str, bytes]) -> bool:
    if tx.sender not in pk_map: return False
    fields = (tx.sender, tx.key, tx.value)
    return verify(CTX_TX, fields, pk_map[tx.sender], bytes.fromhex(tx.signature))
