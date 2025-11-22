from src.crypto import generate_keypair, sign, verify, CTX_TX, CTX_VOTE, encode_kv_state
def test_context_separation():
    kp = generate_keypair()
    fields = ("a","b")
    sig_tx = sign(CTX_TX, fields, kp.sk)
    assert verify(CTX_TX, fields, kp.pk, sig_tx)
    assert not verify(CTX_VOTE, fields, kp.pk, sig_tx)

def test_signature_validity():
    kp = generate_keypair()
    fields = ("x","y","z")
    sig = sign(CTX_VOTE, fields, kp.sk)
    assert verify(CTX_VOTE, fields, kp.pk, sig)


def test_deterministic_encoding():
    # Test map order
    state1 = {"a": "1", "b": "2"}
    state2 = {"b": "2", "a": "1"} # Thứ tự key khác nhau
    assert encode_kv_state(state1) == encode_kv_state(state2)

    # Test hash consistency (Output cụ thể)
    # Chạy 1 lần, lấy chuỗi hash kết quả, hardcode vào đây để đảm bảo 
    # sau này không ai sửa code làm thay đổi logic hashing.
    fields = ("test", 123)
    # assert sha256(encode_fields(fields)).hex() == "hash_mong_doi_o_day"