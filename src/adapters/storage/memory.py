"""内存存储适配器实现

提供基于内存的状态存储实现，适用于开发和测试环境。
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .interfaces import IStateStorageAdapter
from src.core.state.entities import StateSnapshot, StateHistoryEntry


logger = logging.getLogger(__name__)


class MemoryStateStorageAdapter(IStateStorageAdapter):
    """内存状态存储适配器
    
    使用内存数据结构存储状态数据，适用于开发和测试。
    """
    
    def __init__(self):
        """初始化内存存储适配器"""
        # 历史记录存储
        self._history_entries: Dict[str, StateHistoryEntry] = {}
        self._agent_history_index: Dict[str, List[str]] = {}
        
        # 快照存储
        self._snapshots: Dict[str, StateSnapshot] = {}
        self._agent_snapshots_index: Dict[str, List[str]] = {}
        
        # 事务支持
        self._transaction_active = False
        self._transaction_data: Optional[Dict[str, Any]] = None
        
        logger.debug("内存存储适配器初始化完成")
    
    def save_history_entry(self, entry: StateHistoryEntry) -> bool:
        """保存历史记录条目"""
        try:
            if self._transaction_active:
                return self._save_in_transaction("history_entry", entry)
            
            self._history_entries[entry.history_id] = entry
            
            # 更新代理索引
            if entry.agent_id not in self._agent_history_index:
                self._agent_history_index[entry.agent_id] = []
            
            if entry.history_id not in self._agent_history_index[entry.agent_id]:
                self._agent_history_index[entry.agent_id].append(entry.history_id)
            
            logger.debug(f"历史记录保存成功: {entry.history_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
            return False
    
    def get_history_entries(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取历史记录条目"""
        try:
            if agent_id not in self._agent_history_index:
                return []
            
            history_ids = self._agent_history_index[agent_id][-limit:]
            entries = []
            
            for history_id in history_ids:
                if history_id in self._history_entries:
                    entries.append(self._history_entries[history_id])
            
            # 按时间倒序排列
            entries.sort(key=lambda x: x.timestamp, reverse=True)
            return entries
            
        except Exception as e:
            logger.error(f"获取历史记录失败: {e}")
            return []
    
    def delete_history_entry(self, history_id: str) -> bool:
        """删除历史记录条目"""
        try:
            if self._transaction_active:
                return self._delete_in_transaction("history_entry", history_id)
            
            if history_id not in self._history_entries:
                return False
            
            entry = self._history_entries[history_id]
            
            # 从主存储删除
            del self._history_entries[history_id]
            
            # 从代理索引删除
            if entry.agent_id in self._agent_history_index:
                if history_id in self._agent_history_index[entry.agent_id]:
                    self._agent_history_index[entry.agent_id].remove(history_id)
                
                # 如果代理没有历史记录了，删除代理索引
                if not self._agent_history_index[entry.agent_id]:
                    del self._agent_history_index[entry.agent_id]
            
            logger.debug(f"历史记录删除成功: {history_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除历史记录失败: {e}")
            return False
    
    def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录"""
        try:
            if self._transaction_active:
                return self._clear_in_transaction("agent_history", agent_id)
            
            if agent_id not in self._agent_history_index:
                return True
            
            history_ids = self._agent_history_index[agent_id].copy()
            
            # 删除所有历史记录
            for history_id in history_ids:
                if history_id in self._history_entries:
                    del self._history_entries[history_id]
            
            # 删除代理索引
            del self._agent_history_index[agent_id]
            
            logger.debug(f"代理历史记录清空成功: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"清空代理历史记录失败: {e}")
            return False
    
    def save_snapshot(self, snapshot: StateSnapshot) -> bool:
        """保存状态快照"""
        try:
            if self._transaction_active:
                return self._save_in_transaction("snapshot", snapshot)
            
            self._snapshots[snapshot.snapshot_id] = snapshot
            
            # 更新代理索引
            if snapshot.agent_id not in self._agent_snapshots_index:
                self._agent_snapshots_index[snapshot.agent_id] = []
            
            if snapshot.snapshot_id not in self._agent_snapshots_index[snapshot.agent_id]:
                self._agent_snapshots_index[snapshot.agent_id].append(snapshot.snapshot_id)
            
            logger.debug(f"快照保存成功: {snapshot.snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存快照失败: {e}")
            return False
    
    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """加载状态快照"""
        try:
            return self._snapshots.get(snapshot_id)
            
        except Exception as e:
            logger.error(f"加载快照失败: {e}")
            return None
    
    def get_snapshots_by_agent(self, agent_id: str, limit: int = 50) -> List[StateSnapshot]:
        """获取指定代理的快照列表"""
        try:
            if agent_id not in self._agent_snapshots_index:
                return []
            
            snapshot_ids = self._agent_snapshots_index[agent_id][-limit:]
            snapshots = []
            
            for snapshot_id in snapshot_ids:
                if snapshot_id in self._snapshots:
                    snapshots.append(self._snapshots[snapshot_id])
            
            # 按时间倒序排列
            snapshots.sort(key=lambda x: x.timestamp, reverse=True)
            return snapshots
            
        except Exception as e:
            logger.error(f"获取代理快照列表失败: {e}")
            return []
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除状态快照"""
        try:
            if self._transaction_active:
                return self._delete_in_transaction("snapshot", snapshot_id)
            
            if snapshot_id not in self._snapshots:
                return False
            
            snapshot = self._snapshots[snapshot_id]
            
            # 从主存储删除
            del self._snapshots[snapshot_id]
            
            # 从代理索引删除
            if snapshot.agent_id in self._agent_snapshots_index:
                if snapshot_id in self._agent_snapshots_index[snapshot.agent_id]:
                    self._agent_snapshots_index[snapshot.agent_id].remove(snapshot_id)
                
                # 如果代理没有快照了，删除代理索引
                if not self._agent_snapshots_index[snapshot.agent_id]:
                    del self._agent_snapshots_index[snapshot.agent_id]
            
            logger.debug(f"快照删除成功: {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除快照失败: {e}")
            return False
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息"""
        try:
            # 统计代理历史记录数量
            agent_counts = {}
            for agent_id, history_ids in self._agent_history_index.items():
                agent_counts[agent_id] = len(history_ids)
            
            return {
                "total_history_entries": len(self._history_entries),
                "agent_counts": agent_counts,
                "storage_type": "memory",
                "storage_size_bytes": 0  # 内存存储不计算实际大小
            }
            
        except Exception as e:
            logger.error(f"获取历史统计信息失败: {e}")
            return {}
    
    def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            # 统计代理快照数量
            agent_counts = {}
            for agent_id, snapshot_ids in self._agent_snapshots_index.items():
                agent_counts[agent_id] = len(snapshot_ids)
            
            return {
                "total_snapshots": len(self._snapshots),
                "agent_counts": agent_counts,
                "storage_type": "memory",
                "storage_size_bytes": 0  # 内存存储不计算实际大小
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
        self._transaction_data = {
            "history_entries": self._history_entries.copy(),
            "agent_history_index": {k: v.copy() for k, v in self._agent_history_index.items()},
            "snapshots": self._snapshots.copy(),
            "agent_snapshots_index": {k: v.copy() for k, v in self._agent_snapshots_index.items()},
            "operations": []
        }
        
        logger.debug("事务开始")
    
    def commit_transaction(self) -> None:
        """提交事务"""
        if not self._transaction_active:
            logger.warning("没有活动的事务，忽略提交")
            return
        
        self._transaction_active = False
        self._transaction_data = None
        
        logger.debug("事务提交")
    
    def rollback_transaction(self) -> None:
        """回滚事务"""
        if not self._transaction_active:
            logger.warning("没有活动的事务，忽略回滚")
            return
        
        # 恢复事务前的状态
        if self._transaction_data:
            self._history_entries = self._transaction_data["history_entries"]
            self._agent_history_index = self._transaction_data["agent_history_index"]
            self._snapshots = self._transaction_data["snapshots"]
            self._agent_snapshots_index = self._transaction_data["agent_snapshots_index"]
        
        self._transaction_active = False
        self._transaction_data = None
        
        logger.debug("事务回滚")
    
    def close(self) -> None:
        """关闭存储连接"""
        # 清空所有数据
        self._history_entries.clear()
        self._agent_history_index.clear()
        self._snapshots.clear()
        self._agent_snapshots_index.clear()
        
        logger.debug("内存存储适配器已关闭")
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单的健康检查：验证数据结构完整性
            total_history = len(self._history_entries)
            indexed_history = sum(len(ids) for ids in self._agent_history_index.values())
            
            total_snapshots = len(self._snapshots)
            indexed_snapshots = sum(len(ids) for ids in self._agent_snapshots_index.values())
            
            # 检查索引一致性
            if total_history != indexed_history:
                logger.warning("历史记录索引不一致")
                return False
            
            if total_snapshots != indexed_snapshots:
                logger.warning("快照索引不一致")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    def _save_in_transaction(self, data_type: str, data: Any) -> bool:
        """在事务中保存数据"""
        if not self._transaction_data:
            return False
        
        self._transaction_data["operations"].append(("save", data_type, data))
        return True
    
    def _delete_in_transaction(self, data_type: str, data_id: str) -> bool:
        """在事务中删除数据"""
        if not self._transaction_data:
            return False
        
        self._transaction_data["operations"].append(("delete", data_type, data_id))
        return True
    
    def _clear_in_transaction(self, data_type: str, agent_id: str) -> bool:
        """在事务中清空数据"""
        if not self._transaction_data:
            return False
        
        self._transaction_data["operations"].append(("clear", data_type, agent_id))
        return True
    
    def get_all_agents(self) -> List[str]:
        """获取所有代理ID
        
        Returns:
            代理ID列表
        """
        agents = set(self._agent_history_index.keys())
        agents.update(self._agent_snapshots_index.keys())
        return list(agents)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息
        
        Returns:
            存储信息字典
        """
        return {
            "storage_type": "memory",
            "history_entries": len(self._history_entries),
            "snapshots": len(self._snapshots),
            "agents": len(self.get_all_agents()),
            "transaction_active": self._transaction_active
        }