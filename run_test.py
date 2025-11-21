# filepath: d:\Blockchain\Lab01-Blockchain\run_tests.py
import os, sys, unittest

def main():
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests")
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()