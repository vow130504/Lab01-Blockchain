# filepath: d:\Blockchain\Lab01-Blockchain\deterministic_check.py
from src.simulator import Simulator

def run():
    s1 = Simulator(6, seed=99)
    s1.run_until(5)
    log1 = s1.collect_logs()
    s2 = Simulator(6, seed=99)
    s2.run_until(5)
    log2 = s2.collect_logs()
    print("Logs identical:", log1 == log2)
    print("Finalized heights:", sorted(s1.vote_book.finalized.keys()))

if __name__ == "__main__":
    run()