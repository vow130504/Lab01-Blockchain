# filepath: d:\Blockchain\Lab01-Blockchain\tests\test_block.py
from src.block import build_block, verify_block
from src.crypto import generate_keypair
from src.state import make_tx

def test_block_build_verify():
    kp = generate_keypair()
    pk_map = {"P": kp.pk}
    tx = make_tx("P", "P/data", "v", 1, kp.sk, kp.pk)
    blk = build_block("GENESIS", 1, [tx], "P", kp.sk, pk_map)
    assert verify_block(blk, pk_map)

def test_block_reject_wrong_proposer_key():
    """Block bị ký bằng private key khác với public key trong pk_map → phải fail."""
    # kp1: key chính thức của proposer "P"
    kp1 = generate_keypair()
    # kp2: key giả dùng để ký header
    kp2 = generate_keypair()

    pk_map = {"P": kp1.pk}

    tx = make_tx("P", "P/data", "v", 1, kp1.sk, kp1.pk)

    # build_block dùng sk sai (kp2.sk)
    blk = build_block("GENESIS", 1, [tx], "P", kp2.sk, pk_map)

    # verify_block phải phát hiện chữ ký không khớp pk_map["P"]
    assert not verify_block(blk, pk_map)

def test_block_reject_tampered_header():
    """Block build đúng rồi nhưng header bị sửa sau khi ký → verify phải fail."""
    kp = generate_keypair()
    pk_map = {"P": kp.pk}

    tx = make_tx("P", "P/data", "v", 1, kp.sk, kp.pk)
    blk = build_block("GENESIS", 1, [tx], "P", kp.sk, pk_map)

    # Giả lập attacker sửa header sau khi block đã được ký
    blk.header.height = 2   # đổi height, làm chữ ký không còn khớp dữ liệu header

    assert not verify_block(blk, pk_map)
