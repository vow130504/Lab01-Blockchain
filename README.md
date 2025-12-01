// filepath: d:\Blockchain\Lab01-Blockchain\README.md
# Lab01 Minimal Blockchain

Build & Test:
1. Install deps (optional): py -m pip install pynacl
2. Install pytest: py -m pip install pytest
3. Run unit/e2e tests: py run_test.py
4. Determinism check: py deterministic_check.py

Structure:
- src/: Core blockchain modules (crypto, state, block, consensus, network, node, simulator)
- tests/: Unit tests, determinism tests, and E2E network tests
- run_test.py: Unified test runner (wrapper around pytest)
- deterministic_check.py: Script verifying log determinism (runs two identical simulations and checks byte-identical logs)

Notes:
- If pynacl is not installed, the system falls back to a mock signature scheme (acceptable only for testing or educational use).
- All signature operations use domain-separated contexts (CTX_TX, CTX_VOTE, …) to prevent cross-type signature replay.
- Consensus uses two-phase majority (Prevote → Precommit) ensuring safety / no forks under deterministic execution.
- The network layer introduces seeded random delay/drop/duplicate, making behavior fully deterministic when the same seed is used.
- The logging subsystem auto-clears the logs/ folder on each run to guarantee reproducible output.

Extend:
- Add a transaction mempool and maintain state continuity across blocks.
- Persist logs in the logs/ folder for submissions or long-run analysis.
- Add block propagation metrics, Byzantine validator tests, or network adversary models.
- Add real cryptographic signatures by requiring PyNaCl for production-grade correctness.