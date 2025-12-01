import random, heapq, json
from typing import List, Dict, Tuple, Any
from collections import defaultdict
import copy
from .logger import log_event

class Message:
    def __init__(self, msg_id, kind, height, body):
        self.msg_id = msg_id
        self.kind = kind
        self.height = height
        self.body = body  

class NetworkEvent:
    def __init__(self, t, src, dst, msg: Message):
        self.t = t
        self.src = src
        self.dst = dst
        self.msg = msg
    
    def __lt__(self, other):
        """Enable comparison for heapq - compare by time, then by src/dst for determinism"""
        if self.t != other.t:
            return self.t < other.t
        # Secondary comparison for determinism when times are equal
        return (self.src, self.dst) < (other.src, other.dst)

class UnreliableNetwork:
    def __init__(self, nodes: List[str], seed: int,
                 drop_prob=0.05, dup_prob=0.05,
                 delay_min=0, delay_max=5,
                 rate_per_sec=50, bucket_cap=20,
                 block_duration=10):

        self.nodes = nodes
        self.rng = random.Random(seed)
        self.drop_prob = drop_prob
        self.dup_prob = dup_prob
        self.delay_min = delay_min
        self.delay_max = delay_max

        self.time = 0
        self.seq = 0
        self.pq = []  # (t, seq, ev)

        # header-before-body
        self.accepted_headers = defaultdict(set)

        # rate limiting
        self.rate = rate_per_sec
        self.capacity = bucket_cap
        self.tokens = {(src, dst): self.capacity
                       for src in nodes for dst in nodes if src != dst}
        self.last_refill = 0

        # temporary block for overactive peers
        self.block_duration = block_duration
        self.blocked_links: Dict[Tuple[str, str], int] = {}  # (src,dst) -> unblock_time

        # NEW: track last height per link
        self.last_height: Dict[Tuple[str,str], int] = {}

        # deterministic log
        self.log: List[str] = []

#    def log_event(self, **rec):
#       rec["time"] = self.time
#      self.log.append(json.dumps(rec, sort_keys=True))

    def _refill_tokens(self):
        delta = self.time - self.last_refill
        if delta > 0:
            for k in self.tokens:
                self.tokens[k] = min(self.capacity,
                                     self.tokens[k] + delta * (self.rate/1000))
            self.last_refill = self.time

    def broadcast(self, src: str, msg: Message):
        for dst in self.nodes:
            if dst == src: continue
            self.send(src, dst, msg)

    def send(self, src, dst, msg: Message):
        # record last height
        self.last_height[(src, dst)] = msg.height

        # check if blocked
        unblock_time = self.blocked_links.get((src, dst), 0)
        if self.time < unblock_time:
            log_event(
                component="network",
                event="BLOCK_DROP",
                time=self.time,
                src=src,
                dst=dst,
                msg_id=msg.msg_id,
                unblock_time=unblock_time,
                height=msg.height,
            )
            return

        # rate limit
        self._refill_tokens()
        key = (src, dst)
        if self.tokens[key] < 1:
            # block temporaily
            self.blocked_links[(src, dst)] = self.time + self.block_duration
            log_event(
                component="network",
                event="BLOCK",
                time=self.time,
                src=src,
                dst=dst,
                msg_id=msg.msg_id,
                duration=self.block_duration,
                height=msg.height,
            )
            return
        self.tokens[key] -= 1

        # drop
        if self.rng.random() < self.drop_prob:
            log_event(
                component="network",
                event="DROP",
                time=self.time,
                src=src,
                dst=dst,
                msg_id=msg.msg_id,
                height=msg.height,
            )
            return

        # schedule deliver
        delay = self.rng.randint(self.delay_min, self.delay_max)
        msg_clone = copy.deepcopy(msg)
        ev = NetworkEvent(self.time + delay, src, dst, msg_clone)
        self.seq += 1
        heapq.heappush(self.pq, (ev.t, self.seq, ev))
        log_event(
            component="network",
            event="SEND",
            time=self.time,
            src=src,
            dst=dst,
            msg_id=msg.msg_id,
            height=msg.height,
            delay=delay,
        )

        # duplicate
        if self.rng.random() < self.dup_prob:
            ev2 = NetworkEvent(ev.t + 1, src, dst, copy.deepcopy(msg_clone))
            self.seq += 1
            heapq.heappush(self.pq, (ev2.t, self.seq, ev2))
            log_event(
                component="network",
                event="DUP",
                time=self.time,
                src=src,
                dst=dst,
                msg_id=msg.msg_id,
                height=msg.height,
            )

    def step(self, handler):
        if not self.pq:
            self.time += 1
            return

        t, seq, ev = heapq.heappop(self.pq)
        self.time = t

        # HEADER → BODY enforcement
        if ev.msg.kind == "BODY":
            block_hash = ev.msg.body.get("block_hash")
            if block_hash not in self.accepted_headers[ev.dst]:
                # assign deadline if not yet
                if not hasattr(ev, "deadline"):
                    ev.deadline = self.time + 30  # MAX_WAIT_FOR_HEADER

                # expired
                if self.time >= ev.deadline:
                    log_event(
                        component="network",
                        event="BODY_DROP_EXPIRED_HEADER",
                        time=self.time,
                        dst=ev.dst,
                        msg_id=ev.msg.msg_id,
                        block_hash=block_hash,
                        height=ev.msg.height,
                    )
                    return

                # defer body
                new_t = self.time + 2
                ev2 = NetworkEvent(new_t, ev.src, ev.dst, copy.deepcopy(ev.msg))
                ev2.deadline = ev.deadline
                self.seq += 1
                heapq.heappush(self.pq, (new_t, self.seq, ev2))

                log_event(
                    component="network",
                    event="DEFER_BODY",
                    time=self.time,
                    dst=ev.dst,
                    msg_id=ev.msg.msg_id,
                    block_hash=block_hash,
                    height=ev.msg.height,
                    next_try=new_t,
                    deadline=ev2.deadline,
                )
                return

        # deliver
        log_event(
            component="network",
            event="DELIVER",
            time=self.time,
            src=ev.src,
            dst=ev.dst,
            msg_id=ev.msg.msg_id,
            kind=ev.msg.kind,
            height=ev.msg.height,
        )
        # mark accepted header
        if ev.msg.kind == "HEADER":
            block_hash = ev.msg.body.get("block_hash")
            if block_hash:
                self.accepted_headers[ev.dst].add(block_hash)

        # unblock peers if needed
        to_unblock = []
        for (s,d), unblock_time in self.blocked_links.items():
            if self.time >= unblock_time:
                to_unblock.append((s,d))

        for k in to_unblock:
            del self.blocked_links[k]
            # NEW: use last known height per link
            height_val = self.last_height.get(k, None)
            self.log_event(event="UNBLOCK", src=k[0], dst=k[1], height=height_val)

        handler(ev.msg)
        return True

    def idle(self):
        return not self.pq
