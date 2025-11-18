"""状态历史管理服务实现

提供状态变更历史的记录、查询和回放功能。
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.state.interfaces import IStateHistoryManager, IStateSerializer, IStateStorageAdapter
from src.core.state.base import BaseStateHistoryManager
from src.core.state.entities import StateHistoryEntry, StateDiff


logger = logging.getLogger(__name__)


class StateHistoryService(BaseStateHistoryManager):
    """状态历史管理服务实现
    
    提供完整的历史记录管理功能。
    """
    
    def __init__(self, 
                 storage_adapter: IStateStorageAdapter,
                 serializer: Optional[IStateSerializer] = None,
                 max_history_size: int = 1000):
        """初始化历史管理服务
        
        Args:
            storage_adapter: 存储适配器
            serializer: 序列化器
            max_history_size: 最大历史记录数量
        """
        super().__init__(max_history_size)
        self._storage_adapter = storage_adapter
        self._serializer = serializer
        
        # 内存缓存
        self._history_cache: Dict[str, List[StateHistoryEntry]] = {}
        self._agent_history_index: Dict[str, List[str]] = {}
    
    def record_state_change(self, agent_id: str, old_state: Dict[str, Any], 
                          new_state: Dict[str, Any], action: str) -> str:
        """记录状态变化"""
        try:
            # 创建历史记录条目
            entry = self._create_history_entry(agent_id, old_state, new_state, action)
            
            # 压缩差异数据
            if self._serializer:
                diff_data = self._serializer.serialize_state(entry.state_diff)
                entry.compressed_diff = self._serializer.compress_data(diff_data)
            
            # 保存到存储
            self._storage_adapter.save_history_entry(entry)
            
            # 更新缓存
            self._update_cache(entry)
            
            # 清理旧记录
            self.cleanup_old_entries(agent_id)
            
            logger.debug(f"状态变化记录成功: {entry.history_id}")
            return entry.history_id
            
        except Exception as e:
            logger.error(f"记录状态变化失败: {e}")
            raise
    
    def get_state_history(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取状态历史"""
        try:
            # 先从缓存获取
            if agent_id in self._history_cache:
                cached_entries = self._history_cache[agent_id]
                if len(cached_entries) >= limit:
                    return cached_entries[-limit:]
            
            # 从存储获取
            entries = self._storage_adapter.get_history_entries(agent_id, limit)
            
            # 解压缩数据
            for entry in entries:
                if entry.compressed_diff and not entry.state_diff and self._serializer:
                    compressed_data = self._serializer.decompress_data(entry.compressed_diff)
                    entry.state_diff = self._serializer.deserialize_state(compressed_data)
            
            # 更新缓存
            self._history_cache[agent_id] = entries
            
            return entries[-limit:]
            
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
            history_entries.sort(key=lambda x: x.timestamp)
            
            for entry in history_entries:
                if until_timestamp and entry.timestamp > until_timestamp:
                    break
                
                # 应用状态差异
                if entry.state_diff:
                    current_state = self._apply_state_diff(current_state, entry.state_diff)
            
            logger.debug(f"历史重放完成，agent_id: {agent_id}")
            return current_state
            
        except Exception as e:
            logger.error(f"重放历史记录失败: {e}")
            return base_state
    
    def cleanup_old_entries(self, agent_id: str, max_entries: int = 1000) -> int:
        """清理旧的历史记录"""
        try:
            # 获取当前历史记录数量
            current_entries = self.get_state_history(agent_id, limit=10000)
            
            if len(current_entries) <= max_entries:
                return 0
            
            # 计算需要删除的数量
            to_delete_count = len(current_entries) - max_entries
            entries_to_delete = current_entries[:to_delete_count]
            
            # 从存储删除
            deleted_count = 0
            for entry in entries_to_delete:
                if self._storage_adapter.delete_history_entry(entry.history_id):
                    deleted_count += 1
            
            # 更新缓存
            if agent_id in self._history_cache:
                self._history_cache[agent_id] = current_entries[to_delete_count:]
            
            logger.info(f"清理了 {deleted_count} 条历史记录，agent_id: {agent_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理历史记录失败: {e}")
            return 0
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史统计信息"""
        try:
            # 从存储适配器获取统计信息
            stats = self._storage_adapter.get_history_statistics()
            
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
    
    def clear_history(self, agent_id: str) -> bool:
        """清空指定代理的历史记录"""
        try:
            # 从存储删除
            success = self._storage_adapter.clear_agent_history(agent_id)
            
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
    
    def get_state_at_time(self, agent_id: str, target_time: datetime) -> Optional[Dict[str, Any]]:
        """获取指定时间点的状态"""
        try:
            # 获取历史记录
            history_entries = self.get_state_history(agent_id, limit=1000)
            
            # 找到目标时间点之前的历史记录
            relevant_entries = [
                entry for entry in history_entries 
                if entry.timestamp <= target_time
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
        
        self._history_cache[entry.agent_id].append(entry)
        
        # 限制缓存大小
        if len(self._history_cache[entry.agent_id]) > self.max_history_size:
            self._history_cache[entry.agent_id] = self._history_cache[entry.agent_id][-self.max_history_size:]
    
    def _cleanup_cache(self, agent_id: str) -> None:
        """清理缓存"""
        if agent_id in self._history_cache:
            entries = self._history_cache[agent_id]
            if len(entries) > self.max_history_size:
                self._history_cache[agent_id] = entries[-self.max_history_size:]
        
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
                    if start_time and entry.timestamp < start_time:
                        continue
                    if end_time and entry.timestamp > end_time:
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
                hour = entry.timestamp.hour
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
                    time_diff = (entry.timestamp - history_entries[i-1].timestamp).total_seconds()
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