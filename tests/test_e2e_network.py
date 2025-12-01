# filepath: tests/test_e2e_network.py

from src.simulator import Simulator

def _collect_chains(sim: Simulator):
    """
    Helper: lấy chuỗi (height -> block_hash) của từng node.
    Trả về dict: node_id -> {height: block_hash}
    """
    chains = {}
    for nid, node in sim.nodes.items():
        height_to_hash = {le.height: le.block_hash for le in node.ledger}
        chains[nid] = height_to_hash
    return chains


def _assert_no_fork_safety_only(chains):
    """
    Safety-only:
    - Với mọi height h:
      nếu có >= 2 node cùng có block ở height đó,
      thì tất cả phải có cùng block_hash.
    - Không yêu cầu mọi height đều được finalize.
    """
    # Tập tất cả height đã thấy ở bất kỳ node nào
    all_heights = set()
    for hmap in chains.values():
        all_heights.update(hmap.keys())

    for h in sorted(all_heights):
        hashes = set()
        for nid, hmap in chains.items():
            if h in hmap:
                hashes.add(hmap[h])
        # Nếu có từ 2 hash trở lên ở cùng height => fork
        assert len(hashes) <= 1, f"Fork detected at height={h}: hashes={hashes}"

def test_e2e_no_fork_under_default_network():
    sim = Simulator(n_nodes=4, seed=123)
    target_height = 3

    sim.run_until(target_height)

    chains = _collect_chains(sim)
    _assert_no_fork_safety_only(chains)

def test_e2e_no_fork_under_harsh_network():
    sim = Simulator(n_nodes=4, seed=999)

    # Làm mạng "xấu" hơn: tăng drop, dup, delay
    sim.network.drop_prob = 0.25
    sim.network.dup_prob = 0.35
    sim.network.delay_min = 0
    sim.network.delay_max = 15

    target_height = 3
    sim.run_until(target_height)

    chains = _collect_chains(sim)
    _assert_no_fork_safety_only(chains)


def _extract_chain_for_node(sim: Simulator, node_id: str):
    """
    Helper: lấy chuỗi (height, block_hash) của một node, sort theo height
    """
    node = sim.nodes[node_id]
    entries = sorted(node.ledger, key=lambda le: le.height)
    return [(le.height, le.block_hash) for le in entries]


def test_e2e_ledger_deterministic_across_runs():
    """
    E2E: Với cùng seed & cấu hình network,
    ledger của cùng một node (ví dụ N0) phải deterministic (giống nhau 100%).
    """
    target_height = 3

    sim1 = Simulator(n_nodes=4, seed=42)
    sim1.run_until(target_height)
    chain1 = _extract_chain_for_node(sim1, "N0")

    sim2 = Simulator(n_nodes=4, seed=42)
    sim2.run_until(target_height)
    chain2 = _extract_chain_for_node(sim2, "N0")

    assert chain1 == chain2
