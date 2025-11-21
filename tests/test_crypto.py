from src.crypto import generate_keypair, sign, verify, CTX_TX, CTX_VOTE

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
