"""
=============================================================================
HEARTBEAT BIOLOGICAL DATA STRUCTURES (THE COMPUTATIONAL BEDROCK)
=============================================================================
Implements classic, high-performance data structures to optimize SPARK's
memory retrieval, cognitive planning, and hardware actuation:

1. PrefixTrie (Trie / Prefix Tree)
   - Fast O(k) keyword and entity prefix routing.
2. LRUMemoryCache (Doubly Linked List + Hash Map)
   - O(1) working memory (Bloodstream) cache with strict capacity eviction.
3. MetabolicPriorityQueue (Binary Max-Heap via heapq)
   - O(log N) biological recency and metabolic importance ranking.
4. MemoryBloomFilter (Bit Array + Double Hashing)
   - O(1) probabilistic set membership test to eliminate redundant disk queries.
5. TaskExecutionDAG (Directed Acyclic Graph with Topological Sort)
   - Multi-step cognitive task planning for autonomous tool execution.
=============================================================================
"""

import time
import math
import heapq
from typing import Dict, Any, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# 1. TRIE (PREFIX TREE) FOR SUB-MILLISECOND KEYWORD/TOPIC ROUTING
# ---------------------------------------------------------------------------
class TrieNode:
    __slots__ = ("children", "cell_ids", "is_end")
    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.cell_ids: Set[str] = set()
        self.is_end: bool = False

class PrefixTrie:
    """Prefix Tree for instant O(k) retrieval of cells indexed by keywords."""
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, cell_id: str) -> None:
        """Inserts a keyword or phrase into the Trie linked to a cell_id."""
        if not word:
            return
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.cell_ids.add(cell_id)
        node.is_end = True

    def search_prefix(self, prefix: str) -> Set[str]:
        """Finds all cell_ids associated with keywords starting with prefix."""
        if not prefix:
            return set()
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return set()
            node = node.children[char]
        return set(node.cell_ids)


# ---------------------------------------------------------------------------
# 2. LRU MEMORY CACHE (DOUBLY LINKED LIST + HASH MAP)
# ---------------------------------------------------------------------------
class DListNode:
    __slots__ = ("key", "val", "prev", "next")
    def __init__(self, key: str = "", val: Any = None):
        self.key: str = key
        self.val: Any = val
        self.prev: Optional[DListNode] = None
        self.next: Optional[DListNode] = None

class LRUMemoryCache:
    """
    O(1) Working Memory (Bloodstream) Cache using Doubly Linked List + Hash Map.
    Provides strict bounds on RAM while keeping the hottest memories instantly accessible.
    """
    def __init__(self, capacity: int = 64):
        self.capacity: int = capacity
        self.cache: Dict[str, DListNode] = {}
        self.head = DListNode()  # Dummy head
        self.tail = DListNode()  # Dummy tail
        self.head.next = self.tail
        self.tail.prev = self.head

    def _add_node_to_head(self, node: DListNode):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: DListNode):
        prev_node = node.prev
        next_node = node.next
        if prev_node:
            prev_node.next = next_node
        if next_node:
            next_node.prev = prev_node

    def _move_to_head(self, node: DListNode):
        self._remove_node(node)
        self._add_node_to_head(node)

    def _pop_tail(self) -> Optional[DListNode]:
        res = self.tail.prev
        if res and res != self.head:
            self._remove_node(res)
            return res
        return None

    def get(self, key: str) -> Optional[Any]:
        """O(1) retrieve and promote to most recently used."""
        if key in self.cache:
            node = self.cache[key]
            self._move_to_head(node)
            return node.val
        return None

    def put(self, key: str, val: Any) -> None:
        """O(1) insert or update with automatic eviction of coldest entry."""
        if key in self.cache:
            node = self.cache[key]
            node.val = val
            self._move_to_head(node)
        else:
            new_node = DListNode(key, val)
            self.cache[key] = new_node
            self._add_node_to_head(new_node)
            if len(self.cache) > self.capacity:
                tail = self._pop_tail()
                if tail and tail.key in self.cache:
                    del self.cache[tail.key]

    def items(self) -> List[Tuple[str, Any]]:
        """Returns items ordered from newest to oldest."""
        result = []
        curr = self.head.next
        while curr and curr != self.tail:
            result.append((curr.key, curr.val))
            curr = curr.next
        return result


