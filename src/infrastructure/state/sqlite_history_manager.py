import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .interfaces import IStateHistoryManager, StateHistoryEntry


logger = logging.getLogger(__name__)


class SQLiteHistoryManager(IStateHistoryManager):
    """SQLite历史管理器实现"""
    
    def __init__(self, db_path: str = "history/state_history.db", max_history_size: int = 1000):
        self.db_path = Path(db_path)
        self.max_history_size = max_history_size
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self._init_database()
    
    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn
    
    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = self._get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_history (
                    history_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    state_diff TEXT,
                    metadata TEXT,
                    compressed_diff BLOB
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_agent_id ON state_history(agent_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_timestamp ON state_history(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_action ON state_history(action)
            """)
            
            conn.commit()
            logger.debug(f"SQLite历史数据库初始化完成: {self.db_path}")
        except Exception as e:
            logger.error(f"初始化SQLite历史数据库失败: {e}")
            raise
    
    def record_state_change(self, agent_id: str, old_state: Dict[str, Any], 
                          new_state: Dict[str, Any], action: str) -> str:
        """记录状态变化到SQLite"""
        try:
            # 计算状态差异
            state_diff = self._calculate_state_diff(old_state, new_state)
            
            # 创建历史记录
            history_entry = StateHistoryEntry(
                history_id=self._generate_history_id(),
                agent_id=agent_id,
                timestamp=datetime.now(),
                action=action,
                state_diff=state_diff,
                metadata={
                    "old_state_keys": list(old_state.keys()),
                    "new_state_keys": list(new_state.keys())
                }
            )
            
            # 压缩差异数据
            history_entry.compressed_diff = self._compress_diff(state_diff)
            
            # 保存到数据库
            conn = self._get_connection()
            conn.execute("""
                INSERT INTO state_history 
                (history_id, agent_id, timestamp, action, state_diff, 
                 metadata, compressed_diff)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                history_entry.history_id,
                history_entry.agent_id,
                history_entry.timestamp.isoformat(),
                history_entry.action,
                json.dumps(history_entry.state_diff),
                json.dumps(history_entry.metadata),
                history_entry.compressed_diff
            ))
            conn.commit()
            
            # 清理旧记录
            self._cleanup_old_entries(agent_id)
            
            logger.debug(f"状态变化记录成功: {history_entry.history_id}")
            return history_entry.history_id
            
        except Exception as e:
            logger.error(f"记录状态变化失败: {e}")
            raise
    
    def get_state_history(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取状态历史"""
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT history_id, agent_id, timestamp, action, state_diff,
                       metadata, compressed_diff
                FROM state_history 
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_id, limit))
            
            history_entries = []
            for row in cursor.fetchall():
                entry = StateHistoryEntry(
                    history_id=row[0],
                    agent_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    action=row[3],
                    state_diff=json.loads(row[4]) if row[4] else {},
                    metadata=json.loads(row[5]) if row[5] else {},
                    compressed_diff=row[6]
                )
                history_entries.append(entry)
            
            return history_entries
            
        except Exception as e:
            logger.error(f"获取状态历史失败: {e}")
            return []
    
    def replay_history(self, agent_id: str, base_state: Dict[str, Any], 
                      until_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """重放历史记录到指定时间点"""
        try:
            current_state = base_state.copy()
            
            # 获取历史记录（按时间顺序）
            conn = self._get_connection()
            if until_timestamp:
                cursor = conn.execute("""
                    SELECT history_id, agent_id, timestamp, action, state_diff,
                           metadata, compressed_diff
                    FROM state_history 
                    WHERE agent_id = ? AND timestamp <= ?
                    ORDER BY timestamp ASC
                """, (agent_id, until_timestamp.isoformat()))
            else:
                cursor = conn.execute("""
                    SELECT history_id, agent_id, timestamp, action, state_diff,
                           metadata, compressed_diff
                    FROM state_history 
                    WHERE agent_id = ?
                    ORDER BY timestamp ASC
                """, (agent_id,))
            
            for row in cursor.fetchall():
                # 解压缩差异数据
                if row[6] and not row[4]:  # 如果有压缩数据但没有原始数据
                    state_diff = self._decompress_diff(row[6])
                else:
                    state_diff = json.loads(row[4]) if row[4] else {}
                
                # 应用状态差异
                current_state = self._apply_state_diff(current_state, state_diff)
            
            return current_state
            
        except Exception as e:
            logger.error(f"重放历史记录失败: {e}")
            return base_state
    
    def _calculate_state_diff(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """计算状态差异"""
        diff = {}
        
        # 检查新增和修改的键
        for key, new_value in new_state.items():
            if key not in old_state:
                diff[f"added_{key}"] = new_value
            elif old_state[key] != new_value:
                diff[f"modified_{key}"] = {
                    "old": old_state[key],
                    "new": new_value
                }
        
        # 检查删除的键
        for key in old_state:
            if key not in new_state:
                diff[f"removed_{key}"] = old_state[key]
        
        return diff
    
    def _compress_diff(self, diff: Dict[str, Any]) -> bytes:
        """压缩差异数据"""
        import pickle
        import zlib
        serialized_diff = pickle.dumps(diff)
        return zlib.compress(serialized_diff)
    
    def _decompress_diff(self, compressed_diff: bytes) -> Dict[str, Any]:
        """解压缩差异数据"""
        import pickle
        import zlib
        decompressed_data = zlib.decompress(compressed_diff)
        return pickle.loads(decompressed_data)
    
    def _generate_history_id(self) -> str:
        """生成历史记录ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _apply_state_diff(self, current_state: Dict[str, Any], diff: Dict[str, Any]) -> Dict[str, Any]:
        """应用状态差异"""
        new_state = current_state.copy()
        
        for key, value in diff.items():
            if key.startswith("added_"):
                new_key = key[6:]  # 移除 "added_" 前缀
                new_state[new_key] = value
            elif key.startswith("modified_"):
                new_key = key[9:]  # 移除 "modified_" 前缀
                if isinstance(value, dict) and "new" in value:
                    new_state[new_key] = value["new"]
            elif key.startswith("removed_"):
                new_key = key[8:]  # 移除 "removed_" 前缀
                if new_key in new_state:
                    del new_state[new_key]
        
        return new_state
    
    def _cleanup_old_entries(self, agent_id: str):
        """清理旧记录"""
        try:
            conn = self._get_connection()
            # 获取该Agent的总记录数
            cursor = conn.execute(
                "SELECT COUNT(*) FROM state_history WHERE agent_id = ?",
                (agent_id,)
            )
            total_count = cursor.fetchone()[0]
            
            if total_count <= self.max_history_size:
                return
            
            # 删除最旧的记录
            to_delete = total_count - self.max_history_size
            cursor = conn.execute("""
                DELETE FROM state_history 
                WHERE agent_id = ? 
                AND history_id IN (
                    SELECT history_id FROM state_history 
                    WHERE agent_id = ? 
                    ORDER BY timestamp ASC 
                    LIMIT ?
                )
            """, (agent_id, agent_id, to_delete))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.debug(f"清理了 {deleted_count} 条历史记录，agent_id: {agent_id}")
            
        except Exception as e:
            logger.error(f"清理历史记录失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取历史统计信息"""
        try:
            conn = self._get_connection()
            # 总记录数
            cursor = conn.execute("SELECT COUNT(*) FROM state_history")
            total_count = cursor.fetchone()[0]
            
            # 按Agent分组统计
            cursor = conn.execute("""
                SELECT agent_id, COUNT(*) 
                FROM state_history 
                GROUP BY agent_id
                ORDER BY COUNT(*) DESC
            """)
            agent_counts = dict(cursor.fetchall())
            
            # 按Action分组统计
            cursor = conn.execute("""
                SELECT action, COUNT(*) 
                FROM state_history 
                GROUP BY action
                ORDER BY COUNT(*) DESC
            """)
            action_counts = dict(cursor.fetchall())
            
            # 数据库大小
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "total_records": total_count,
                "agent_counts": agent_counts,
                "action_counts": action_counts,
                "database_size_bytes": db_size,
                "database_path": str(self.db_path),
                "max_history_size": self.max_history_size
            }
            
        except Exception as e:
            logger.error(f"获取历史统计信息失败: {e}")
            return {}
    
    def delete_history(self, agent_id: str, before_timestamp: Optional[datetime] = None) -> int:
        """删除历史记录"""
        try:
            conn = self._get_connection()
            if before_timestamp:
                cursor = conn.execute("""
                    DELETE FROM state_history 
                    WHERE agent_id = ? AND timestamp < ?
                """, (agent_id, before_timestamp.isoformat()))
            else:
                cursor = conn.execute(
                    "DELETE FROM state_history WHERE agent_id = ?",
                    (agent_id,)
                )
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"删除了 {deleted_count} 条历史记录，agent_id: {agent_id}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"删除历史记录失败: {e}")
            return 0