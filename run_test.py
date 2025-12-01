# run_test.py
import sys
import pytest

def main():
    # -q cho output gọn
    sys.exit(pytest.main(["-q"]))

if __name__ == "__main__":
    main()
