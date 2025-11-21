from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Transaction:
    sender: str
    key: str
    value: str
    signature: str  # hex
    def id(self) -> str:
        return f"{self.sender}:{self.key}"

@dataclass
class BlockHeader:
    parent_hash: str
    height: int
    state_commit: str
    proposer: str
    signature: str  # hex

@dataclass
class Block:
    header: BlockHeader
    txs: List[Transaction]
    hash: str

@dataclass
class Vote:
    validator: str
    height: int
    block_hash: str
    phase: str  # PREVOTE / PRECOMMIT
    signature: str  # hex

@dataclass
class LedgerEntry:
    height: int
    block_hash: str
    state_commit: str

@dataclass
class FinalizationResult:
    height: int
    block_hash: str
    success: bool
    reason: str = ""
