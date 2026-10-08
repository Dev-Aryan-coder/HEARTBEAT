import sqlite3
import logging
from typing import List, Tuple, Dict, Any
from datetime import datetime, timezone
from storage.database import get_connection

logger = logging.getLogger("HEARTBEAT_SYNAPTIC_NETWORK")

class SynapticNetwork:
    """
    Bi-directional Synaptic Reinforcement (Hebbian Learning).
    Rule: "Neurons that fire together, wire together".
    When two memory cells are retrieved and co-utilized in the same prompt context,
    the synaptic link between them is strengthened.
    """

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def reinforce_co_occurrence(cls, cell_ids: List[str], boost: float = 0.2) -> int:
        """
        Reinforces synaptic connections between all unique pairs of cell_ids.
        Pairs are normalized (cell_a < cell_b) to represent an undirected edge.
        Returns the number of reinforced synapses.
        """
        unique_ids = sorted(list(set(cid.strip() for cid in cell_ids if cid and cid.strip())))
        if len(unique_ids) < 2:
            return 0

        conn = get_connection()
        now = cls._now_iso()
        links_reinforced = 0

        with conn:
            cursor = conn.cursor()
            for i in range(len(unique_ids)):
                for j in range(i + 1, len(unique_ids)):
                    cell_a = unique_ids[i]
                    cell_b = unique_ids[j]

                    cursor.execute("""
                        INSERT INTO synaptic_links (cell_id_a, cell_id_b, synaptic_weight, co_fired_count, last_fired_at)
                        VALUES (?, ?, 1.0 + ?, 1, ?)
                        ON CONFLICT(cell_id_a, cell_id_b) DO UPDATE SET
                            synaptic_weight = synaptic_weight + ?,
                            co_fired_count = co_fired_count + 1,
                            last_fired_at = ?
                    """, (cell_a, cell_b, boost, now, boost, now))
                    links_reinforced += 1

        logger.info(f"[SYNAPTIC_NETWORK] Reinforced {links_reinforced} synapses across {len(unique_ids)} co-fired cells.")
        return links_reinforced

    @classmethod
    def get_associated_cells(
        cls,
        seed_cell_ids: List[str],
        top_k: int = 5,
        min_weight: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Associative Priming:
        Given active cells in context, finds 1-hop synaptic neighbors that have high co-occurrence weight.
        Excludes the seed cells themselves.
        """
        if not seed_cell_ids:
            return []

        seed_set = set(cid.strip() for cid in seed_cell_ids)
        conn = get_connection()
        cursor = conn.cursor()

        # Query all edges touching any seed cell
        placeholders = ",".join("?" for _ in seed_set)
        cursor.execute(f"""
            SELECT cell_id_a, cell_id_b, synaptic_weight, co_fired_count
            FROM synaptic_links
            WHERE (cell_id_a IN ({placeholders}) OR cell_id_b IN ({placeholders}))
              AND synaptic_weight >= ?
            ORDER BY synaptic_weight DESC
        """, list(seed_set) + list(seed_set) + [min_weight])

        rows = cursor.fetchall()
        neighbor_weights: Dict[str, float] = {}
        neighbor_fire_counts: Dict[str, int] = {}

        for row in rows:
            ca, cb, weight, fired_cnt = row["cell_id_a"], row["cell_id_b"], row["synaptic_weight"], row["co_fired_count"]
            neighbor = cb if ca in seed_set else ca
            if neighbor not in seed_set:
                neighbor_weights[neighbor] = neighbor_weights.get(neighbor, 0.0) + weight
                neighbor_fire_counts[neighbor] = neighbor_fire_counts.get(neighbor, 0) + fired_cnt

        # Sort by total associative weight
        sorted_neighbors = sorted(neighbor_weights.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            {
                "cell_id": nid,
                "synaptic_weight": round(w, 2),
                "co_fired_count": neighbor_fire_counts.get(nid, 1)
            }
            for nid, w in sorted_neighbors
        ]

    @classmethod
    def apply_metabolic_decay(cls, decay_rate: float = 0.05, prune_below: float = 0.5) -> int:
        """
        Metabolic pruning: weakly connected or dormant synapses gradually decay.
        """
        conn = get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE synaptic_links
                SET synaptic_weight = MAX(0.0, synaptic_weight - ?)
            """, (decay_rate,))
            cursor.execute("""
                DELETE FROM synaptic_links
                WHERE synaptic_weight < ?
            """, (prune_below,))
            pruned = cursor.rowcount
        logger.info(f"[SYNAPTIC_NETWORK] Decayed synapses. Pruned {pruned} weak traces below {prune_below}.")
        return pruned
