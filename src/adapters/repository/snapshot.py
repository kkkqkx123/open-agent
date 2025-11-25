"""快照Repository重构实现

使用基类和工具类重构的快照Repository实现。
"""

from typing import Dict, Any, List, Optional

from src.interfaces.repository import ISnapshotRepository
from .base import SQLiteBaseRepository, MemoryBaseRepository, FileBaseRepository
from .utils import JsonUtils, TimeUtils, IdUtils, SQLiteUtils, FileUtils


class SQLiteSnapshotRepository(SQLiteBaseRepository, ISnapshotRepository):
    """SQLite快照Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite快照Repository"""
        table_sql = """
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                state_data TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_snapshots_agent_id ON snapshots(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON snapshots(created_at)"
        ]
        
        super().__init__(config, "snapshots", table_sql, indexes_sql)
    
    async def save_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """保存快照"""
        try:
            snapshot_id = IdUtils.get_or_generate_id(
                snapshot, "snapshot_id", IdUtils.generate_snapshot_id
            )
            
            data = {
                "snapshot_id": snapshot_id,
                "agent_id": snapshot["agent_id"],
                "state_data": JsonUtils.serialize(snapshot["state_data"]),
                "metadata": JsonUtils.serialize(snapshot.get("metadata", {}))
            }
            
            self._insert_or_replace(data)
            self._log_operation("快照保存", True, snapshot_id)
            return snapshot_id
            
        except Exception as e:
            self._handle_exception("保存快照", e)
            raise  # 重新抛出异常，不会到达下一行
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照"""
        try:
            row = self._find_by_id("snapshot_id", snapshot_id)
            if row:
                return {
                    "snapshot_id": row[0],
                    "agent_id": row[1],
                    "state_data": JsonUtils.deserialize(row[2]),
                    "metadata": JsonUtils.deserialize(row[3]),
                    "created_at": row[4],
                    "updated_at": row[5]
                }
            return None
            
        except Exception as e:
            self._handle_exception("加载快照", e)
            raise  # 重新抛出异常
    
    async def get_snapshots(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取代理的快照列表"""
        try:
            query = """
                SELECT snapshot_id, agent_id, state_data, metadata, created_at, updated_at
                FROM snapshots
                WHERE agent_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            results = SQLiteUtils.execute_query(self.db_path, query, (agent_id, limit))
            
            snapshots = []
            for row in results:
                snapshots.append({
                    "snapshot_id": row[0],
                    "agent_id": row[1],
                    "state_data": JsonUtils.deserialize(row[2]),
                    "metadata": JsonUtils.deserialize(row[3]),
                    "created_at": row[4],
                    "updated_at": row[5]
                })
            
            self._log_operation("获取快照列表", True, f"{agent_id}, 共{len(snapshots)}条")
            return snapshots
            
        except Exception as e:
            self._handle_exception("获取快照列表", e)
            raise  # 重新抛出异常
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            deleted = self._delete_by_id("snapshot_id", snapshot_id)
            self._log_operation("快照删除", deleted, snapshot_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除快照", e)
            raise # 重新抛出异常
    
    async def delete_snapshots_by_agent(self, agent_id: str) -> int:
        """删除代理的所有快照"""
        try:
            query = "DELETE FROM snapshots WHERE agent_id = ?"
            affected_rows = SQLiteUtils.execute_update(self.db_path, query, (agent_id,))
            deleted_count = affected_rows
            self._log_operation("代理快照删除", True, f"{agent_id}, 共{deleted_count}条")
            return deleted_count
            
        except Exception as e:
            self._handle_exception("删除代理快照", e)
            raise # 重新抛出异常
    
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            # 总快照数
            total_count = self._count_records()
            
            # 按代理统计
            top_agents_results = SQLiteUtils.get_top_records(
                self.db_path, self.table_name, "agent_id", "created_at", 10
            )
            top_agents = [{"agent_id": row[0], "count": row[1]} for row in top_agents_results]
            
            stats = {
                "total_count": total_count,
                "agent_count": len(top_agents),
                "top_agents": top_agents
            }
            
            self._log_operation("获取快照统计信息", True)
            return stats
            
        except Exception as e:
            self._handle_exception("获取快照统计信息", e)
            raise # 重新抛出异常
    
    async def get_latest_snapshot(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取代理的最新快照"""
        try:
            query = """
                SELECT snapshot_id, agent_id, state_data, metadata, created_at, updated_at
                FROM snapshots
                WHERE agent_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            results = SQLiteUtils.execute_query(self.db_path, query, (agent_id,))
            
            if results:
                row = results[0]
                return {
                    "snapshot_id": row[0],
                    "agent_id": row[1],
                    "state_data": JsonUtils.deserialize(row[2]),
                    "metadata": JsonUtils.deserialize(row[3]),
                    "created_at": row[4],
                    "updated_at": row[5]
                }
            return None
            
        except Exception as e:
            self._handle_exception("获取最新快照", e)
            raise  # 重新抛出异常
    
    async def cleanup_old_snapshots(self, agent_id: str, max_count: int) -> int:
        """清理旧的快照，保留最新的max_count个"""
        try:
            # 获取所有快照ID，按创建时间排序
            query = """
                SELECT snapshot_id FROM snapshots
                WHERE agent_id = ?
                ORDER BY created_at DESC
            """
            results = SQLiteUtils.execute_query(self.db_path, query, (agent_id,))
            all_snapshot_ids = [row[0] for row in results]
            
            if len(all_snapshot_ids) <= max_count:
                return 0
            
            # 需要删除的快照
            to_delete_ids = all_snapshot_ids[max_count:]
            
            # 删除旧快照
            deleted_count = 0
            for snapshot_id in to_delete_ids:
                if self._delete_by_id("snapshot_id", snapshot_id):
                    deleted_count += 1
            
            self._log_operation("清理旧快照", True, f"{agent_id}, 删除{deleted_count}条")
            return deleted_count
            
        except Exception as e:
            self._handle_exception("清理旧快照", e)
            raise # 重新抛出异常


class MemorySnapshotRepository(MemoryBaseRepository, ISnapshotRepository):
    """内存快照Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存快照Repository"""
        super().__init__(config)
    
    async def save_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """保存快照"""
        try:
            snapshot_id = IdUtils.get_or_generate_id(
                snapshot, "snapshot_id", IdUtils.generate_snapshot_id
            )
            
            full_snapshot = TimeUtils.add_timestamp({
                "snapshot_id": snapshot_id,
                **snapshot
            })
            
            # 保存到存储
            self._save_item(snapshot_id, full_snapshot)
            
            # 更新索引
            self._add_to_index("agent", snapshot["agent_id"], snapshot_id)
            
            self._log_operation("内存快照保存", True, snapshot_id)
            return snapshot_id
            
        except Exception as e:
            self._handle_exception("保存内存快照", e)
            raise # 重新抛出异常
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照"""
        try:
            snapshot = self._load_item(snapshot_id)
            if snapshot:
                self._log_operation("内存快照加载", True, snapshot_id)
                return snapshot
            return None
            
        except Exception as e:
            self._handle_exception("加载内存快照", e)
            raise # 重新抛出异常
    
    async def get_snapshots(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取代理的快照列表"""
        try:
            snapshot_ids = self._get_from_index("agent", agent_id)
            # 过滤掉None值，确保只返回有效的快照
            snapshots = [item for sid in snapshot_ids if (item := self._load_item(sid)) is not None]
            
            # 按创建时间倒序排序
            snapshots = TimeUtils.sort_by_time(snapshots, "created_at", True)
            snapshots = snapshots[:limit]
            
            self._log_operation("获取内存快照列表", True, f"{agent_id}, 共{len(snapshots)}条")
            return snapshots
            
        except Exception as e:
            self._handle_exception("获取内存快照列表", e)
            raise # 重新抛出异常
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            snapshot = self._load_item(snapshot_id)
            if not snapshot:
                return False
            
            # 从索引中移除
            self._remove_from_index("agent", snapshot["agent_id"], snapshot_id)
            
            # 从存储中删除
            deleted = self._delete_item(snapshot_id)
            self._log_operation("内存快照删除", deleted, snapshot_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除内存快照", e)
            raise # 重新抛出异常
    
    async def delete_snapshots_by_agent(self, agent_id: str) -> int:
        """删除代理的所有快照"""
        try:
            snapshot_ids = self._get_from_index("agent", agent_id)
            
            # 删除所有快照
            deleted_count = 0
            for snapshot_id in snapshot_ids:
                if self._delete_item(snapshot_id):
                    deleted_count += 1
            
            # 清空索引
            if agent_id in self._indexes.get("agent", {}):
                del self._indexes["agent"][agent_id]
            
            self._log_operation("内存代理快照删除", True, f"{agent_id}, 共{deleted_count}条")
            return deleted_count
            
        except Exception as e:
            self._handle_exception("删除内存代理快照", e)
            raise # 重新抛出异常
    
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            total_count = len(self._storage)
            
            # 按代理统计
            top_agents = []
            for agent_id, snapshot_ids in self._indexes.get("agent", {}).items():
                top_agents.append({"agent_id": agent_id, "count": len(snapshot_ids)})
            # 修复排序函数的类型问题
            top_agents = sorted(top_agents, key=lambda x: x["count"], reverse=True)[:10]  # type: ignore
            
            stats = {
                "total_count": total_count,
                "agent_count": len(top_agents),
                "top_agents": top_agents
            }
            
            self._log_operation("获取内存快照统计信息", True)
            return stats
            
        except Exception as e:
            self._handle_exception("获取内存快照统计信息", e)
            raise # 重新抛出异常
    
    async def get_latest_snapshot(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取代理的最新快照"""
        try:
            snapshots = await self.get_snapshots(agent_id, limit=1)
            return snapshots[0] if snapshots else None
            
        except Exception as e:
            self._handle_exception("获取最新内存快照", e)
            raise # 重新抛出异常
    
    async def cleanup_old_snapshots(self, agent_id: str, max_count: int) -> int:
        """清理旧的快照，保留最新的max_count个"""
        try:
            snapshots = await self.get_snapshots(agent_id, limit=1000)
            
            if len(snapshots) <= max_count:
                return 0
            
            # 需要删除的快照
            to_delete = snapshots[max_count:]
            
            # 删除旧快照
            deleted_count = 0
            for snapshot in to_delete:
                if await self.delete_snapshot(snapshot["snapshot_id"]):
                    deleted_count += 1
            
            self._log_operation("清理内存旧快照", True, f"{agent_id}, 删除{deleted_count}条")
            return deleted_count
            
        except Exception as e:
            self._handle_exception("清理内存旧快照", e)
            raise # 重新抛出异常


class FileSnapshotRepository(FileBaseRepository, ISnapshotRepository):
    """文件快照Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件快照Repository"""
        super().__init__(config)
    
    async def save_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """保存快照"""
        try:
            snapshot_id = IdUtils.get_or_generate_id(
                snapshot, "snapshot_id", IdUtils.generate_snapshot_id
            )
            
            full_snapshot = TimeUtils.add_timestamp({
                "snapshot_id": snapshot_id,
                **snapshot
            })
            
            # 保存到文件
            self._save_item(snapshot["agent_id"], snapshot_id, full_snapshot)
            
            self._log_operation("文件快照保存", True, snapshot_id)
            return snapshot_id
            
        except Exception as e:
            self._handle_exception("保存文件快照", e)
            raise # 重新抛出异常
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照"""
        try:
            # 在所有代理目录中查找快照
            from pathlib import Path
            base_path = Path(self.base_path)
            
            for agent_dir in base_path.iterdir():
                if agent_dir.is_dir():
                    snapshot = self._load_item(agent_dir.name, snapshot_id)
                    if snapshot:
                        self._log_operation("文件快照加载", True, snapshot_id)
                        return snapshot
            return None
            
        except Exception as e:
            self._handle_exception("加载文件快照", e)
            raise # 重新抛出异常
    
    async def get_snapshots(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取代理的快照列表"""
        try:
            snapshots = self._list_items(agent_id)
            
            # 按创建时间倒序排序
            snapshots = TimeUtils.sort_by_time(snapshots, "created_at", True)
            snapshots = snapshots[:limit]
            
            self._log_operation("获取文件快照列表", True, f"{agent_id}, 共{len(snapshots)}条")
            return snapshots
            
        except Exception as e:
            self._handle_exception("获取文件快照列表", e)
            raise # 重新抛出异常
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            # 在所有代理目录中查找并删除快照
            from pathlib import Path
            base_path = Path(self.base_path)
            
            for agent_dir in base_path.iterdir():
                if agent_dir.is_dir():
                    deleted = self._delete_item(agent_dir.name, snapshot_id)
                    if deleted:
                        self._log_operation("文件快照删除", True, snapshot_id)
                        return True
            return False
            
        except Exception as e:
            self._handle_exception("删除文件快照", e)
            raise # 重新抛出异常
    
    async def delete_snapshots_by_agent(self, agent_id: str) -> int:
        """删除代理的所有快照"""
        try:
            import shutil
            from pathlib import Path
            agent_dir = Path(self.base_path) / agent_id
            
            if agent_dir.exists():
                snapshot_files = list(agent_dir.glob("*.json"))
                deleted_count = len(snapshot_files)
                shutil.rmtree(agent_dir)
                self._log_operation("文件代理快照删除", True, f"{agent_id}, 共{deleted_count}条")
                return deleted_count
            return 0
            
        except Exception as e:
            self._handle_exception("删除文件代理快照", e)
            raise # 重新抛出异常
    
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            from pathlib import Path
            base_path = Path(self.base_path)
            
            total_count = 0
            agent_counts = {}
            
            for agent_dir in base_path.iterdir():
                if agent_dir.is_dir():
                    snapshot_files = list(agent_dir.glob("*.json"))
                    agent_id = agent_dir.name
                    agent_counts[agent_id] = len(snapshot_files)
                    total_count += len(snapshot_files)
            
            # 排序统计结果
            top_agents_items = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_agents = [{"agent_id": str(aid), "count": count} for aid, count in top_agents_items]
            
            stats = {
                "total_count": total_count,
                "agent_count": len(agent_counts),
                "top_agents": top_agents
            }
            
            self._log_operation("获取文件快照统计信息", True)
            return stats
            
        except Exception as e:
            self._handle_exception("获取文件快照统计信息", e)
            raise # 重新抛出异常
    
    async def get_latest_snapshot(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取代理的最新快照"""
        try:
            snapshots = await self.get_snapshots(agent_id, limit=1)
            return snapshots[0] if snapshots else None
            
        except Exception as e:
            self._handle_exception("获取最新文件快照", e)
            raise # 重新抛出异常
    
    async def cleanup_old_snapshots(self, agent_id: str, max_count: int) -> int:
        """清理旧的快照，保留最新的max_count个"""
        try:
            snapshots = await self.get_snapshots(agent_id, limit=1000)
            
            if len(snapshots) <= max_count:
                return 0
            
            # 需要删除的快照
            to_delete = snapshots[max_count:]
            
            # 删除旧快照
            deleted_count = 0
            for snapshot in to_delete:
                if await self.delete_snapshot(snapshot["snapshot_id"]):
                    deleted_count += 1
            
            self._log_operation("清理文件旧快照", True, f"{agent_id}, 删除{deleted_count}条")
            return deleted_count
            
        except Exception as e:
            self._handle_exception("清理文件旧快照", e)
            raise # 重新抛出异常