# filepath: d:\Blockchain\Lab01-Blockchain\tests\test_block.py
from src.block import build_block, verify_block
from src.crypto import generate_keypair
from src.state import make_tx

def test_block_build_verify():
    kp = generate_keypair()
    pk_map = {"P": kp.pk}
    tx = make_tx("P", "P/data", "v", kp.sk, kp.pk)
    blk = build_block("GENESIS", 1, [tx], "P", kp.sk, pk_map)
    assert verify_block(blk, pk_map)