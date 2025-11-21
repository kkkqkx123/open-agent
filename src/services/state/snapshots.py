"""状态快照管理服务实现

提供状态快照的创建、恢复和清理功能。
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.interfaces.state.snapshot import IStateSnapshotManager
from src.interfaces.state.serializer import IStateSerializer
from src.interfaces.state.storage.adapter import IStateStorageAdapter
from src.interfaces.state.concrete import StateSnapshot
from src.core.state.base import BaseStateSnapshotManager


logger = logging.getLogger(__name__)


class StateSnapshotService(BaseStateSnapshotManager):
    """状态快照管理服务实现
    
    提供完整的快照管理功能。
    """
    
    def __init__(self, 
                 storage_adapter: IStateStorageAdapter,
                 serializer: Optional[IStateSerializer] = None,
                 max_snapshots_per_agent: int = 50):
        """初始化快照管理服务
        
        Args:
            storage_adapter: 存储适配器
            serializer: 序列化器
            max_snapshots_per_agent: 每个代理的最大快照数量
        """
        super().__init__(max_snapshots_per_agent)
        self._storage_adapter = storage_adapter
        self._serializer = serializer
        
        # 内存缓存
        self._snapshot_cache: Dict[str, StateSnapshot] = {}
        self._agent_snapshots_index: Dict[str, List[str]] = {}
    
    def create_snapshot(self, agent_id: str, state_data: Dict[str, Any], 
                       snapshot_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建状态快照"""
        try:
            # 创建快照对象
            snapshot = self._create_snapshot(agent_id, state_data, snapshot_name, metadata)
            
            # 序列化和压缩状态数据
            if self._serializer:
                serialized_data = self._serializer.serialize_state(state_data)
                compressed_data = self._serializer.compress_data(serialized_data)
                snapshot.compressed_data = compressed_data
                snapshot.size_bytes = len(compressed_data)
            
            # 保存到存储
            self._storage_adapter.save_snapshot(snapshot)
            
            # 更新缓存
            self._update_cache(snapshot)
            
            # 清理旧快照
            self.cleanup_old_snapshots(agent_id)
            
            logger.debug(f"快照创建成功: {snapshot.snapshot_id}")
            return snapshot.snapshot_id
            
        except Exception as e:
            logger.error(f"创建快照失败: {e}")
            raise
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """恢复状态快照"""
        try:
            # 先从缓存获取
            if snapshot_id in self._snapshot_cache:
                snapshot = self._snapshot_cache[snapshot_id]
            else:
                # 从存储获取
                snapshot = self._storage_adapter.load_snapshot(snapshot_id)
                if not snapshot:
                    logger.warning(f"快照不存在: {snapshot_id}")
                    return None
                
                # 解压缩状态数据
                if snapshot.compressed_data and not snapshot.domain_state and self._serializer:
                    compressed_data = self._serializer.decompress_data(snapshot.compressed_data)
                    snapshot.domain_state = self._serializer.deserialize_state(compressed_data)
                
                # 更新缓存
                self._snapshot_cache[snapshot_id] = snapshot
            
            logger.debug(f"快照恢复成功: {snapshot_id}")
            return snapshot
            
        except Exception as e:
            logger.error(f"恢复快照失败: {e}")
            return None
    
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定代理的快照列表"""
        try:
            # 先从缓存索引获取
            if agent_id in self._agent_snapshots_index:
                snapshot_ids = self._agent_snapshots_index[agent_id][-limit:]
                snapshots = []
                
                for snapshot_id in snapshot_ids:
                    if snapshot_id in self._snapshot_cache:
                        snapshot = self._snapshot_cache[snapshot_id]
                    else:
                        snapshot = self._storage_adapter.load_snapshot(snapshot_id)
                        if snapshot:
                            self._snapshot_cache[snapshot_id] = snapshot
                    
                    if snapshot:
                        snapshots.append(snapshot)
                
                return snapshots
            
            # 从存储获取
            snapshots = self._storage_adapter.get_snapshots_by_agent(agent_id, limit)
            
            # 解压缩数据并更新缓存
            for snapshot in snapshots:
                if snapshot.compressed_data and not snapshot.domain_state and self._serializer:
                    compressed_data = self._serializer.decompress_data(snapshot.compressed_data)
                    snapshot.domain_state = self._serializer.deserialize_state(compressed_data)
                
                self._snapshot_cache[snapshot.snapshot_id] = snapshot
            
            # 更新索引
            if agent_id not in self._agent_snapshots_index:
                self._agent_snapshots_index[agent_id] = []
            
            for snapshot in snapshots:
                if snapshot.snapshot_id not in self._agent_snapshots_index[agent_id]:
                    self._agent_snapshots_index[agent_id].append(snapshot.snapshot_id)
            
            return snapshots
            
        except Exception as e:
            logger.error(f"获取代理快照列表失败: {e}")
            return []
    
    def cleanup_old_snapshots(self, agent_id: str, max_snapshots: int = 50) -> int:
        """清理旧快照"""
        try:
            # 获取当前快照列表
            snapshots = self.get_snapshots_by_agent(agent_id, limit=1000)
            
            if len(snapshots) <= max_snapshots:
                return 0
            
            # 按时间排序，删除最旧的快照
            snapshots.sort(key=lambda x: x.timestamp)
            to_delete = snapshots[:-max_snapshots]
            
            deleted_count = 0
            for snapshot in to_delete:
                if self._storage_adapter.delete_snapshot(snapshot.snapshot_id):
                    # 从缓存删除
                    if snapshot.snapshot_id in self._snapshot_cache:
                        del self._snapshot_cache[snapshot.snapshot_id]
                    
                    # 从索引删除
                    if agent_id in self._agent_snapshots_index:
                        if snapshot.snapshot_id in self._agent_snapshots_index[agent_id]:
                            self._agent_snapshots_index[agent_id].remove(snapshot.snapshot_id)
                    
                    deleted_count += 1
            
            logger.info(f"清理了 {deleted_count} 个旧快照，agent_id: {agent_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧快照失败: {e}")
            return 0
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除指定快照"""
        try:
            # 从存储删除
            success = self._storage_adapter.delete_snapshot(snapshot_id)
            
            if success:
                # 从缓存删除
                if snapshot_id in self._snapshot_cache:
                    snapshot = self._snapshot_cache[snapshot_id]
                    del self._snapshot_cache[snapshot_id]
                    
                    # 从索引删除
                    agent_id = snapshot.agent_id
                    if agent_id in self._agent_snapshots_index:
                        if snapshot_id in self._agent_snapshots_index[agent_id]:
                            self._agent_snapshots_index[agent_id].remove(snapshot_id)
                
                logger.debug(f"快照删除成功: {snapshot_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除快照失败: {e}")
            return False
    
    def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            # 从存储适配器获取统计信息
            stats = self._storage_adapter.get_snapshot_statistics()
            
            # 添加缓存统计
            cache_stats = {
                "cached_snapshots": len(self._snapshot_cache),
                "cached_agents": len(self._agent_snapshots_index),
                "total_cached_size": sum(
                    snapshot.size_bytes for snapshot in self._snapshot_cache.values()
                )
            }
            
            stats.update(cache_stats)
            return stats
            
        except Exception as e:
            logger.error(f"获取快照统计信息失败: {e}")
            return {}
    
    def find_snapshots_by_name(self, agent_id: str, name_pattern: str) -> List[StateSnapshot]:
        """根据名称模式查找快照
        
        Args:
            agent_id: 代理ID
            name_pattern: 名称模式（支持通配符）
            
        Returns:
            匹配的快照列表
        """
        try:
            snapshots = self.get_snapshots_by_agent(agent_id, limit=1000)
            
            # 简单的模式匹配
            import fnmatch
            matched_snapshots = []
            
            for snapshot in snapshots:
                if fnmatch.fnmatch(snapshot.snapshot_name, name_pattern):
                    matched_snapshots.append(snapshot)
            
            return matched_snapshots
            
        except Exception as e:
            logger.error(f"根据名称查找快照失败: {e}")
            return []
    
    def get_snapshots_in_time_range(self, agent_id: str, 
                                   start_time: datetime, 
                                   end_time: datetime) -> List[StateSnapshot]:
        """获取指定时间范围内的快照
        
        Args:
            agent_id: 代理ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            时间范围内的快照列表
        """
        try:
            snapshots = self.get_snapshots_by_agent(agent_id, limit=1000)
            
            # 过滤时间范围
            filtered_snapshots = []
            for snapshot in snapshots:
                snapshot_time = datetime.fromisoformat(snapshot.timestamp)
                if start_time <= snapshot_time <= end_time:
                    filtered_snapshots.append(snapshot)
            
            return filtered_snapshots
            
        except Exception as e:
            logger.error(f"获取时间范围内快照失败: {e}")
            return []
    
    def create_auto_snapshot(self, agent_id: str, state_data: Dict[str, Any], 
                           trigger_reason: str = "") -> str:
        """创建自动快照
        
        Args:
            agent_id: 代理ID
            state_data: 状态数据
            trigger_reason: 触发原因
            
        Returns:
            快照ID
        """
        snapshot_name = f"auto_{trigger_reason}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metadata = {
            "auto_created": True,
            "trigger_reason": trigger_reason,
            "created_at": datetime.now().isoformat()
        }
        
        return self.create_snapshot(agent_id, state_data, snapshot_name, metadata)
    
    def _update_cache(self, snapshot: StateSnapshot) -> None:
        """更新缓存"""
        # 更新快照缓存
        self._snapshot_cache[snapshot.snapshot_id] = snapshot
        
        # 更新代理快照索引
        if snapshot.agent_id not in self._agent_snapshots_index:
            self._agent_snapshots_index[snapshot.agent_id] = []
        
        if snapshot.snapshot_id not in self._agent_snapshots_index[snapshot.agent_id]:
            self._agent_snapshots_index[snapshot.agent_id].append(snapshot.snapshot_id)
        
        # 限制缓存大小
        if len(self._agent_snapshots_index[snapshot.agent_id]) > self.max_snapshots_per_agent:
            # 删除最旧的快照ID
            oldest_snapshot_id = self._agent_snapshots_index[snapshot.agent_id].pop(0)
            if oldest_snapshot_id in self._snapshot_cache:
                del self._snapshot_cache[oldest_snapshot_id]
    
    def _cleanup_cache(self, agent_id: str) -> None:
        """清理缓存"""
        if agent_id in self._agent_snapshots_index:
            snapshot_ids = self._agent_snapshots_index[agent_id]
            if len(snapshot_ids) > self.max_snapshots_per_agent:
                # 保留最新的快照
                keep_snapshot_ids = snapshot_ids[-self.max_snapshots_per_agent:]
                self._agent_snapshots_index[agent_id] = keep_snapshot_ids
                
                # 删除超出限制的快照缓存
                for snapshot_id in snapshot_ids:
                    if snapshot_id not in keep_snapshot_ids and snapshot_id in self._snapshot_cache:
                        del self._snapshot_cache[snapshot_id]


