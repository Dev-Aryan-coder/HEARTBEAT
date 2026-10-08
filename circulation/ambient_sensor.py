import os
import subprocess
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from storage.database import get_connection, _normalize_user_id
from cells.cell_model import BloodCell, CellType, CellStatus, MemoryTier, ContentType
from storage.chroma_client import get_chroma_client

logger = logging.getLogger("HEARTBEAT_AMBIENT_SENSOR")

class AmbientSensor:
    """
    Upgrade 4: Ambient Perception (Outside the Chat Box).
    Silently monitors the user's workspace, Git repository, and system environment.
    Automatically crystallizes code edits, git commits, and project milestones
    into subconscious memory without requiring manual chat input.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = workspace_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._last_git_commit = None
        self._last_git_status_hash = None
        self._last_modified_files = {}

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def probe_git_state(self) -> Optional[Dict[str, Any]]:
        """Probes git repository for branch, latest commit, and dirty status."""
        try:
            # Check if directory is a git repo
            branch_out = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if branch_out.returncode != 0:
                return None
            branch = branch_out.stdout.strip() or "main"

            commit_out = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%h|%s|%an|%cI"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            commit_hash, commit_msg, commit_author, commit_date = ("none", "no commits", "unknown", "")
            if commit_out.returncode == 0 and commit_out.stdout.strip():
                parts = commit_out.stdout.strip().split("|")
                if len(parts) >= 4:
                    commit_hash, commit_msg, commit_author, commit_date = parts[0], parts[1], parts[2], parts[3]

            status_out = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            modified_files = []
            if status_out.returncode == 0 and status_out.stdout.strip():
                for line in status_out.stdout.strip().split("\n"):
                    clean = line.strip()
                    if clean:
                        modified_files.append(clean)

            return {
                "branch": branch,
                "commit_hash": commit_hash,
                "commit_msg": commit_msg,
                "commit_author": commit_author,
                "modified_files": modified_files[:10],
                "modified_count": len(modified_files)
            }
        except Exception as e:
            logger.debug(f"[AMBIENT_SENSOR] Git probe error: {str(e)}")
            return None

    def record_ambient_event(
        self,
        event_type: str,
        summary: str,
        details: Dict[str, Any],
        user_id: str = "MASTER_USER"
    ) -> str:
        """
        Persists an ambient telemetry event into ambient_events table,
        creates an episodic BloodCell, and indexes it into Chroma vector store.
        """
        uid = _normalize_user_id(user_id)
        conn = get_connection()
        now = self._now_iso()
        event_id = str(uuid4())
        cell_id = str(uuid4())
        details_json = json.dumps(details)

        # 1. Create Ambient Memory Cell
        with conn:
            conn.execute("""
                INSERT INTO blood_cells (
                    cell_id, user_id, chat_id, message_id, session_id,
                    status, cell_type, memory_tier,
                    user_raw_content, user_content, summary,
                    importance_score, keywords, topic_id,
                    analysis_status, created_at, purified_at, last_activated_at
                ) VALUES (
                    ?, ?, 'AMBIENT_STREAM', ?, 'BACKGROUND_OBSERVER',
                    'active', 'purified', 'episodic',
                    ?, ?, ?,
                    6, ?, 'ambient_telemetry',
                    'purified', ?, ?, ?
                )
            """, (
                cell_id, uid, event_type.upper(),
                summary, summary, summary,
                json.dumps(["ambient", event_type, "telemetry"]),
                now, now, now
            ))

            # 2. Record telemetry entry
            conn.execute("""
                INSERT INTO ambient_events (
                    event_id, event_type, source, summary, details, timestamp, cell_id
                ) VALUES (?, ?, 'repo_watcher', ?, ?, ?, ?)
            """, (event_id, event_type, summary, details_json, now, cell_id))

        # 3. Vectorize in Chroma store for semantic retrieval
        try:
            chroma = get_chroma_client()
            chroma.add_cell(
                cell_id=cell_id,
                content=f"Ambient Event: {summary}",
                metadata={
                    "user_id": uid,
                    "memory_tier": "episodic",
                    "event_type": event_type,
                    "ambient": True
                }
            )
        except Exception as e:
            logger.debug(f"[AMBIENT_SENSOR] Chroma indexing notice: {str(e)}")

        logger.info(f"👁️ [AMBIENT PERCEPTION COMMITTED] {summary}")
        return event_id

    def poll_ambient_changes(self, user_id: str = "MASTER_USER") -> List[Dict[str, Any]]:
        """
        Checks for new git commits or major work changes and records them.
        Returns a list of captured events.
        """
        captured = []
        git_info = self.probe_git_state()
        if not git_info:
            return captured

        # 1. Detect New Git Commit
        current_commit = git_info.get("commit_hash")
        if current_commit and current_commit != "none":
            if self._last_git_commit is None:
                # First boot baseline
                self._last_git_commit = current_commit
            elif self._last_git_commit != current_commit:
                summary = f"User committed code: '{git_info['commit_msg']}' (branch: {git_info['branch']}, hash: {current_commit})"
                event_id = self.record_ambient_event(
                    event_type="git_commit",
                    summary=summary,
                    details=git_info,
                    user_id=user_id
                )
                captured.append({"event_id": event_id, "summary": summary, "type": "git_commit"})
                self._last_git_commit = current_commit

        # 2. Detect Modified Working Tree State
        status_hash = hash(tuple(git_info.get("modified_files", [])))
        if git_info.get("modified_count", 0) > 0 and status_hash != self._last_git_status_hash:
            if self._last_git_status_hash is not None:
                files_str = ", ".join(git_info["modified_files"][:5])
                summary = f"Workspace modifications detected across {git_info['modified_count']} files ({files_str})"
                event_id = self.record_ambient_event(
                    event_type="workspace_modified",
                    summary=summary,
                    details=git_info,
                    user_id=user_id
                )
                captured.append({"event_id": event_id, "summary": summary, "type": "workspace_modified"})
            self._last_git_status_hash = status_hash

        return captured

    async def start_background_watcher(self, interval_seconds: int = 45, user_id: str = "MASTER_USER"):
        """Continuous background watcher loop."""
        logger.info(f"👁️ AMBIENT SENSOR: Starting background observer daemon on '{self.workspace_path}' (interval: {interval_seconds}s)")
        while True:
            try:
                self.poll_ambient_changes(user_id=user_id)
            except Exception as e:
                logger.error(f"[AMBIENT_SENSOR] Watcher error: {str(e)}")
            await asyncio.sleep(interval_seconds)
