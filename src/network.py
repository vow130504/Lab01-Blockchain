import random, heapq
from typing import Any, Callable, List, Dict

class NetworkEvent:
    def __init__(self, t, src, dst, etype, height, payload):
        self.t = t
        self.src = src
        self.dst = dst
        self.etype = etype
        self.height = height
        self.payload = payload

class UnreliableNetwork:
    def __init__(self, nodes: List[str], seed: int, drop_prob=0.05, dup_prob=0.05, max_delay=5):
        self.nodes = nodes
        self.rng = random.Random(seed)
        self.drop_prob = drop_prob
        self.dup_prob = dup_prob
        self.max_delay = max_delay
        self.time = 0
        self.pq = []  # (deliver_time, event)
        self.log: List[str] = []

    def broadcast(self, src: str, height: int, payload: Any):
        for dst in self.nodes:
            if dst == src: continue
            self._send(src, dst, height, payload)

    def _send(self, src, dst, height, payload):
        if self.rng.random() < self.drop_prob:
            self.log.append(f"{self.time}|DROP|{src}->{dst}|h={height}")
            return
        delay = self.rng.randint(0, self.max_delay)
        ev = NetworkEvent(self.time + delay, src, dst, "DELIVER", height, payload)
        heapq.heappush(self.pq, (ev.t, ev))
        self.log.append(f"{self.time}|SEND|{src}->{dst}|h={height}|d={delay}")
        if self.rng.random() < self.dup_prob:
            ev2 = NetworkEvent(self.time + delay + 1, src, dst, "DELIVER", height, payload)
            heapq.heappush(self.pq, (ev2.t, ev2))
            self.log.append(f"{self.time}|DUP|{src}->{dst}|h={height}")

    def step(self, handler: Callable[[NetworkEvent], None]):
        if not self.pq: 
            self.time += 1
            return
        t, ev = heapq.heappop(self.pq)
        self.time = t
        handler(ev)

    def idle(self):
        return not self.pq
