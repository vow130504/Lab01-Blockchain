from typing import Dict, Set
from .crypto import state_hash, CTX_TX, sign, verify, encode_fields
from .types import Transaction

class State:
    """Deterministic key-value state with transaction replay protection.
    
    Workflow:
    1. State được khởi tạo từ parent state (hoặc empty cho genesis)
    2. Transactions được apply tuần tự (verify signature → check ownership → update kv)
    3. Executed tx_ids được track để prevent replay
    4. commit() tạo deterministic hash của state
    """
    def __init__(self, parent_kv: Dict[str, str] = None, executed_txs: Set[str] = None):
        # Inherit state from parent block (copy để không mutate parent)
        self.kv: Dict[str, str] = dict(parent_kv) if parent_kv else {}
        # Copy executed transactions set to preserve replay protection across chain
        self.executed_txs: Set[str] = set(executed_txs) if executed_txs else set()

    def apply(self, tx: Transaction) -> bool:
        """Apply transaction to state với validation.
        
        Returns True nếu tx được apply thành công, False nếu invalid.
        
        Checks:
        1. Replay protection: tx đã được execute chưa?
        2. Ownership: sender chỉ có thể modify sender/* keys
        """
        tx_id = tx.id()
        
        # Replay protection: prevent executing same tx twice
        if tx_id in self.executed_txs:
            return False
        
        # Ownership: sender can only modify sender/*
        if not tx.key.startswith(tx.sender + "/"):
            return False
        
        # Apply transaction
        self.kv[tx.key] = tx.value
        self.executed_txs.add(tx_id)
        return True

    def commit(self) -> str:
        """Generate deterministic commitment hash of current state."""
        return state_hash(self.kv)
    
    def copy(self) -> 'State':
        """Create a deep copy of state for speculation/testing."""
        new_state = State(self.kv)
        new_state.executed_txs = set(self.executed_txs)
        return new_state
    
    def get(self, key: str) -> str:
        """Get value from state, return empty string if not found."""
        return self.kv.get(key, "")

def make_tx(sender: str, key: str, value: str, nonce: int, sk, pk) -> Transaction:
    fields = (sender, key, value, nonce)
    sig = sign(CTX_TX, fields, sk).hex()
    return Transaction(sender=sender, key=key, value=value, nonce=nonce, signature=sig)

def verify_tx(tx: Transaction, pk_map: Dict[str, bytes]) -> bool:
    if tx.sender not in pk_map: return False
    fields = (tx.sender, tx.key, tx.value, tx.nonce)
    return verify(CTX_TX, fields, pk_map[tx.sender], bytes.fromhex(tx.signature))
