"""状态历史管理服务实现

提供状态变更历史的记录、查询和回放功能。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.interfaces.state.history import IStateHistoryManager
from src.interfaces.state.serializer import IStateSerializer
from src.interfaces.repository import IHistoryRepository
from src.interfaces.state import StateHistoryEntry, AbstractStateHistoryEntry
from src.core.state.core.base import BaseStateHistoryManager
from src.core.state.entities import StateDiff


logger = logging.getLogger(__name__)


class StateHistoryService(BaseStateHistoryManager):
    """状态历史管理服务实现
    
    提供完整的历史记录管理功能。
    """
    
    def __init__(self,
                 history_repository: IHistoryRepository,
                 serializer: Optional[IStateSerializer] = None,
                 max_history_size: int = 1000):
        """初始化历史管理服务
        
        Args:
            history_repository: 历史Repository
            serializer: 序列化器
            max_history_size: 最大历史记录数量
        """
        super().__init__(max_history_size)
        self._history_repository = history_repository
        self._serializer = serializer
        
        # 内存缓存
        self._history_cache: Dict[str, List[AbstractStateHistoryEntry]] = {}
        self._agent_history_index: Dict[str, List[str]] = {}
    
    def _create_history_entry(self, agent_id: str, old_state: Dict[str, Any],
                             new_state: Dict[str, Any], action: str) -> StateHistoryEntry:
        """创建历史记录条目"""
        from uuid import uuid4
        state_diff = StateDiff.calculate(old_state, new_state)
        
        return StateHistoryEntry(
            history_id=str(uuid4()),
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            action=action,
            state_diff=state_diff.to_dict()
        )

    async def record_state_change_async(self, agent_id: str, old_state: Dict[str, Any],
                                       new_state: Dict[str, Any], action: str) -> str:
        """异步记录状态变化"""
        try:
            # 创建历史记录条目
            entry = self._create_history_entry(agent_id, old_state, new_state, action)
            
            # 压缩差异数据
            if self._serializer:
                diff_data = self._serializer.serialize_state(entry.state_diff)
                entry.compressed_diff = self._serializer.compress_data(diff_data)
            
            # 转换为字典格式保存到Repository
            entry_dict = {
                "history_id": entry.history_id,
                "agent_id": entry.agent_id,
                "timestamp": entry.timestamp,
                "action": entry.action,
                "state_diff": entry.state_diff,
                "metadata": entry.metadata or {}
            }
            
            # 保存到Repository
            await self._history_repository.save_history(entry_dict)
            
            # 更新缓存
            self._update_cache(entry)
            
            # 清理旧记录
            await self.cleanup_old_entries_async(agent_id)
            
            logger.debug(f"状态变化记录成功: {entry.history_id}")
            return entry.history_id
            
        except Exception as e:
            logger.error(f"记录状态变化失败: {e}")
            raise
    
    async def get_state_history_async(self, agent_id: str, limit: Optional[int] = None) -> List[AbstractStateHistoryEntry]:
        """异步获取状态历史"""
        try:
            if limit is None:
                limit = 10
            
            # 先从缓存获取
            if agent_id in self._history_cache:
                cached_entries = self._history_cache[agent_id]
                if len(cached_entries) >= limit:
                    return cached_entries[-limit:]  # type: ignore
            
            # 从Repository获取
            entry_dicts = await self._history_repository.get_history(agent_id, limit)
            
            # 转换为StateHistoryEntry对象
            entries = []
            for entry_dict in entry_dicts:
                entry = StateHistoryEntry(
                    history_id=entry_dict["history_id"],
                    agent_id=entry_dict["agent_id"],
                    timestamp=entry_dict["timestamp"],
                    action=entry_dict["action"],
                    state_diff=entry_dict.get("state_diff", {}),
                    metadata=entry_dict.get("metadata", {})
                )
                entries.append(entry)
            
            # 更新缓存
            self._history_cache[agent_id] = entries
            
            return entries[-limit:]  # type: ignore
            
        except Exception as e:
            logger.error(f"获取状态历史失败: {e}")
            return []
    
    def replay_history(self, agent_id: str, base_state: Dict[str, Any],
                      until_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """重放历史记录到指定时间点"""
        try:
            current_state = base_state.copy()
            history_entries = self.get_state_history(agent_id, limit=1000)
            
            # 按时间排序
            history_entries.sort(key=lambda x: datetime.fromisoformat(x.timestamp))
            
            for entry in history_entries:
                if until_timestamp and datetime.fromisoformat(entry.timestamp) > until_timestamp:
                    break
                
                # 应用状态差异
                if entry.state_diff:
                    state_diff = StateDiff.from_dict(entry.state_diff)
                    current_state = state_diff.apply_to_state(current_state)
            
            logger.debug(f"历史重放完成，agent_id: {agent_id}")
            return current_state
            
        except Exception as e:
            logger.error(f"重放历史记录失败: {e}")
            return base_state
    
    async def cleanup_old_entries_async(self, agent_id: str, max_entries: int = 1000) -> int:
        """异步清理旧的历史记录"""
        try:
            # 获取当前历史记录数量
            current_entries = await self.get_state_history_async(agent_id, limit=1000)
            
            if len(current_entries) <= max_entries:
                return 0
            
            # 计算需要删除的数量
            to_delete_count = len(current_entries) - max_entries
            entries_to_delete = current_entries[:to_delete_count]
            
            # 并发从Repository删除
            delete_tasks = [
                self._history_repository.delete_history(entry.history_id)
                for entry in entries_to_delete
            ]
            delete_results = await asyncio.gather(*delete_tasks)
            deleted_count = sum(1 for result in delete_results if result)
            
            # 更新缓存
            if agent_id in self._history_cache:
                self._history_cache[agent_id] = current_entries[to_delete_count:]  # type: ignore
            
            logger.info(f"清理了 {deleted_count} 条历史记录，agent_id: {agent_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理历史记录失败: {e}")
            return 0
    
    async def get_history_statistics_async(self) -> Dict[str, Any]:
        """异步获取历史统计信息"""
        try:
            # 从Repository获取统计信息
            stats = await self._history_repository.get_history_statistics()
            
            # 添加缓存统计
            cache_stats = {
                "cached_agents": len(self._history_cache),
                "total_cached_entries": sum(len(entries) for entries in self._history_cache.values())
            }
            
            stats.update(cache_stats)
            return stats
            
        except Exception as e:
            logger.error(f"获取历史统计信息失败: {e}")
            return {}
    
    async def clear_history_async(self, agent_id: str) -> bool:
        """异步清空指定代理的历史记录"""
        try:
            # 从Repository删除
            success = await self._history_repository.clear_agent_history(agent_id)
            
            # 清空缓存
            if agent_id in self._history_cache:
                del self._history_cache[agent_id]
            if agent_id in self._agent_history_index:
                del self._agent_history_index[agent_id]
            
            logger.info(f"清空历史记录，agent_id: {agent_id}")
            return success
            
        except Exception as e:
            logger.error(f"清空历史记录失败: {e}")
            return False
    
    async def get_state_at_time_async(self, agent_id: str, target_time: datetime) -> Optional[Dict[str, Any]]:
        """异步获取指定时间点的状态"""
        try:
            # 获取历史记录
            history_entries = await self.get_state_history_async(agent_id, limit=1000)
            
            # 找到目标时间点之前的历史记录
            relevant_entries = [
                entry for entry in history_entries
                if datetime.fromisoformat(entry.timestamp) <= target_time
            ]
            
            if not relevant_entries:
                return None
            
            # 重放到目标时间点
            base_state = {}
            return self.replay_history(agent_id, base_state, target_time)
            
        except Exception as e:
            logger.error(f"获取指定时间点状态失败: {e}")
            return None
    
    def _update_cache(self, entry: StateHistoryEntry) -> None:
        """更新缓存"""
        # 更新代理历史索引
        if entry.agent_id not in self._agent_history_index:
            self._agent_history_index[entry.agent_id] = []
        
        self._agent_history_index[entry.agent_id].append(entry.history_id)
        
        # 更新历史缓存
        if entry.agent_id not in self._history_cache:
            self._history_cache[entry.agent_id] = []
        
        self._history_cache[entry.agent_id].append(entry)  # type: ignore
        
        # 限制缓存大小
        if len(self._history_cache[entry.agent_id]) > self.max_history_size:
            self._history_cache[entry.agent_id] = self._history_cache[entry.agent_id][-self.max_history_size:]
    
    def _cleanup_cache(self, agent_id: str) -> None:
        """清理缓存"""
        if agent_id in self._history_cache:
            entries = self._history_cache[agent_id]
            if len(entries) > self.max_history_size:
                self._history_cache[agent_id] = entries[-self.max_history_size:]  # type: ignore
        
        if agent_id in self._agent_history_index:
            history_ids = self._agent_history_index[agent_id]
            if len(history_ids) > self.max_history_size:
                self._agent_history_index[agent_id] = history_ids[-self.max_history_size:]


class StateHistoryAnalyzer:
    """状态历史分析器
    
    提供历史数据的分析功能。
    """
    
    def __init__(self, history_service: StateHistoryService):
        """初始化分析器
        
        Args:
            history_service: 历史管理服务
        """
        self._history_service = history_service
    
    def analyze_state_changes(self, agent_id: str, 
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """分析状态变化
        
        Args:
            agent_id: 代理ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            分析结果
        """
        try:
            history_entries = self._history_service.get_state_history(agent_id, limit=1000)
            
            # 过滤时间范围
            if start_time or end_time:
                filtered_entries = []
                for entry in history_entries:
                    entry_timestamp = datetime.fromisoformat(entry.timestamp)
                    if start_time and entry_timestamp < start_time:
                        continue
                    if end_time and entry_timestamp > end_time:
                        continue
                    filtered_entries.append(entry)
                history_entries = filtered_entries
            
            # 统计分析
            analysis = {
                "total_changes": len(history_entries),
                "action_counts": {},
                "field_change_frequency": {},
                "change_frequency": {},
                "time_distribution": {}
            }
            
            # 统计动作类型
            for entry in history_entries:
                action = entry.action
                analysis["action_counts"][action] = analysis["action_counts"].get(action, 0) + 1
                
                # 统计字段变化频率
                if entry.state_diff:
                    for key in entry.state_diff.keys():
                        analysis["field_change_frequency"][key] = analysis["field_change_frequency"].get(key, 0) + 1
                
                # 统计时间分布（按小时）
                entry_datetime = datetime.fromisoformat(entry.timestamp)
                hour = entry_datetime.hour
                analysis["time_distribution"][hour] = analysis["time_distribution"].get(hour, 0) + 1
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析状态变化失败: {e}")
            return {}
    
    def detect_anomalies(self, agent_id: str) -> List[Dict[str, Any]]:
        """检测状态异常
        
        Args:
            agent_id: 代理ID
            
        Returns:
            异常列表
        """
        try:
            history_entries = self._history_service.get_state_history(agent_id, limit=1000)
            anomalies = []
            
            # 检测异常模式
            for i, entry in enumerate(history_entries):
                # 检测大量字段变化
                if entry.state_diff and len(entry.state_diff) > 10:
                    anomalies.append({
                        "type": "excessive_field_changes",
                        "timestamp": entry.timestamp,
                        "history_id": entry.history_id,
                        "details": f"字段变化数量: {len(entry.state_diff)}"
                    })
                
                # 检测频繁变化
                if i > 0:
                    current_timestamp = datetime.fromisoformat(entry.timestamp)
                    prev_timestamp = datetime.fromisoformat(history_entries[i-1].timestamp)
                    time_diff = (current_timestamp - prev_timestamp).total_seconds()
                    if time_diff < 1:  # 1秒内多次变化
                        anomalies.append({
                            "type": "rapid_changes",
                            "timestamp": entry.timestamp,
                            "history_id": entry.history_id,
                            "details": f"变化间隔: {time_diff}秒"
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"检测状态异常失败: {e}")
            return []