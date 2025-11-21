# filepath: d:\Blockchain\Lab01-Blockchain\tests\test_determinism.py
from src.simulator import Simulator

def test_deterministic_logs():
    s1 = Simulator(4, seed=42)
    s1.run_until(3)
    log1 = s1.collect_logs()
    s2 = Simulator(4, seed=42)
    s2.run_until(3)
    log2 = s2.collect_logs()
    assert log1 == log2