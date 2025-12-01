import unittest
from src.ledger import Ledger
from src.types import Block, BlockHeader, Transaction

class DummyBlock(Block):
    pass

class TestLedger(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()
        self.block1 = Block(
            header=BlockHeader(parent_hash="0", height=0, state_commit="h0", proposer="A", signature="sig0"),
            txs=[],
            hash="hash0"
        )
        self.block2 = Block(
            header=BlockHeader(parent_hash="hash0", height=1, state_commit="h1", proposer="A", signature="sig1"),
            txs=[],
            hash="hash1"
        )

    def test_add_and_get_block(self):
        self.ledger.add_block(self.block1)
        self.ledger.add_block(self.block2)
        self.assertEqual(self.ledger.get_block_by_hash("hash0"), self.block1)
        self.assertEqual(self.ledger.get_block_by_height(1), self.block2)
        self.assertEqual(self.ledger.latest_block(), self.block2)
        self.assertEqual(self.ledger.height(), 1)

if __name__ == "__main__":
    unittest.main()
