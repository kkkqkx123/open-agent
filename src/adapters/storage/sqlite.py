"""SQLite存储适配器实现

提供基于SQLite的状态存储实现，整合现有的历史管理和快照存储功能。
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .interfaces import IStateStorageAdapter
from src.core.state.entities import StateSnapshot, StateHistoryEntry


logger = logging.getLogger(__name__)


class SQLiteStateStorageAdapter(IStateStorageAdapter):
    """SQLite状态存储适配器
    
    使用SQLite数据库存储状态数据，提供持久化存储。
    """
    
    def __init__(self, db_path: str = "data/state_storage.db"):
        """初始化SQLite存储适配器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
        self._transaction_active = False
        
        self._init_database()
        logger.debug(f"SQLite存储适配器初始化完成: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_database(self) -> None:
        """初始化数据库表"""
        try:
            conn = self._get_connection()
            
            # 创建历史记录表
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
            
            # 创建快照表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_snapshots (
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
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_agent_id ON state_history(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON state_history(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_agent_id ON state_snapshots(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp ON state_snapshots(timestamp)")
            
            conn.commit()
            logger.debug("SQLite数据库初始化完成")
            
        except Exception as e:
            logger.error(f"初始化SQLite数据库失败: {e}")
            raise
    
    def save_history_entry(self, entry: StateHistoryEntry) -> bool:
        """保存历史记录条目"""
        try:
            conn = self._get_connection()
            conn.execute("""
                INSERT OR REPLACE INTO state_history 
                (history_id, agent_id, timestamp, action, state_diff, metadata, compressed_diff)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.history_id,
                entry.agent_id,
                entry.timestamp.isoformat(),
                entry.action,
                json.dumps(entry.state_diff),
                json.dumps(entry.metadata),
                entry.compressed_diff
            ))
            
            if not self._transaction_active:
                conn.commit()
            
            logger.debug(f"历史记录保存成功: {entry.history_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
            return False
    
    def get_history_entries(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取历史记录条目"""
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT history_id, agent_id, timestamp, action, state_diff, metadata, compressed_diff
                FROM state_history 
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_id, limit))
            
            entries = []
            for row in cursor.fetchall():
                entry = StateHistoryEntry(
                    history_id=row['history_id'],
                    agent_id=row['agent_id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    action=row['action'],
                    state_diff=json.loads(row['state_diff']) if row['state_diff'] else {},
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    compressed_diff=row['compressed_diff']
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"获取历史记录失败: {e}")
            return []
    
    def delete_history_entry(self, history_id: str) -> bool:
        """删除历史记录条目"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "DELETE FROM state_history WHERE history_id = ?",
                (history_id,)
            )
            
            if not self._transaction_active:
                conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.debug(f"历史记录删除成功: {history_id}")
            else:
                logger.warning(f"历史记录不存在: {history_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"删除历史记录失败: {e}")
            return False
    
    def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "DELETE FROM state_history WHERE agent_id = ?",
                (agent_id,)
            )
            
            if not self._transaction_active:
                conn.commit()
            
            deleted_count = cursor.rowcount
            logger.debug(f"代理历史记录清空成功: {agent_id}, 删除 {deleted_count} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"清空代理历史记录失败: {e}")
            return False
    
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """保存状态快照"""
        try:
            conn = self._get_connection()
            conn.execute("""
                INSERT OR REPLACE INTO state_snapshots 
                (snapshot_id, agent_id, domain_state, timestamp, snapshot_name, 
                 metadata, compressed_data, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.snapshot_id,
                snapshot.agent_id,
                json.dumps(snapshot.domain_state),
                snapshot.timestamp.isoformat(),
                snapshot.snapshot_name,
                json.dumps(snapshot.metadata),
                snapshot.compressed_data,
                snapshot.size_bytes
            ))
            
            if not self._transaction_active:
                conn.commit()
            
            logger.debug(f"快照保存成功: {snapshot.snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存快照失败: {e}")
            return False
    
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载状态快照"""
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT snapshot_id, agent_id, domain_state, timestamp, snapshot_name,
                       metadata, compressed_data, size_bytes
                FROM state_snapshots WHERE snapshot_id = ?
            """, (snapshot_id,))
            
            row = cursor.fetchone()
            if row:
                return StateSnapshot(
                    snapshot_id=row['snapshot_id'],
                    agent_id=row['agent_id'],
                    domain_state=json.loads(row['domain_state']),
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    snapshot_name=row['snapshot_name'] or "",
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    compressed_data=row['compressed_data'],
                    size_bytes=row['size_bytes'] or 0
                )
            
            return None
            
        except Exception as e:
            logger.error(f"加载快照失败: {e}")
            return None
    
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定代理的快照列表"""
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT snapshot_id, agent_id, domain_state, timestamp, snapshot_name,
                       metadata, compressed_data, size_bytes
                FROM state_snapshots 
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_id, limit))
            
            snapshots = []
            for row in cursor.fetchall():
                snapshot = StateSnapshot(
                    snapshot_id=row['snapshot_id'],
                    agent_id=row['agent_id'],
                    domain_state=json.loads(row['domain_state']),
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    snapshot_name=row['snapshot_name'] or "",
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    compressed_data=row['compressed_data'],
                    size_bytes=row['size_bytes'] or 0
                )
                snapshots.append(snapshot)
            
            return snapshots
            
        except Exception as e:
            logger.error(f"获取代理快照列表失败: {e}")
            return []
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除状态快照"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "DELETE FROM state_snapshots WHERE snapshot_id = ?",
                (snapshot_id,)
            )
            
            if not self._transaction_active:
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
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
            conn = self._get_connection()
            
            # 总记录数
            cursor = conn.execute("SELECT COUNT(*) FROM state_history")
            total_count = cursor.fetchone()[0]
            
            # 按代理分组统计
            cursor = conn.execute("""
                SELECT agent_id, COUNT(*) 
                FROM state_history 
                GROUP BY agent_id
                ORDER BY COUNT(*) DESC
            """)
            agent_counts = dict(cursor.fetchall())
            
            # 数据库大小
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "total_history_entries": total_count,
                "agent_counts": agent_counts,
                "database_size_bytes": db_size,
                "database_path": str(self.db_path),
                "storage_type": "sqlite"
            }
            
        except Exception as e:
            logger.error(f"获取历史统计信息失败: {e}")
            return {}
    
    def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            conn = self._get_connection()
            
            # 总快照数
            cursor = conn.execute("SELECT COUNT(*) FROM state_snapshots")
            total_count = cursor.fetchone()[0]
            
            # 按代理分组统计
            cursor = conn.execute("""
                SELECT agent_id, COUNT(*) 
                FROM state_snapshots 
                GROUP BY agent_id
                ORDER BY COUNT(*) DESC
            """)
            agent_counts = dict(cursor.fetchall())
            
            return {
                "total_snapshots": total_count,
                "agent_counts": agent_counts,
                "storage_type": "sqlite"
            }
            
        except Exception as e:
            logger.error(f"获取快照统计信息失败: {e}")
            return {}
    
    def begin_transaction(self) -> None:
        """开始事务"""
        if self._transaction_active:
            logger.warning("事务已处于活动状态，忽略嵌套事务")
            return
        
        self._transaction_active = True
        conn = self._get_connection()
        conn.execute("BEGIN")
        logger.debug("事务开始")
    
    def commit_transaction(self) -> None:
        """提交事务"""
        if not self._transaction_active:
            logger.warning("没有活动的事务，忽略提交")
            return
        
        self._transaction_active = False
        conn = self._get_connection()
        conn.commit()
        logger.debug("事务提交")
    
    def rollback_transaction(self) -> None:
        """回滚事务"""
        if not self._transaction_active:
            logger.warning("没有活动的事务，忽略回滚")
            return
        
        self._transaction_active = False
        conn = self._get_connection()
        conn.rollback()
        logger.debug("事务回滚")
    
    def close(self) -> None:
        """关闭存储连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.debug("SQLite存储适配器已关闭")
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            conn = self._get_connection()
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            return True
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    def get_all_agents(self) -> List[str]:
        """获取所有代理ID
        
        Returns:
            代理ID列表
        """
        try:
            conn = self._get_connection()
            
            # 从历史记录获取代理ID
            cursor = conn.execute("SELECT DISTINCT agent_id FROM state_history")
            history_agents = [row[0] for row in cursor.fetchall()]
            
            # 从快照获取代理ID
            cursor = conn.execute("SELECT DISTINCT agent_id FROM state_snapshots")
            snapshot_agents = [row[0] for row in cursor.fetchall()]
            
            # 合并并去重
            all_agents = list(set(history_agents + snapshot_agents))
            return all_agents
            
        except Exception as e:
            logger.error(f"获取所有代理ID失败: {e}")
            return []
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息
        
        Returns:
            存储信息字典
        """
        try:
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "storage_type": "sqlite",
                "database_path": str(self.db_path),
                "database_size_bytes": db_size,
                "transaction_active": self._transaction_active,
                "connection_open": self._conn is not None
            }
            
        except Exception as e:
            logger.error(f"获取存储信息失败: {e}")
            return {}
    
    def vacuum_database(self) -> bool:
        """清理数据库，回收空间
        
        Returns:
            是否成功清理
        """
        try:
            conn = self._get_connection()
            conn.execute("VACUUM")
            logger.debug("数据库清理完成")
            return True
            
        except Exception as e:
            logger.error(f"数据库清理失败: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """优化数据库，更新统计信息
        
        Returns:
            是否成功优化
        """
        try:
            conn = self._get_connection()
            conn.execute("ANALYZE")
            logger.debug("数据库优化完成")
            return True
            
        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
            return False