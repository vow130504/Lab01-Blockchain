from collections import defaultdict
from typing import Dict, List
from .types import Vote, FinalizationResult
from .crypto import sign, verify, CTX_VOTE
from .logger import log_event

class VoteBook:
    def __init__(self, validators: List[str]):
        self.validators = validators
        self.prevotes: Dict[int, Dict[str, set]] = defaultdict(lambda: defaultdict(set))  # height -> block_hash -> validators
        self.precommits: Dict[int, Dict[str, set]] = defaultdict(lambda: defaultdict(set))
        self.finalized: Dict[int, str] = {}

    def majority(self) -> int:
        # Strict majority
        return (2 * len(self.validators)) // 3 + 1

    def add_vote(self, v: Vote) -> FinalizationResult:
        log_event(
            component="consensus",
            event=v.phase,   # "PREVOTE" or "PRECOMMIT"
            validator=v.validator,
            height=v.height,
            block_hash=v.block_hash,
        )
        target = self.prevotes if v.phase == "PREVOTE" else self.precommits
        target[v.height][v.block_hash].add(v.validator)
        if v.phase == "PRECOMMIT":
            if len(target[v.height][v.block_hash]) >= self.majority():
                # Safety: ensure no conflicting finalized height
                if v.height in self.finalized and self.finalized[v.height] != v.block_hash:
                    log_event(
                        component="consensus",
                        event="FINALIZE_CONFLICT",
                        validator=v.validator,
                        height=v.height,
                        block_hash=v.block_hash,
                        existing_block=self.finalized[v.height],
                    )
                    return FinalizationResult(v.height, v.block_hash, False, "Conflicting finalization attempt")
                self.finalized[v.height] = v.block_hash
                log_event(
                    component="consensus",
                    event="FINALIZE",
                    height=v.height,
                    block_hash=v.block_hash,
                    validators=list(target[v.height][v.block_hash]),
                )
                return FinalizationResult(v.height, v.block_hash, True, "")
        return FinalizationResult(v.height, v.block_hash, False, "")

def make_vote(validator: str, height: int, block_hash: str, phase: str, sk) -> Vote:
    fields = (validator, str(height), block_hash, phase)
    sig = sign(CTX_VOTE, fields, sk).hex()
    #optional logging
    log_event(
        component="consensus",
        event="MAKE_VOTE",
        validator=validator,
        height=height,
        block_hash=block_hash,
        phase=phase,
    )
    return Vote(validator=validator, height=height, block_hash=block_hash, phase=phase, signature=sig)

def verify_vote(v: Vote, pk_map: Dict[str, bytes]) -> bool:
    if v.validator not in pk_map: 
        log_event(
            component="consensus",
            event="VOTE_REJECT",
            reason="unknown_validator",
            validator=v.validator,
            height=v.height,
            block_hash=v.block_hash,
            phase=v.phase,
        )
        return False
    fields = (v.validator, str(v.height), v.block_hash, v.phase)
    ok = verify(CTX_VOTE, fields, pk_map[v.validator], bytes.fromhex(v.signature))
    if not ok:
        log_event(
            component="consensus",
            event="VOTE_REJECT",
            reason="bad_signature",
            validator=v.validator,
            height=v.height,
            block_hash=v.block_hash,
            phase=v.phase,
        )
    else:
        log_event(
            component="consensus",
            event="VOTE_ACCEPT",
            validator=v.validator,
            height=v.height,
            block_hash=v.block_hash,
            phase=v.phase,
        )

    return ok
