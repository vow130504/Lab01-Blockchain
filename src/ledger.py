from typing import Dict, List, Optional
from .block import Block

class Ledger:
    """Ledger lưu trữ các block đã finalize và trạng thái cuối cùng."""
    def __init__(self):
        self.blocks: List[Block] = []
        self.block_by_hash: Dict[str, Block] = {}
        self.block_by_height: Dict[int, Block] = {}

    def add_block(self, block: Block):
        self.blocks.append(block)
        self.block_by_hash[block.hash] = block
        self.block_by_height[block.header.height] = block

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        return self.block_by_hash.get(block_hash)

    def get_block_by_height(self, height: int) -> Optional[Block]:
        return self.block_by_height.get(height)

    def latest_block(self) -> Optional[Block]:
        if not self.blocks:
            return None
        return self.blocks[-1]

    def height(self) -> int:
        return len(self.blocks) - 1
