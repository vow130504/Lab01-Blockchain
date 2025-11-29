import unittest
from src.state import State, make_tx, verify_tx
from src.types import Transaction

class TestState(unittest.TestCase):
    def setUp(self):
        self.state = State()
        self.sender = "alice"
        self.key = "alice/balance"
        self.value = "100"
        self.sk = b"dummy_sk"
        self.pk = b"dummy_pk"
        self.pk_map = {self.sender: self.pk}
        # Patch sign/verify for test
        import src.crypto
        src.crypto.sign = lambda ctx, fields, sk: b"sig"
        src.crypto.verify = lambda ctx, fields, pk, sig: True

    def test_apply_and_commit(self):
        tx = make_tx(self.sender, self.key, self.value, self.sk, self.pk)
        self.assertTrue(self.state.apply(tx))
        self.assertIn(self.key, self.state.kv)
        self.assertEqual(self.state.kv[self.key], self.value)
        commit1 = self.state.commit()
        # Apply same tx again (should fail replay)
        self.assertFalse(self.state.apply(tx))
        # Commit hash should be deterministic
        commit2 = self.state.commit()
        self.assertEqual(commit1, commit2)

    def test_ownership(self):
        tx = make_tx(self.sender, "bob/balance", self.value, self.sk, self.pk)
        self.assertFalse(self.state.apply(tx))

if __name__ == "__main__":
    unittest.main()
