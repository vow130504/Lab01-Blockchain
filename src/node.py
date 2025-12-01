from typing import Dict, List
from .types import Block, Vote, LedgerEntry
from .block import verify_block
from .consensus import VoteBook, make_vote, verify_vote
from .crypto import generate_keypair
from .state import State, verify_tx

class Node:
    def __init__(self, nid: str, validators: List[str], pk_map: Dict[str, bytes], vote_book: VoteBook, broadcast_cb=None):
        self.id = nid
        self.validators = validators
        self.keypair = generate_keypair()  # separate participant key (simplified)
        self.pk_map = pk_map
        self.vote_book = vote_book
        self.blocks_by_height: Dict[int, Block] = {}
        self.ledger: List[LedgerEntry] = []
        self.broadcast_cb = broadcast_cb
        # Local application state maintained by this node
        self.state = State()

    def receive_block(self, block: Block):
        # Verify block signature and state commitment using local parent state
        if not verify_block(block, self.pk_map, parent_state=self.state):
            return
        h = block.header.height
        if h in self.blocks_by_height: return
        self.blocks_by_height[h] = block
        if self.id in self.validators:
            v = make_vote(self.id, h, block.hash, "PREVOTE", self.keypair.sk)
            self.handle_vote(v)

    def receive_vote(self, v: Vote):
        self.handle_vote(v)

    def handle_vote(self, v: Vote):
        if not verify_vote(v, self.pk_map): return
        
        # Check if we already have this vote to avoid infinite loops if we were to rebroadcast (we don't rebroadcast here but good practice)
        # Actually, VoteBook handles duplicates, but we need to know if it's new to decide on actions.
        # For now, just add it.
        res = self.vote_book.add_vote(v)
        
        # If it's our own vote, broadcast it
        if v.validator == self.id and self.broadcast_cb:
            self.broadcast_cb(v.height, ("VOTE", v))

        if v.phase == "PREVOTE" and self.id in self.validators:
            # Issue PRECOMMIT if majority prevote reached for this block
            prev_count = len(self.vote_book.prevotes[v.height][v.block_hash])
            if prev_count >= self.vote_book.majority():
                # Check if we already precommitted for this height/block
                # (VoteBook doesn't explicitly track "my" votes separately, but we can check if we are in the set)
                # However, make_vote is deterministic for same inputs.
                # We need to ensure we don't spam precommits.
                # Simple check: is my id in the precommits for this block?
                if self.id not in self.vote_book.precommits[v.height][v.block_hash]:
                    pc = make_vote(self.id, v.height, v.block_hash, "PRECOMMIT", self.keypair.sk)
                    self.handle_vote(pc)

        if res.success:
            self.finalize(v.height, v.block_hash)

    def finalize(self, height: int, block_hash: str):
        block = self.blocks_by_height.get(height)
        if not block or block.hash != block_hash: return
        if any(le.height == height for le in self.ledger): return
        # Apply block transactions to local state (only valid txs)
        for tx in block.txs:
            if verify_tx(tx, self.pk_map):
                self.state.apply(tx)
        # Append ledger entry after state updated
        self.ledger.append(LedgerEntry(height=height, block_hash=block_hash, state_commit=block.header.state_commit))
