from typing import Dict, List, Optional
from .block import Block
from .logger import log_event

class Ledger:
    """Ledger lưu trữ các block đã finalize và trạng thái cuối cùng."""
    def __init__(self):
        self.blocks: List[Block] = []
        self.block_by_hash: Dict[str, Block] = {}
        self.block_by_height: Dict[int, Block] = {}

    def add_block(self, block: Block):
        log_event(
            component="ledger",
            event="ADD_BLOCK",
            height=block.header.height,
            block_hash=getattr(block, "hash", None)
        )
        self.blocks.append(block)
        self.block_by_hash[block.hash] = block
        self.block_by_height[block.header.height] = block
        log_event(
            component="ledger",
            event="ADD_BLOCK_DONE",
            height=block.header.height,
            block_hash=block.hash
        )

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        log_event(
            component="ledger",
            event="GET_BLOCK_BY_HASH",
            block_hash=block_hash
        )
        return self.block_by_hash.get(block_hash)

    def get_block_by_height(self, height: int) -> Optional[Block]:
        log_event(
            component="ledger",
            event="GET_BLOCK_BY_HEIGHT",
            height=height
        )
        return self.block_by_height.get(height)

    def latest_block(self) -> Optional[Block]:
        log_event(
            component="ledger",
            event="LATEST_BLOCK",
            has_blocks=len(self.blocks) > 0
        )
        if not self.blocks:
            return None
        return self.blocks[-1]

    def height(self) -> int:
        log_event(
            component="ledger",
            event="LEDGER_HEIGHT",
            height=len(self.blocks) - 1
        )
        return len(self.blocks) - 1