# ---------------------------------------------------------------------------
# 3. METABOLIC PRIORITY QUEUE (BINARY MAX-HEAP VIA HEAPQ)
# ---------------------------------------------------------------------------
class MetabolicPriorityQueue:
    """
    Binary Max-Heap for biological memory rank calculation.
    Priority formula: importance_score * ln(activations + 1) + recency_bonus
    """
    def __init__(self):
        self._heap: List[Tuple[float, int, str, Dict[str, Any]]] = []
        self._counter: int = 0  # Tie-breaker for heap stability

    def push(self, cell_id: str, importance: int, activations: int, created_ts: float, data: Dict[str, Any]):
        age_hours = max(0.1, (time.time() - created_ts) / 3600.0)
        recency_bonus = 10.0 / math.sqrt(age_hours)
        act_bonus = math.log(activations + 1.0)
        score = (float(importance) * 2.0) + (act_bonus * 1.5) + recency_bonus

        # heapq is a min-heap by default; store negative score for max-heap behavior
        self._counter += 1
        heapq.heappush(self._heap, (-score, self._counter, cell_id, data))

    def pop_top(self) -> Optional[Tuple[str, Dict[str, Any], float]]:
        """Pops highest vitality cell in O(log N)."""
        if not self._heap:
            return None
        neg_score, _, cell_id, data = heapq.heappop(self._heap)
        return cell_id, data, -neg_score

    def get_top_k(self, k: int = 5) -> List[Tuple[str, Dict[str, Any], float]]:
        """Extracts top K elements without destroying the entire heap."""
        top_k = []
        temp = []
        for _ in range(min(k, len(self._heap))):
            neg_score, counter, cell_id, data = heapq.heappop(self._heap)
            top_k.append((cell_id, data, -neg_score))
            temp.append((neg_score, counter, cell_id, data))
        for item in temp:
            heapq.heappush(self._heap, item)
        return top_k


# ---------------------------------------------------------------------------
# 4. MEMORY BLOOM FILTER (PROBABILISTIC SET MEMBERSHIP)
# ---------------------------------------------------------------------------
class MemoryBloomFilter:
    """
    Probabilistic O(1) set membership test using a 4096-bit vector and 4 hash functions.
    Instantly confirms if an entity has NEVER been stored, saving unnecessary vector/SQL calls.
    """
    def __init__(self, size_bits: int = 4096):
        self.size: int = size_bits
        self.bit_array: int = 0  # Python arbitrary-precision integer bitmask

    def _hashes(self, item: str) -> List[int]:
        s = item.lower().strip()
        h1 = hash(s)
        h2 = hash(s[::-1])
        return [
            abs(h1) % self.size,
            abs(h2) % self.size,
            abs(h1 ^ 0x55555555) % self.size,
            abs(h2 ^ 0xAAAAAAAA) % self.size
        ]

    def add(self, item: str) -> None:
        """Adds a concept/word into the bloom filter."""
        for bit_idx in self._hashes(item):
            self.bit_array |= (1 << bit_idx)

    def contains(self, item: str) -> bool:
        """
        Returns False if the item is GUARANTEED to NOT be present.
        Returns True if the item MIGHT be present.
        """
        for bit_idx in self._hashes(item):
            if not (self.bit_array & (1 << bit_idx)):
                return False
        return True


# ---------------------------------------------------------------------------
# 5. TASK EXECUTION DAG (DIRECTED ACYCLIC GRAPH & TOPOLOGICAL SORT)
# ---------------------------------------------------------------------------
class TaskNode:
    def __init__(self, task_id: str, tool_name: str, args: Dict[str, Any]):
        self.task_id = task_id
        self.tool_name = tool_name
        self.args = args
        self.dependencies: Set[str] = set()

class TaskExecutionDAG:
    """
    Directed Acyclic Graph for structuring multi-step autonomous cognitive plans.
    Enables parallel dispatch of independent tool executions and strictly ordered chains.
    """
    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.edges: Dict[str, Set[str]] = {}  # node -> set of successors

    def add_task(self, task_id: str, tool_name: str, args: Dict[str, Any], depends_on: List[str] = None):
        node = TaskNode(task_id, tool_name, args)
        if depends_on:
            node.dependencies = set(depends_on)
        self.nodes[task_id] = node
        if task_id not in self.edges:
            self.edges[task_id] = set()
        if depends_on:
            for dep in depends_on:
                if dep not in self.edges:
                    self.edges[dep] = set()
                self.edges[dep].add(task_id)

    def topological_sort(self) -> List[List[str]]:
        """
        Returns execution batches via Kahn's Algorithm.
        Tasks within the same batch can execute concurrently.
        """
        in_degree = {task_id: len(node.dependencies) for task_id, node in self.nodes.items()}
        batches = []

        while True:
            current_batch = [task_id for task_id, deg in in_degree.items() if deg == 0]
            if not current_batch:
                break
            batches.append(current_batch)
            for task_id in current_batch:
                del in_degree[task_id]
                for successor in self.edges.get(task_id, set()):
                    if successor in in_degree:
                        in_degree[successor] -= 1

        return batches
