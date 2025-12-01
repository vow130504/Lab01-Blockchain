from typing import List, Dict

from .crypto import generate_keypair
from .block import build_block
from .consensus import VoteBook
from .network import UnreliableNetwork, Message
from .node import Node
from .logger import log_event


class Simulator:
    def __init__(self, n_nodes: int, seed: int):
        self.seed = seed
        self.node_ids = [f"N{i}" for i in range(n_nodes)]
        self.validator_ids = self.node_ids  # all validators for simplicity
        self.pk_map: Dict[str, bytes] = {}
        self.signers = {}

        # Tạo keypair cho từng validator
        for vid in self.validator_ids:
            kp = generate_keypair()
            self.pk_map[vid] = kp.pk
            self.signers[vid] = kp.sk

        # Mạng không tin cậy
        self.network = UnreliableNetwork(self.node_ids, seed)

        # Tạo Node + VoteBook riêng cho từng node
        self.nodes: Dict[str, Node] = {}

        # Hàm tạo broadcast callback cho từng node
        def make_broadcast(src_id: str):
            def broadcast(height: int, payload):
                typ, obj = payload

                if typ == "VOTE":
                    msg = Message(
                        msg_id=f"vote_{src_id}_{height}_{obj.block_hash}",
                        kind="VOTE",
                        height=height,
                        body={"vote": obj},
                    )
                    self.network.broadcast(src_id, msg)
                # nếu sau này có loại khác thì thêm ở đây
            return broadcast

        for nid in self.node_ids:
            vb = VoteBook(self.validator_ids)
            self.nodes[nid] = Node(
                nid,
                self.validator_ids,
                self.pk_map,
                vb,
                broadcast_cb=make_broadcast(nid),
            )

        self.height = 1
        self.parent_hash = "GENESIS"

    def propose(self):
        proposer = self.node_ids[self.height % len(self.node_ids)]
        sk = self.signers[proposer]
        txs = []  # Empty tx batch; extend as needed

        block = build_block(self.parent_hash, self.height, txs, proposer, sk, self.pk_map)

        # Ghi log đề xuất block
        log_event(
            component="simulator",
            event="PROPOSE_BLOCK",
            height=self.height,
            proposer=proposer,
            parent_hash=self.parent_hash,
            block_hash=getattr(block, "hash", None),
        )

        # Wrap block vào Message cho network
        msg = Message(
            msg_id=f"blk_{self.height}",
            kind="BLOCK",
            height=self.height,
            body={"block": block},
        )

        # Gửi qua UnreliableNetwork - API mới: (src, msg)
        self.network.broadcast(proposer, msg)

    def run_until(self, target_height: int):
        while self.height <= target_height:
            self.propose()

            # Process events until block finalized
            while True:
                # Đây chính là handler bạn hỏi – nó nằm bên trong run_until
                def handler(msg: Message):
                    if msg.kind == "BLOCK":
                        block = msg.body["block"]
                        for node in self.nodes.values():
                            node.receive_block(block)
                    elif msg.kind == "VOTE":
                        vote = msg.body["vote"]
                        for node in self.nodes.values():
                            node.receive_vote(vote)

                # network.step sẽ gọi handler(msg)
                self.network.step(handler)

                # Điều kiện dừng: tất cả node đã finalize height hiện tại
                if all(
                    any(le.height == self.height for le in n.ledger)
                    for n in self.nodes.values()
                ):
                    break

                if self.network.idle():
                    break

            # Lấy block_hash đã finalize để làm parent cho height tiếp theo
            sample_node = self.nodes[self.node_ids[0]]
            finalized_entry = next(
                (le for le in sample_node.ledger if le.height == self.height),
                None,
            )
            if finalized_entry:
                self.parent_hash = finalized_entry.block_hash
                log_event(
                    component="simulator",
                    event="HEIGHT_FINALIZED",
                    height=self.height,
                    block_hash=finalized_entry.block_hash,
                )

            self.height += 1

    def collect_logs(self) -> str:
        return "\n".join(self.network.log)
