# filepath: deterministic_check.py

from pathlib import Path
from src.simulator import Simulator
LOG_PATH = Path("logs") / "runs.log"


def run_one(seed: int = 99, target_height: int = 5) -> bytes:
    # Xóa file log cũ (nếu có) để đảm bảo log chỉ chứa run hiện tại
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    # Tạo simulator và chạy tới height target_height
    sim = Simulator(6, seed=seed)
    sim.run_until(target_height)

    # Đọc lại toàn bộ file log dưới dạng bytes
    # (so sánh byte-identical cho đúng yêu cầu)
    return LOG_PATH.read_bytes()


def run():
    # Chạy 2 lần với cùng tham số (seed, height)
    log1 = run_one(seed=99, target_height=5)
    log2 = run_one(seed=99, target_height=5)

    # So sánh kích thước + nội dung
    print("Log1 size:", len(log1))
    print("Log2 size:", len(log2))
    print("Logs identical (byte-by-byte):", log1 == log2)

    if log1 != log2:
        print("\nLogs differ! Showing first differing byte index:")
        max_len = min(len(log1), len(log2))
        diff_index = None
        for i in range(max_len):
            if log1[i] != log2[i]:
                diff_index = i
                break
        if diff_index is not None:
            print("First difference at byte index:", diff_index)
        else:
            print("Lengths differ but prefixes are identical.")


if __name__ == "__main__":
    run()
