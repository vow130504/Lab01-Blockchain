from typing import List, Dict
from .types import Block, BlockHeader, Transaction
from .state import State, verify_tx
from .crypto import sha256, sign, verify, CTX_HEADER

def build_block(parent_hash: str, height: int, txs: List[Transaction], proposer: str, sk, pk_map: Dict[str, bytes]) -> Block:
    st = State()
    # Execute txs deterministically (assume parent state separately applied; here minimal)
    for tx in txs:
        if not verify_tx(tx, pk_map): continue
        st.apply(tx)
    commit = st.commit()
    header_fields = (parent_hash, str(height), commit, proposer)
    sig = sign(CTX_HEADER, header_fields, sk).hex()
    header = BlockHeader(parent_hash=parent_hash, height=height, state_commit=commit, proposer=proposer, signature=sig)
    h_bytes = parent_hash.encode() + b":" + str(height).encode() + commit.encode()
    block_hash = sha256(h_bytes).hex()
    return Block(header=header, txs=txs, hash=block_hash)

def verify_block(block: Block, pk_map: Dict[str, bytes]) -> bool:
    if block.header.proposer not in pk_map: return False
    fields = (block.header.parent_hash, str(block.header.height), block.header.state_commit, block.header.proposer)
    if not verify(CTX_HEADER, fields, pk_map[block.header.proposer], bytes.fromhex(block.header.signature)):
        return False
    # Deterministic recompute commitment from txs
    st = State()
    for tx in block.txs:
        if verify_tx(tx, pk_map):
            st.apply(tx)
    return st.commit() == block.header.state_commit
