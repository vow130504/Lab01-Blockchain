from typing import Dict, List
from .types import Block, Vote, LedgerEntry
from .block import verify_block
from .consensus import VoteBook, make_vote, verify_vote
from .crypto import generate_keypair

class Node:
    def __init__(self, nid: str, validators: List[str], pk_map: Dict[str, bytes], vote_book: VoteBook):
        self.id = nid
        self.validators = validators
        self.keypair = generate_keypair()  # separate participant key (simplified)
        self.pk_map = pk_map
        self.vote_book = vote_book
        self.blocks_by_height: Dict[int, Block] = {}
        self.ledger: List[LedgerEntry] = []

    def receive_block(self, block: Block):
        if not verify_block(block, self.pk_map):
            return
        h = block.header.height
        if h in self.blocks_by_height: return
        self.blocks_by_height[h] = block
        if self.id in self.validators:
            v = make_vote(self.id, h, block.hash, "PREVOTE", self.keypair.sk)
            self.handle_vote(v)

    def handle_vote(self, v: Vote):
        if not verify_vote(v, self.pk_map): return
        res = self.vote_book.add_vote(v)
        if v.phase == "PREVOTE" and self.id in self.validators:
            # Issue PRECOMMIT if majority prevote reached for this block
            prev_count = len(self.vote_book.prevotes[v.height][v.block_hash])
            if prev_count >= self.vote_book.majority():
                pc = make_vote(self.id, v.height, v.block_hash, "PRECOMMIT", self.keypair.sk)
                self.handle_vote(pc)
        if res.success:
            self.finalize(v.height, v.block_hash)

    def finalize(self, height: int, block_hash: str):
        block = self.blocks_by_height.get(height)
        if not block or block.hash != block_hash: return
        if any(le.height == height for le in self.ledger): return
        self.ledger.append(LedgerEntry(height=height, block_hash=block_hash, state_commit=block.header.state_commit))
