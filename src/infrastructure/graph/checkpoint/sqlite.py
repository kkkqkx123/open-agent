"""SQLite检查点保存器实现

提供SQLite数据库中的检查点存储。
"""

import json
import sqlite3
import threading
from collections.abc import Iterator, Sequence
from typing import Any, Dict, Optional

from .base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

__all__ = ("SqliteCheckpointSaver",)


class SqliteCheckpointSaver(BaseCheckpointSaver[str]):
    """SQLite检查点保存器。
    
    将检查点存储在SQLite数据库中，适用于轻量级、同步使用场景。
    
    注意：
        此类适用于轻量级、同步使用场景，不扩展到多个线程。
        对于类似的sqlite保存器与异步支持，考虑使用AsyncSqliteCheckpointSaver。
    """
    
    def __init__(self, conn: sqlite3.Connection):
        """初始化SQLite检查点保存器。
        
        Args:
            conn: SQLite数据库连接
        """
        self.conn = conn
        self.is_setup = False
        self.lock = threading.Lock()
        self._setup()
    
    def _setup(self) -> None:
        """设置检查点数据库。"""
        if self.is_setup:
            return
        
        with self.lock:
            self.conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    type TEXT,
                    checkpoint BLOB,
                    metadata BLOB,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                );
                CREATE TABLE IF NOT EXISTS writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    type TEXT,
                    value BLOB,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                );
                """
            )
            self.is_setup = True
    
    def get(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """获取检查点。
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点，如果未找到则为None
        """
        if value := self.get_tuple(config):
            return value.checkpoint
        return None
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """获取检查点元组。
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点元组，如果未找到则为None
        """
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        
        with self.lock:
            cursor = self.conn.cursor()
            
            # 查找最新的检查点
            checkpoint_id = config["configurable"].get("checkpoint_id")
            if checkpoint_id:
                cursor.execute(
                    "SELECT checkpoint, metadata FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?",
                    (str(config["configurable"]["thread_id"]), checkpoint_ns, checkpoint_id)
                )
            else:
                cursor.execute(
                    "SELECT checkpoint, metadata FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? ORDER BY checkpoint_id DESC LIMIT 1",
                    (str(config["configurable"]["thread_id"]), checkpoint_ns)
                )
            
            row = cursor.fetchone()
            if row:
                checkpoint_blob, metadata_blob = row
                checkpoint = json.loads(checkpoint_blob)
                metadata = json.loads(metadata_blob) if metadata_blob else {}
                
                # 查找写入
                cursor.execute(
                    "SELECT channel, value FROM writes WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ? ORDER BY task_id, idx",
                    (str(config["configurable"]["thread_id"]), checkpoint_ns, checkpoint["id"])
                )
                
                writes = [(channel, json.loads(value)) for channel, value in cursor.fetchall()]
                
                return CheckpointTuple(
                    config=config,
                    checkpoint=Checkpoint(**checkpoint),
                    metadata=CheckpointMetadata(**metadata),
                    pending_writes=writes
                )
        
        return None
    
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """列出检查点。
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Returns:
            匹配的检查点元组的迭代器
        """
        count = 0
        
        with self.lock:
            cursor = self.conn.cursor()
            
            # 构建查询
            query = "SELECT thread_id, checkpoint_ns, checkpoint_id, checkpoint, metadata FROM checkpoints"
            params = []
            
            if config:
                query += " WHERE thread_id = ?"
                params.append(str(config["configurable"]["thread_id"]))
            
            query += " ORDER BY checkpoint_id DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                thread_id, checkpoint_ns, checkpoint_id, checkpoint_blob, metadata_blob = row
                checkpoint = json.loads(checkpoint_blob)
                metadata = json.loads(metadata_blob) if metadata_blob else {}
                
                # 查找写入
                cursor.execute(
                    "SELECT channel, value FROM writes WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ? ORDER BY task_id, idx",
                    (thread_id, checkpoint_ns, checkpoint_id)
                )
                
                writes = [(channel, json.loads(value)) for channel, value in cursor.fetchall()]
                
                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": checkpoint_id,
                        }
                    },
                    checkpoint=Checkpoint(**checkpoint),
                    metadata=CheckpointMetadata(**metadata),
                    pending_writes=writes
                )
                
                count += 1
                if limit and count >= limit:
                    return
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Dict[str, str],
    ) -> Dict[str, Any]:
        """存储检查点。
        
        Args:
            config: 检查点的配置
            checkpoint: 要存储的检查点
            metadata: 检查点的额外元数据
            new_versions: 作为此写入的新通道版本
            
        Returns:
            存储检查点后更新的配置
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        
        checkpoint_blob = json.dumps(checkpoint)
        metadata_blob = json.dumps(metadata)
        
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(thread_id),
                    checkpoint_ns,
                    checkpoint["id"],
                    config["configurable"].get("checkpoint_id"),
                    "checkpoint",
                    checkpoint_blob,
                    metadata_blob
                )
            )
            self.conn.commit()
        
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }
    
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储中间写入。
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = config["configurable"]["checkpoint_id"]
        
        with self.lock:
            cursor = self.conn.cursor()
            
            for idx, (channel, value) in enumerate(writes):
                cursor.execute(
                    "INSERT OR REPLACE INTO writes (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, value) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(thread_id),
                        checkpoint_ns,
                        checkpoint_id,
                        task_id,
                        idx,
                        channel,
                        "write",
                        json.dumps(value)
                    )
                )
            
            self.conn.commit()
    
    def delete_thread(self, thread_id: str) -> None:
        """删除与线程ID关联的所有检查点和写入。
        
        Args:
            thread_id: 线程ID
        """
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (str(thread_id),))
            cursor.execute("DELETE FROM writes WHERE thread_id = ?", (str(thread_id),))
            self.conn.commit()
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息。
        
        Returns:
            统计信息字典
        """
        with self.lock:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM checkpoints")
            checkpoint_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM writes")
            writes_count = cursor.fetchone()[0]
            
            return {
                "checkpoint_count": checkpoint_count,
                "writes_count": writes_count,
                "database_path": self.conn.execute("PRAGMA database_list").fetchall()[0][2]
            }