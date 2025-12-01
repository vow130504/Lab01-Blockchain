from typing import Dict, List
from .types import Block, Vote, LedgerEntry
from .block import verify_block
from .consensus import VoteBook, make_vote, verify_vote
from .crypto import generate_keypair
from .state import State, verify_tx
from .logger import log_event

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
        log_event(
            component="node",
            event="RECEIVE_BLOCK",
            node_id=self.id,
            height=block.header.height,
            block_hash=getattr(block, "hash", None),
        )
        # Verify block signature and state commitment using local parent state
        if not verify_block(block, self.pk_map, parent_state=self.state):
            log_event(
                component="node",
                event="BLOCK_REJECT",
                node_id=self.id,
                height=block.header.height,
                block_hash=getattr(block, "hash", None),
                reason="verify_block_failed",
            )
            return
        h = block.header.height
        if h in self.blocks_by_height: 
            log_event(
                component="node",
                event="BLOCK_DUPLICATE",
                node_id=self.id,
                height=h,
                block_hash=getattr(block, "hash", None),
            )
            return
        self.blocks_by_height[h] = block
        log_event(
            component="node",
            event="BLOCK_ACCEPT",
            node_id=self.id,
            height=h,
            block_hash=getattr(block, "hash", None),
        )
        if self.id in self.validators:
            v = make_vote(self.id, h, block.hash, "PREVOTE", self.keypair.sk)
            log_event(
                component="node",
                event="ISSUE_PREVOTE",
                node_id=self.id,
                height=h,
                block_hash=block.hash,
            )
            self.handle_vote(v)

    def receive_vote(self, v: Vote):
        log_event(
            component="node",
            event="RECEIVE_VOTE",
            node_id=self.id,
            height=v.height,
            block_hash=v.block_hash,
            phase=v.phase,
            validator=v.validator,
        )
        self.handle_vote(v)

    def handle_vote(self, v: Vote):
        if not verify_vote(v, self.pk_map): 
            log_event(
                component="node",
                event="VOTE_INVALID",
                node_id=self.id,
                height=v.height,
                block_hash=v.block_hash,
                phase=v.phase,
                validator=v.validator,
            )
            return
        
        # Check if we already have this vote to avoid infinite loops if we were to rebroadcast (we don't rebroadcast here but good practice)
        # Actually, VoteBook handles duplicates, but we need to know if it's new to decide on actions.
        # For now, just add it.
        res = self.vote_book.add_vote(v)
        
        # If it's our own vote, broadcast it
        if v.validator == self.id and self.broadcast_cb:
            log_event(
                component="node",
                event="BROADCAST_VOTE",
                node_id=self.id,
                height=v.height,
                block_hash=v.block_hash,
                phase=v.phase,
            )
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
                    log_event(
                        component="node",
                        event="ISSUE_PRECOMMIT",
                        node_id=self.id,
                        height=v.height,
                        block_hash=v.block_hash,
                    )
                    self.handle_vote(pc)

        if res.success:
            log_event(
                component="node",
                event="FINALIZE_TRIGGER",
                node_id=self.id,
                height=v.height,
                block_hash=v.block_hash,
            )
            self.finalize(v.height, v.block_hash)

    def finalize(self, height: int, block_hash: str):
        block = self.blocks_by_height.get(height)
        if not block or block.hash != block_hash: 
            log_event(
                component="node",
                event="FINALIZE_SKIP",
                node_id=self.id,
                height=height,
                block_hash=block_hash,
                reason="block_missing_or_hash_mismatch",
            )
            return
        if any(le.height == height for le in self.ledger): 
            log_event(
                component="node",
                event="FINALIZE_SKIP",
                node_id=self.id,
                height=height,
                block_hash=block_hash,
                reason="already_in_ledger",
            )
            return
        # Apply block transactions to local state (only valid txs)
        for tx in block.txs:
            if verify_tx(tx, self.pk_map):
                self.state.apply(tx)
        # Append ledger entry after state updated
        self.ledger.append(LedgerEntry(height=height, block_hash=block_hash, state_commit=block.header.state_commit))
        log_event(
            component="node",
            event="FINALIZE_COMMIT",
            node=self.id,
            height=height,
            block_hash=block_hash
        )