class SnapshotScheduler:
    """快照调度器
    
    提供自动快照调度功能。
    """
    
    def __init__(self, snapshot_service: StateSnapshotService):
        """初始化调度器
        
        Args:
            snapshot_service: 快照管理服务
        """
        self._snapshot_service = snapshot_service
        self._schedules: Dict[str, Dict[str, Any]] = {}
    
    def schedule_auto_snapshot(self, agent_id: str, interval_minutes: int = 60, 
                             max_snapshots: int = 24) -> None:
        """调度自动快照
        
        Args:
            agent_id: 代理ID
            interval_minutes: 快照间隔（分钟）
            max_snapshots: 最大快照数量
        """
        self._schedules[agent_id] = {
            "interval_minutes": interval_minutes,
            "max_snapshots": max_snapshots,
            "last_snapshot": None
        }
        
        logger.info(f"为代理 {agent_id} 调度自动快照，间隔: {interval_minutes} 分钟")
    
    def check_and_create_snapshot(self, agent_id: str, domain_state: Dict[str, Any]) -> Optional[str]:
        """检查并创建自动快照
        
        Args:
            agent_id: 代理ID
            domain_state: 当前域状态
            
        Returns:
            快照ID，如果未创建则返回None
        """
        if agent_id not in self._schedules:
            return None
        
        schedule = self._schedules[agent_id]
        now = datetime.now()
        
        # 检查是否需要创建快照
        if (schedule["last_snapshot"] is None or 
            (now - schedule["last_snapshot"]).total_seconds() >= schedule["interval_minutes"] * 60):
            
            snapshot_id = self._snapshot_service.create_auto_snapshot(
                agent_id, domain_state, "scheduled"
            )
            
            schedule["last_snapshot"] = now
            
            # 清理旧快照
            self._snapshot_service.cleanup_old_snapshots(agent_id, schedule["max_snapshots"])
            
            logger.debug(f"为代理 {agent_id} 创建自动快照: {snapshot_id}")
            return snapshot_id
        
        return None
    
    def remove_schedule(self, agent_id: str) -> bool:
        """移除自动快照调度
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否成功移除
        """
        if agent_id in self._schedules:
            del self._schedules[agent_id]
            logger.info(f"移除代理 {agent_id} 的自动快照调度")
            return True
        return False
    
    def get_schedules(self) -> Dict[str, Dict[str, Any]]:
        """获取所有调度信息"""
        return self._schedules.copy()