"""内存快照Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ISnapshotRepository
from ..memory_base import MemoryBaseRepository
from ..utils import TimeUtils, IdUtils


class MemorySnapshotRepository(MemoryBaseRepository, ISnapshotRepository):
    """内存快照Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存快照Repository"""
        super().__init__(config)
    
    async def save_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """保存快照"""
        try:
            def _save() -> str:
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
                self._add_to_index("agent", snapshot["thread_id"], snapshot_id)
                
                self._log_operation("内存快照保存", True, snapshot_id)
                return snapshot_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存内存快照", e)
            raise # 重新抛出异常
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照"""
        try:
            def _load() -> Optional[Dict[str, Any]]:
                snapshot = self._load_item(snapshot_id)
                if snapshot:
                    self._log_operation("内存快照加载", True, snapshot_id)
                    return snapshot
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载内存快照", e)
            raise # 重新抛出异常
    
    async def get_snapshots(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取线程的快照列表"""
        try:
            def _get() -> List[Dict[str, Any]]:
                snapshot_ids = self._get_from_index("agent", thread_id)
                # 过滤掉None值，确保只返回有效的快照
                snapshots = [item for sid in snapshot_ids if (item := self._load_item(sid)) is not None]
                
                # 按创建时间倒序排序
                snapshots = TimeUtils.sort_by_time(snapshots, "created_at", True)
                snapshots = snapshots[:limit]
                
                self._log_operation("获取内存快照列表", True, f"{thread_id}, 共{len(snapshots)}条")
                return snapshots
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取内存快照列表", e)
            raise # 重新抛出异常
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            def _delete() -> bool:
                snapshot = self._load_item(snapshot_id)
                if not snapshot:
                    return False
                
                # 从索引中移除
                self._remove_from_index("agent", snapshot["thread_id"], snapshot_id)
                
                # 从存储中删除
                deleted = self._delete_item(snapshot_id)
                self._log_operation("内存快照删除", deleted, snapshot_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除内存快照", e)
            raise # 重新抛出异常
    
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            def _get_stats() -> Dict[str, Any]:
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_stats)
            
        except Exception as e:
            self._handle_exception("获取内存快照统计信息", e)
            raise # 重新抛出异常
    
    async def delete_snapshots_by_thread(self, thread_id: str) -> int:
        """删除线程的所有快照"""
        try:
            def _delete() -> int:
                snapshot_ids = self._get_from_index("agent", thread_id)
                count = 0
                
                for snapshot_id in snapshot_ids:
                    if self._delete_item(snapshot_id):
                        count += 1
                
                # 清空索引
                if "agent" in self._indexes and thread_id in self._indexes["agent"]:
                    del self._indexes["agent"][thread_id]
                
                self._log_operation("删除线程快照", True, f"{thread_id}, 共{count}条")
                return count
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除线程快照", e)
            raise # 重新抛出异常
    
    async def get_latest_snapshot(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取线程的最新快照"""
        try:
            def _get() -> Optional[Dict[str, Any]]:
                snapshot_ids = self._get_from_index("agent", thread_id)
                if not snapshot_ids:
                    return None
                
                # 过滤掉None值，确保只返回有效的快照
                snapshots = [item for sid in snapshot_ids if (item := self._load_item(sid)) is not None]
                
                if not snapshots:
                    return None
                
                # 按创建时间倒序排序，取第一个
                snapshots = TimeUtils.sort_by_time(snapshots, "created_at", True)
                latest = snapshots[0] if snapshots else None
                
                self._log_operation("获取最新快照", True, f"{thread_id}")
                return latest
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取最新快照", e)
            raise # 重新抛出异常
    
    async def cleanup_old_snapshots(self, thread_id: str, max_count: int) -> int:
        """清理旧的快照，保留最新的max_count个"""
        try:
            def _cleanup() -> int:
                snapshot_ids = self._get_from_index("agent", thread_id)
                if len(snapshot_ids) <= max_count:
                    return 0
                
                # 过滤掉None值，确保只返回有效的快照
                snapshots = [item for sid in snapshot_ids if (item := self._load_item(sid)) is not None]
                
                if len(snapshots) <= max_count:
                    return 0
                
                # 按创建时间倒序排序
                snapshots = TimeUtils.sort_by_time(snapshots, "created_at", True)
                
                # 保留最新的max_count个，删除其余的
                to_delete = snapshots[max_count:]
                deleted_count = 0
                
                for snapshot in to_delete:
                    snapshot_id = snapshot.get("snapshot_id")
                    if snapshot_id and self._delete_item(snapshot_id):
                        self._remove_from_index("agent", thread_id, snapshot_id)
                        deleted_count += 1
                
                self._log_operation("清理旧快照", True, f"{thread_id}, 删除{deleted_count}条")
                return deleted_count
            
            return await asyncio.get_event_loop().run_in_executor(None, _cleanup)
            
        except Exception as e:
            self._handle_exception("清理旧快照", e)
            raise # 重新抛出异常
    
    async def get_snapshot_comparison(
        self,
        snapshot_id1: str,
        snapshot_id2: str
    ) -> Dict[str, Any]:
        """比较两个快照"""
        try:
            snapshot1 = await self.load_snapshot(snapshot_id1)
            snapshot2 = await self.load_snapshot(snapshot_id2)
            
            if not snapshot1 or not snapshot2:
                return {
                    "error": "一个或两个快照不存在",
                    "snapshot1_exists": snapshot1 is not None,
                    "snapshot2_exists": snapshot2 is not None
                }
            
            # 简单的状态数据比较
            state1 = snapshot1.get("state_data", {})
            state2 = snapshot2.get("state_data", {})
            
            comparison = {
                "snapshot_id1": snapshot_id1,
                "snapshot_id2": snapshot_id2,
                "timestamp1": snapshot1.get("timestamp"),
                "timestamp2": snapshot2.get("timestamp"),
                "thread_id1": snapshot1.get("thread_id"),
                "thread_id2": snapshot2.get("thread_id"),
                "state_equal": state1 == state2,
                "metadata_equal": snapshot1.get("metadata") == snapshot2.get("metadata")
            }
            
            self._log_operation("快照比较", True, f"{snapshot_id1} vs {snapshot_id2}")
            return comparison
            
        except Exception as e:
            self._handle_exception("快照比较", e)
            raise # 重新抛出异常
    
    async def validate_snapshot_integrity(self, snapshot_id: str) -> bool:
        """验证快照完整性"""
        try:
            snapshot = await self.load_snapshot(snapshot_id)
            
            if not snapshot:
                return False
            
            # 检查必需字段
            required_fields = ["snapshot_id", "thread_id", "state_data", "timestamp"]
            for field in required_fields:
                if field not in snapshot:
                    self._log_operation("快照完整性验证", False, f"{snapshot_id}, 缺少字段: {field}")
                    return False
            
            # 检查时间戳格式 - 简单验证，不依赖可能不存在的方法
            timestamp = snapshot.get("timestamp")
            if not timestamp or not isinstance(timestamp, str):
                self._log_operation("快照完整性验证", False, f"{snapshot_id}, 无效时间戳")
                return False
            
            self._log_operation("快照完整性验证", True, snapshot_id)
            return True
            
        except Exception as e:
            self._handle_exception("快照完整性验证", e)
            raise # 重新抛出异常