from typing import List, Dict
from .crypto import generate_keypair
from .block import build_block
from .consensus import VoteBook
from .network import UnreliableNetwork
from .node import Node

class Simulator:
    def __init__(self, n_nodes: int, seed: int):
        self.seed = seed
        self.node_ids = [f"N{i}" for i in range(n_nodes)]
        self.validator_ids = self.node_ids  # all validators for simplicity
        self.pk_map: Dict[str, bytes] = {}
        self.signers = {}
        for vid in self.validator_ids:
            kp = generate_keypair()
            self.pk_map[vid] = kp.pk
            self.signers[vid] = kp.sk
        # self.vote_book = VoteBook(self.validator_ids) # REMOVED: Shared vote book
        self.network = UnreliableNetwork(self.node_ids, seed)
        
        # Create nodes with individual VoteBooks and broadcast callback
        self.nodes: Dict[str, Node] = {}
        for nid in self.node_ids:
            vb = VoteBook(self.validator_ids)
            # Define a closure for broadcast that captures self.network
            # We need to be careful with scope, but here it's fine as self.network is stable
            def broadcast(h, p):
                self.network.broadcast(nid, h, p)
            
            self.nodes[nid] = Node(nid, self.validator_ids, self.pk_map, vb, broadcast_cb=broadcast)

        self.height = 1
        self.parent_hash = "GENESIS"

    def propose(self):
        proposer = self.node_ids[self.height % len(self.node_ids)]
        sk = self.signers[proposer]
        txs = []  # Empty tx batch; extend as needed
        block = build_block(self.parent_hash, self.height, txs, proposer, sk, self.pk_map)
        # Broadcast block (header/body simplified as one message)
        self.network.broadcast(proposer, self.height, ("BLOCK", block))

    def run_until(self, target_height: int):
        while self.height <= target_height:
            self.propose()
            # Process events until block finalized
            while True:
                def handler(ev):
                    typ, payload = ev.payload
                    if typ == "BLOCK":
                        self.nodes[ev.dst].receive_block(payload)
                    elif typ == "VOTE":
                        self.nodes[ev.dst].receive_vote(payload)

                self.network.step(handler)
                if all(le.height >= self.height for n in self.nodes.values() for le in n.ledger if le.height == self.height):
                    break
                if self.network.idle():
                    break
            # Advance parent hash if finalized
            # We need to check if *any* node finalized (or all, depending on termination condition)
            # The loop above breaks when ALL nodes finalize.
            # We can pick any node's ledger to get the finalized hash for the next block.
            # Since they are consistent, any node works.
            sample_node = self.nodes[self.node_ids[0]]
            finalized_entry = next((le for le in sample_node.ledger if le.height == self.height), None)
            if finalized_entry:
                self.parent_hash = finalized_entry.block_hash
            
            self.height += 1

    def collect_logs(self):
        return "\n".join(self.network.log)
