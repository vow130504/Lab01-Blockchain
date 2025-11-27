from typing import List, Dict
from .crypto import generate_keypair
from .block import build_block
from .consensus import VoteBook
from .network import UnreliableNetwork, Message
from .node import Node

class Simulator:
    def __init__(self, n_nodes: int, seed: int, block_duration: int = 10):
        self.seed = seed
        self.node_ids = [f"N{i}" for i in range(n_nodes)]
        self.validator_ids = self.node_ids  # all validators for simplicity

        # Key pairs for validators
        self.pk_map: Dict[str, bytes] = {}
        self.signers = {}
        for vid in self.validator_ids:
            kp = generate_keypair()
            self.pk_map[vid] = kp.pk
            self.signers[vid] = kp.sk

        # Consensus tracker
        self.vote_book = VoteBook(self.validator_ids)

        # Node instances
        self.nodes: Dict[str, Node] = {
            nid: Node(nid, self.validator_ids, self.pk_map, self.vote_book)
            for nid in self.node_ids
        }

        # Network
        self.network = UnreliableNetwork(
            self.node_ids, seed, block_duration=block_duration
        )

        self.height = 1
        self.parent_hash = "GENESIS"

    def propose(self):
        proposer = self.node_ids[self.height % len(self.node_ids)]
        sk = self.signers[proposer]

        # Build empty block
        txs = []  # Extend with transactions if needed
        block = build_block(self.parent_hash, self.height, txs, proposer, sk, self.pk_map)

        # Create HEADER and BODY messages
        header_msg = Message(
            msg_id=f"H_{self.height}",
            kind="HEADER",
            height=self.height,
            body={"block_hash": block.hash}
        )
        body_msg = Message(
            msg_id=f"B_{self.height}",
            kind="BODY",
            height=self.height,
            body={"block": block, "block_hash": block.hash}
        )

        # Broadcast to all peers
        self.network.broadcast(proposer, header_msg)
        self.network.broadcast(proposer, body_msg)

    def run_until(self, target_height: int):
        while self.height <= target_height:
            self.propose()

            # Process events until block finalized
            while True:
                def handler(msg: Message):
                    # Deliver block to node if BODY or HEADER
                    if msg.kind in ["HEADER", "BODY"]:
                        block = msg.body.get("block")
                        if block:
                            self.nodes[msg.dst].receive_block(block)

                self.network.step(handler)

                # Check if all nodes have at least one ledger entry for this height
                all_received = all(
                    any(le.height == self.height for le in n.ledger)
                    for n in self.nodes.values()
                )
                if all_received or self.network.idle():
                    break

            # Advance parent hash if block finalized
            if self.height in self.vote_book.finalized:
                self.parent_hash = self.vote_book.finalized[self.height]

            self.height += 1

    def collect_logs(self) -> str:
        """Return the full network log as a string"""
        return "\n".join(self.network.log)
