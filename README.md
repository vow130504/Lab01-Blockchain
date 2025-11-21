// filepath: d:\Blockchain\Lab01-Blockchain\README.md
# Lab01 Minimal Blockchain

Build & Test:
1. Install deps (optional): pip install pynacl
2. Run unit/e2e tests: python run_tests.py
3. Determinism check: python deterministic_check.py

Structure:
- src/: core modules (crypto, state, block, consensus, network, node, simulator)
- tests/: unit and deterministic tests
- run_tests.py: single entry
- deterministic_check.py: log equality demo

Notes:
- Signatures fall back to mock if pynacl not installed (acceptable only for testing).
- All message types use domain-separated contexts.
- Consensus: two-phase majority finalization; safety enforced.
- Network: random delay, drop, duplicate with deterministic seed.

Extend:
- Add transaction pools and state continuity across blocks.
- Add logging persistence (logs/ folder) for submission.