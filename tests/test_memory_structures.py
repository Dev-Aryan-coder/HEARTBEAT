import pytest
import time
from cells.memory_structures import (
    PrefixTrie, LRUMemoryCache, MetabolicPriorityQueue,
    MemoryBloomFilter, TaskExecutionDAG
)

def test_prefix_trie():
    trie = PrefixTrie()
    trie.insert("python", "cell_01")
    trie.insert("pytorch", "cell_02")
    trie.insert("database", "cell_03")

    py_hits = trie.search_prefix("py")
    assert "cell_01" in py_hits
    assert "cell_02" in py_hits
    assert "cell_03" not in py_hits

    data_hits = trie.search_prefix("data")
    assert "cell_03" in data_hits
    assert len(data_hits) == 1

def test_lru_memory_cache():
    cache = LRUMemoryCache(capacity=3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)

    assert cache.get("a") == 1  # Access "a", making "b" the least recently used
    cache.put("d", 4)           # "b" should be evicted

    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4

def test_metabolic_priority_queue():
    pq = MetabolicPriorityQueue()
    now = time.time()
    pq.push("cell_cold", importance=2, activations=0, created_ts=now - 86400, data={"title": "cold"})
    pq.push("cell_hot", importance=10, activations=15, created_ts=now, data={"title": "hot"})
    pq.push("cell_medium", importance=6, activations=2, created_ts=now - 3600, data={"title": "medium"})

    top = pq.get_top_k(k=2)
    assert len(top) == 2
    assert top[0][0] == "cell_hot"
    assert top[1][0] == "cell_medium"

def test_memory_bloom_filter():
    bf = MemoryBloomFilter(size_bits=2048)
    bf.add("jarvis_status.txt")
    bf.add("Master Aryan")

    assert bf.contains("jarvis_status.txt") is True
    assert bf.contains("Master Aryan") is True
    assert bf.contains("non_existent_secret_file_999.xyz") is False

def test_task_execution_dag():
    dag = TaskExecutionDAG()
    # Task 1: Check time (no dependencies)
    dag.add_task("task_time", "get_current_time", {})
    # Task 2: Check vitals (no dependencies)
    dag.add_task("task_vitals", "get_system_vitals", {})
    # Task 3: Write report (depends on time and vitals)
    dag.add_task("task_report", "write_workspace_file", {"filepath": "report.txt"}, depends_on=["task_time", "task_vitals"])

    batches = dag.topological_sort()
    assert len(batches) == 2
    # Batch 0: independent tasks can run in parallel
    assert set(batches[0]) == {"task_time", "task_vitals"}
    # Batch 1: dependent task
    assert batches[1] == ["task_report"]
