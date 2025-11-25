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
            def _save():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存内存快照", e)
            raise # 重新抛出异常
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照"""
        try:
            def _load():
                snapshot = self._load_item(snapshot_id)
                if snapshot:
                    self._log_operation("内存快照加载", True, snapshot_id)
                    return snapshot
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载内存快照", e)
            raise # 重新抛出异常
    
    async def get_snapshots(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取代理的快照列表"""
        try:
            def _get():
                snapshot_ids = self._get_from_index("agent", agent_id)
                # 过滤掉None值，确保只返回有效的快照
                snapshots = [item for sid in snapshot_ids if (item := self._load_item(sid)) is not None]
                
                # 按创建时间倒序排序
                snapshots = TimeUtils.sort_by_time(snapshots, "created_at", True)
                snapshots = snapshots[:limit]
                
                self._log_operation("获取内存快照列表", True, f"{agent_id}, 共{len(snapshots)}条")
                return snapshots
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取内存快照列表", e)
            raise # 重新抛出异常
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            def _delete():
                snapshot = self._load_item(snapshot_id)
                if not snapshot:
                    return False
                
                # 从索引中移除
                self._remove_from_index("agent", snapshot["agent_id"], snapshot_id)
                
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
            def _get_stats():
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