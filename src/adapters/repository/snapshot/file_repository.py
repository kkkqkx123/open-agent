"""文件快照Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ISnapshotRepository
from ..file_base import FileBaseRepository
from ..utils import TimeUtils, IdUtils, FileUtils


class FileSnapshotRepository(FileBaseRepository, ISnapshotRepository):
    """文件快照Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件快照Repository"""
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
                
                # 保存到文件
                self._save_item(snapshot["agent_id"], snapshot_id, full_snapshot)
                
                self._log_operation("文件快照保存", True, snapshot_id)
                return snapshot_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存文件快照", e)
            raise # 重新抛出异常
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照"""
        try:
            def _load():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载文件快照", e)
            raise # 重新抛出异常
    
    async def get_snapshots(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取代理的快照列表"""
        try:
            def _get():
                snapshots = self._list_items(agent_id)
                
                # 按创建时间倒序排序
                snapshots = TimeUtils.sort_by_time(snapshots, "created_at", True)
                snapshots = snapshots[:limit]
                
                self._log_operation("获取文件快照列表", True, f"{agent_id}, 共{len(snapshots)}条")
                return snapshots
            
            return await asyncio.get_event_loop().run_in_executor(None, _get)
            
        except Exception as e:
            self._handle_exception("获取文件快照列表", e)
            raise # 重新抛出异常
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            def _delete():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除文件快照", e)
            raise # 重新抛出异常
    
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            def _get_stats():
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
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_stats)
            
        except Exception as e:
            self._handle_exception("获取文件快照统计信息", e)
            raise # 重新抛出异常