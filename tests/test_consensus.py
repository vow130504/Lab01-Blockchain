import unittest
from src.consensus import VoteBook, make_vote, verify_vote
from src.node import Node
from src.types import Vote, Block, BlockHeader, Transaction
from src.crypto import generate_keypair
from src.block import build_block

class TestConsensus(unittest.TestCase):
    def setUp(self):
        self.validators = ["V1", "V2", "V3", "V4"]
        self.pk_map = {}
        self.signers = {}
        for v in self.validators:
            kp = generate_keypair()
            self.pk_map[v] = kp.pk
            self.signers[v] = kp.sk
        self.vote_book = VoteBook(self.validators)

    def test_vote_book_majority(self):
        self.assertEqual(self.vote_book.majority(), 3)  # (2*4)//3 + 1 = 2 + 1 = 3

    def test_make_and_verify_vote(self):
        v = make_vote("V1", 1, "hash123", "PREVOTE", self.signers["V1"])
        self.assertTrue(verify_vote(v, self.pk_map))
        # Test invalid signature by modifying fields
        v.block_hash = "wronghash"
        self.assertFalse(verify_vote(v, self.pk_map))
        # Test unknown validator
        v.validator = "Unknown"
        self.assertFalse(verify_vote(v, self.pk_map))

    def test_add_vote_prevote(self):
        v = make_vote("V1", 1, "hash123", "PREVOTE", self.signers["V1"])
        res = self.vote_book.add_vote(v)
        self.assertFalse(res.success)
        self.assertEqual(len(self.vote_book.prevotes[1]["hash123"]), 1)

    def test_add_vote_precommit_no_finalize(self):
        # Add prevotes first
        for i in range(2):
            v = make_vote(self.validators[i], 1, "hash123", "PREVOTE", self.signers[self.validators[i]])
            self.vote_book.add_vote(v)
        # Add precommit
        pc = make_vote("V1", 1, "hash123", "PRECOMMIT", self.signers["V1"])
        res = self.vote_book.add_vote(pc)
        self.assertFalse(res.success)  # Not majority yet

    def test_finalization(self):
        # Add majority precommits
        for i in range(3):
            pc = make_vote(self.validators[i], 1, "hash123", "PRECOMMIT", self.signers[self.validators[i]])
            res = self.vote_book.add_vote(pc)
        self.assertTrue(res.success)
        self.assertEqual(self.vote_book.finalized[1], "hash123")

    def test_safety_no_double_finalize(self):
        # Finalize one block
        for i in range(3):
            pc = make_vote(self.validators[i], 1, "hash123", "PRECOMMIT", self.signers[self.validators[i]])
            self.vote_book.add_vote(pc)
        # Try to finalize another block at same height with majority
        for i in range(3):
            pc2 = make_vote(self.validators[i], 1, "hash456", "PRECOMMIT", self.signers[self.validators[i]])
            res = self.vote_book.add_vote(pc2)
        self.assertFalse(res.success)
        self.assertEqual(res.reason, "Conflicting finalization attempt")

    def test_node_receive_block_and_vote(self):
        node = Node("V1", self.validators, self.pk_map, self.vote_book)
        # Set node's keypair to match
        kp = type('KP', (), {'sk': self.signers["V1"], 'pk': self.pk_map["V1"]})()
        node.keypair = kp
        # Create a block
        txs = []
        block = build_block("parent", 1, txs, "V1", self.signers["V1"], self.pk_map)
        node.receive_block(block)
        # Check prevote added
        self.assertIn("V1", self.vote_book.prevotes[1][block.hash])

    def test_node_handle_vote_and_precommit(self):
        node = Node("V1", self.validators, self.pk_map, self.vote_book)
        # Set node's keypair to match
        kp = type('KP', (), {'sk': self.signers["V1"], 'pk': self.pk_map["V1"]})()
        node.keypair = kp
        # Add majority prevotes
        for i in range(3):
            v = make_vote(self.validators[i], 1, "hash123", "PREVOTE", self.signers[self.validators[i]])
            node.handle_vote(v)
        # Node should have issued precommit
        self.assertIn("V1", self.vote_book.precommits[1]["hash123"])

    def test_node_finalize(self):
        node = Node("V1", self.validators, self.pk_map, self.vote_book)
        # Set node's keypair to match
        kp = type('KP', (), {'sk': self.signers["V1"], 'pk': self.pk_map["V1"]})()
        node.keypair = kp
        # Create and receive block
        txs = []
        block = build_block("parent", 1, txs, "V1", self.signers["V1"], self.pk_map)
        node.receive_block(block)
        # Add majority precommits
        for i in range(3):
            pc = make_vote(self.validators[i], 1, block.hash, "PRECOMMIT", self.signers[self.validators[i]])
            node.handle_vote(pc)
        # Check finalized
        self.assertEqual(len(node.ledger), 1)
        self.assertEqual(node.ledger[0].height, 1)
        self.assertEqual(node.ledger[0].block_hash, block.hash)

if __name__ == '__main__':
    unittest.main()