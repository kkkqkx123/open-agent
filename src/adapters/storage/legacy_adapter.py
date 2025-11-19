"""向后兼容的存储适配器

提供向后兼容的存储适配器，确保现有代码可以无缝迁移到新架构。
"""

import logging
from typing import Dict, Any, List, Optional

from src.core.state.interfaces import IStateStorageAdapter
from src.core.state.entities import StateSnapshot, StateHistoryEntry
from src.core.state.exceptions import StorageError
from .base import BaseStateStorageAdapter


logger = logging.getLogger(__name__)


class LegacyStorageAdapter(BaseStateStorageAdapter):
    """向后兼容的存储适配器
    
    提供与旧版本存储系统兼容的接口，确保现有代码可以无缝迁移。
    """
    
    def __init__(self, backend: IStateStorageAdapter):
        """初始化向后兼容的存储适配器
        
        Args:
            backend: 新的存储适配器
        """
        super().__init__(backend)
        
        # 旧版本接口映射
        self._legacy_method_mapping = {
            "save": "save_history_entry",
            "load": "get_history_entry",
            "update": "update_history_entry",
            "delete": "delete_history_entry",
            "list": "get_history_entries",
            "exists": "history_entry_exists",
            "count": "get_history_count"
        }
        
        logger.info("LegacyStorageAdapter initialized")
    
    def save(self, data: Dict[str, Any]) -> str:
        """保存数据（旧版本接口）
        
        Args:
            data: 要保存的数据
            
        Returns:
            保存的数据ID
        """
        try:
            # 检查数据类型并转换
            if "type" in data:
                if data["type"] == "history_entry":
                    # 转换为历史记录条目
                    entry = StateHistoryEntry.from_dict(data)
                    success = self.save_history_entry(entry)
                    return entry.history_id if success else ""
                elif data["type"] == "snapshot":
                    # 转换为状态快照
                    snapshot = StateSnapshot.from_dict(data)
                    success = self.save_snapshot(snapshot)
                    return snapshot.snapshot_id if success else ""
            
            # 默认作为历史记录条目处理
            entry = StateHistoryEntry.from_dict(data)
            success = self.save_history_entry(entry)
            return entry.history_id if success else ""
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return ""
    
    def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据（旧版本接口）
        
        Args:
            id: 数据ID
            
        Returns:
            加载的数据或None
        """
        try:
            # 首先尝试作为历史记录条目加载
            entry = self.get_history_entry(id)
            if entry:
                return entry.to_dict()
            
            # 然后尝试作为状态快照加载
            snapshot = self.load_snapshot(id)
            if snapshot:
                return snapshot.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load data {id}: {e}")
            return None
    
    def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据（旧版本接口）
        
        Args:
            id: 数据ID
            updates: 更新数据
            
        Returns:
            是否更新成功
        """
        try:
            # 尝试更新历史记录条目
            success = self.update_history_entry(id, updates)
            if success:
                return True
            
            # 如果历史记录条目不存在，尝试更新状态快照
            # 注意：快照通常不支持更新，这里只是示例
            logger.warning(f"Snapshot update not supported for {id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update data {id}: {e}")
            return False
    
    def delete(self, id: str) -> bool:
        """删除数据（旧版本接口）
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        try:
            # 尝试删除历史记录条目
            success = self.delete_history_entry(id)
            if success:
                return True
            
            # 尝试删除状态快照
            success = self.delete_snapshot(id)
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete data {id}: {e}")
            return False
    
    def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据（旧版本接口）
        
        Args:
            filters: 过滤条件
            limit: 返回数量限制
            
        Returns:
            数据列表
        """
        try:
            # 根据类型过滤
            data_type = filters.get("type")
            
            if data_type == "history_entry" or data_type is None:
                # 获取历史记录条目
                entries = self.get_history_entries(
                    filters.get("agent_id"),
                    limit or 100
                )
                return [entry.to_dict() for entry in entries]
            
            elif data_type == "snapshot":
                # 获取状态快照
                snapshots = self.get_snapshots_by_agent(
                    filters.get("agent_id"),
                    limit or 50
                )
                return [snapshot.to_dict() for snapshot in snapshots]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to list data: {e}")
            return []
    
    def exists(self, id: str) -> bool:
        """检查数据是否存在（旧版本接口）
        
        Args:
            id: 数据ID
            
        Returns:
            数据是否存在
        """
        try:
            # 检查历史记录条目是否存在
            entry = self.get_history_entry(id)
            if entry:
                return True
            
            # 检查状态快照是否存在
            snapshot = self.load_snapshot(id)
            return snapshot is not None
            
        except Exception as e:
            logger.error(f"Failed to check existence of data {id}: {e}")
            return False
    
    def count(self, filters: Dict[str, Any]) -> int:
        """计算数据数量（旧版本接口）
        
        Args:
            filters: 过滤条件
            
        Returns:
            数据数量
        """
        try:
            # 根据类型过滤
            data_type = filters.get("type")
            
            if data_type == "history_entry" or data_type is None:
                # 获取历史记录统计
                stats = self.get_history_statistics()
                return stats.get("total_entries", 0)
            
            elif data_type == "snapshot":
                # 获取快照统计
                stats = self.get_snapshot_statistics()
                return stats.get("total_snapshots", 0)
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to count data: {e}")
            return 0
    
    def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查询数据（旧版本接口）
        
        Args:
            query: 查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        try:
            # 这里需要后端支持查询方法
            # 由于接口中没有定义，我们返回空列表
            logger.warning("Query method not fully supported in legacy adapter")
            return []
            
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            return []
    
    def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存数据（旧版本接口）
        
        Args:
            data_list: 数据列表
            
        Returns:
            保存的数据ID列表
        """
        try:
            ids = []
            
            for data in data_list:
                id = self.save(data)
                if id:
                    ids.append(id)
            
            return ids
            
        except Exception as e:
            logger.error(f"Failed to batch save data: {e}")
            return []
    
    def batch_delete(self, ids: List[str]) -> int:
        """批量删除数据（旧版本接口）
        
        Args:
            ids: 数据ID列表
            
        Returns:
            删除的数据数量
        """
        try:
            count = 0
            
            for id in ids:
                if self.delete(id):
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to batch delete data: {e}")
            return 0
    
    def cleanup_old_data(self, retention_days: int) -> int:
        """清理旧数据（旧版本接口）
        
        Args:
            retention_days: 保留天数
            
        Returns:
            清理的数据数量
        """
        try:
            # 清理旧的历史记录
            count = self.cleanup_old_history(retention_days)
            
            # 注意：快照清理可能需要单独实现
            logger.info(f"Cleaned up {count} old history entries")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息（旧版本接口）
        
        Returns:
            统计信息
        """
        try:
            # 获取历史记录统计
            history_stats = self.get_history_statistics()
            
            # 获取快照统计
            snapshot_stats = self.get_snapshot_statistics()
            
            # 合并统计信息
            return {
                "history_entries": history_stats.get("total_entries", 0),
                "snapshots": snapshot_stats.get("total_snapshots", 0),
                "storage_type": history_stats.get("storage_type", "unknown"),
                "total_items": history_stats.get("total_entries", 0) + snapshot_stats.get("total_snapshots", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def health_check(self) -> bool:
        """健康检查（旧版本接口）
        
        Returns:
            是否健康
        """
        try:
            return super().health_check()
            
        except Exception as e:
            logger.error(f"Failed health check: {e}")
            return False
    
    def close(self) -> None:
        """关闭存储（旧版本接口）"""
        try:
            super().close()
            
        except Exception as e:
            logger.error(f"Failed to close storage: {e}")
    
    # 旧版本特有方法的兼容性处理
    
    def history_entry_exists(self, history_id: str) -> bool:
        """检查历史记录条目是否存在（旧版本接口）
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否存在
        """
        return self.get_history_entry(history_id) is not None
    
    def get_history_count(self, agent_id: Optional[str] = None) -> int:
        """获取历史记录数量（旧版本接口）
        
        Args:
            agent_id: 代理ID（可选）
            
        Returns:
            历史记录数量
        """
        try:
            if agent_id:
                entries = self.get_history_entries(agent_id, limit=10000)
                return len(entries)
            else:
                stats = self.get_history_statistics()
                return stats.get("total_entries", 0)
                
        except Exception as e:
            logger.error(f"Failed to get history count: {e}")
            return 0
    
    def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理历史记录（旧版本接口）
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否清空成功
        """
        try:
            return super().clear_agent_history(agent_id)
            
        except Exception as e:
            logger.error(f"Failed to clear agent history: {e}")
            return False
    
    def get_agent_history(
        self, 
        agent_id: str, 
        limit: int = 100,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """获取代理历史记录（旧版本接口）
        
        Args:
            agent_id: 代理ID
            limit: 返回数量限制
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            
        Returns:
            历史记录列表
        """
        try:
            if start_time is not None or end_time is not None:
                entries = self.get_history_entries_by_time_range(
                    start_time or 0,
                    end_time or float('inf'),
                    agent_id,
                    limit
                )
            else:
                entries = self.get_history_entries(agent_id, limit)
            
            return [entry.to_dict() for entry in entries]
            
        except Exception as e:
            logger.error(f"Failed to get agent history: {e}")
            return []
    
    def search_history(
        self, 
        query: str, 
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """搜索历史记录（旧版本接口）
        
        Args:
            query: 搜索查询
            agent_id: 代理ID（可选）
            limit: 返回数量限制
            
        Returns:
            历史记录列表
        """
        try:
            entries = self.search_history_entries(query, agent_id, limit)
            return [entry.to_dict() for entry in entries]
            
        except Exception as e:
            logger.error(f"Failed to search history: {e}")
            return []
    
    def export_history(
        self, 
        agent_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        format: str = "json"
    ) -> str:
        """导出历史记录（旧版本接口）
        
        Args:
            agent_id: 代理ID（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            format: 导出格式
            
        Returns:
            导出文件路径
        """
        try:
            return super().export_history(agent_id, start_time, end_time, format)
            
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            return ""
    
    def import_history(self, file_path: str) -> int:
        """导入历史记录（旧版本接口）
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            导入的记录数
        """
        try:
            return super().import_history(file_path)
            
        except Exception as e:
            logger.error(f"Failed to import history: {e}")
            return 0