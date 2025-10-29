import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .snapshot_store import StateSnapshot

logger = logging.getLogger(__name__)


class SQLiteSnapshotStore:
    """SQLite快照存储实现"""
    
    def __init__(self, db_path: str = "history/snapshots.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS snapshots (
                        snapshot_id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        domain_state TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        snapshot_name TEXT,
                        metadata TEXT,
                        compressed_data BLOB,
                        size_bytes INTEGER
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_agent_id ON snapshots(agent_id)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON snapshots(timestamp)
                """)
                
                conn.commit()
            logger.debug(f"SQLite快照数据库初始化完成: {self.db_path}")
        except Exception as e:
            logger.error(f"初始化SQLite快照数据库失败: {e}")
            raise
    
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """保存快照到SQLite"""
        try:
            # 序列化状态
            serialized_state = json.dumps(snapshot.domain_state)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO snapshots 
                    (snapshot_id, agent_id, domain_state, timestamp, snapshot_name, 
                     metadata, compressed_data, size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.snapshot_id,
                    snapshot.agent_id,
                    serialized_state,
                    snapshot.timestamp.isoformat(),
                    snapshot.snapshot_name,
                    json.dumps(snapshot.metadata),
                    snapshot.compressed_data,
                    snapshot.size_bytes
                ))
                conn.commit()
            
            logger.debug(f"快照保存成功: {snapshot.snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存快照失败: {e}")
            return False
    
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """从SQLite加载快照"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT snapshot_id, agent_id, domain_state, timestamp, snapshot_name,
                           metadata, compressed_data, size_bytes
                    FROM snapshots WHERE snapshot_id = ?
                """, (snapshot_id,))
                
                row = cursor.fetchone()
                if row:
                    return StateSnapshot(
                        snapshot_id=row[0],
                        agent_id=row[1],
                        domain_state=json.loads(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        snapshot_name=row[4] or "",
                        metadata=json.loads(row[5]) if row[5] else {},
                        compressed_data=row[6],
                        size_bytes=row[7] or 0
                    )
        except Exception as e:
            logger.error(f"加载快照失败: {e}")
        
        return None
    
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定Agent的快照列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT snapshot_id, agent_id, domain_state, timestamp, snapshot_name,
                           metadata, compressed_data, size_bytes
                    FROM snapshots 
                    WHERE agent_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (agent_id, limit))
                
                snapshots = []
                for row in cursor.fetchall():
                    snapshot = StateSnapshot(
                        snapshot_id=row[0],
                        agent_id=row[1],
                        domain_state=json.loads(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        snapshot_name=row[4] or "",
                        metadata=json.loads(row[5]) if row[5] else {},
                        compressed_data=row[6],
                        size_bytes=row[7] or 0
                    )
                    snapshots.append(snapshot)
                
                return snapshots
                
        except Exception as e:
            logger.error(f"获取Agent快照列表失败: {e}")
            return []
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM snapshots WHERE snapshot_id = ?",
                    (snapshot_id,)
                )
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.debug(f"快照删除成功: {snapshot_id}")
                else:
                    logger.warning(f"快照不存在: {snapshot_id}")
                
                return deleted
                
        except Exception as e:
            logger.error(f"删除快照失败: {e}")
            return False
    
    def cleanup_old_snapshots(self, agent_id: str, max_snapshots: int = 50) -> int:
        """清理旧快照"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取所有快照ID，按时间排序
                cursor = conn.execute("""
                    SELECT snapshot_id FROM snapshots 
                    WHERE agent_id = ?
                    ORDER BY timestamp ASC
                """, (agent_id,))
                
                all_snapshot_ids = [row[0] for row in cursor.fetchall()]
                
                if len(all_snapshot_ids) <= max_snapshots:
                    return 0
                
                # 删除最旧的快照
                to_delete = all_snapshot_ids[:-max_snapshots]
                deleted_count = 0
                
                for snapshot_id in to_delete:
                    cursor = conn.execute(
                        "DELETE FROM snapshots WHERE snapshot_id = ?",
                        (snapshot_id,)
                    )
                    deleted_count += cursor.rowcount
                
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"清理了 {deleted_count} 个旧快照，agent_id: {agent_id}")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"清理旧快照失败: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 总快照数
                cursor = conn.execute("SELECT COUNT(*) FROM snapshots")
                total_count = cursor.fetchone()[0]
                
                # 按Agent分组统计
                cursor = conn.execute("""
                    SELECT agent_id, COUNT(*) 
                    FROM snapshots 
                    GROUP BY agent_id
                    ORDER BY COUNT(*) DESC
                """)
                agent_counts = dict(cursor.fetchall())
                
                # 数据库大小
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "total_snapshots": total_count,
                    "agent_counts": agent_counts,
                    "database_size_bytes": db_size,
                    "database_path": str(self.db_path)
                }
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}