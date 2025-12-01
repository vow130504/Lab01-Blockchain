# logger.py
import json
from pathlib import Path
from threading import Lock

# Đường dẫn file log (đổi lại nếu project bạn đang dùng tên khác)
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "runs.log"

_log_lock = Lock()

# --- Khởi tạo: đảm bảo mỗi lần chạy pytest là 1 file log mới ---

# Tạo thư mục logs/ nếu chưa có
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Truncate file (xóa nội dung cũ, tạo file rỗng)
# Mỗi process mới (mỗi lần bạn chạy pytest) sẽ thực hiện đoạn này đúng 1 lần.
LOG_FILE.write_text("", encoding="utf-8")

# --- Hàm ghi log dùng chung cho toàn bộ project ---

def log_event(**rec):
    """Ghi một event (một dict) ra file logs/runs.log dạng JSON mỗi dòng."""
    with _log_lock:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            json.dump(rec, f, sort_keys=True)
            f.write("\n")
