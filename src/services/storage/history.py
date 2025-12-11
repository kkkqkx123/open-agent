"""历史服务

提供历史数据的存储和管理服务。
"""

import time
from typing import Dict, Any, Optional, List, AsyncIterator
from src.interfaces.storage.base import IStorage
from src.interfaces.storage.exceptions import StorageError
from src.interfaces.dependency_injection import get_logger


logger = get_logger(__name__)


class HistoryService:
    """历史服务
    
    提供历史数据的存储、查询和管理功能。
    """
    
    def __init__(self, storage: IStorage) -> None:
        """初始化历史服务
        
        Args:
            storage: 存储实例
        """
        self.storage = storage
        self.logger = get_logger(self.__class__.__name__)
    
    async def save_history_entry(
        self,
        entry_data: Dict[str, Any],
        entry_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None
    ) -> str:
        """保存历史记录
        
        Args:
            entry_data: 历史记录数据
            entry_id: 记录ID，None表示自动生成
            metadata: 元数据
            timestamp: 时间戳，None表示当前时间
            
        Returns:
            记录ID
            
        Raises:
            StorageError: 保存失败
        """
        try:
            # 准备数据
            data = entry_data.copy()
            
            # 添加历史标识
            data["type"] = "history"
            
            # 设置记录ID
            if entry_id:
                data["id"] = entry_id
            
            # 添加时间戳
            data["timestamp"] = timestamp or time.time()
            
            # 添加元数据
            if metadata:
                data["metadata"] = metadata
            
            # 添加创建时间
            data["created_at"] = time.time()
            
            # 保存历史记录
            result_id = await self.storage.save(data)
            
            self.logger.debug(f"历史记录保存成功，ID: {result_id}")
            return result_id
            
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {e}")
            raise StorageError(f"Failed to save history entry: {e}")
    
    async def load_history_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """加载历史记录
        
        Args:
            entry_id: 记录ID
            
        Returns:
            历史记录数据，不存在则返回None
            
        Raises:
            StorageError: 加载失败
        """
        try:
            # 加载数据
            data = await self.storage.load(entry_id)
            
            if data is None:
                return None
            
            # 验证数据类型
            if data.get("type") != "history":
                self.logger.warning(f"数据类型不匹配，期望'history'，实际'{data.get('type')}'")
                return None
            
            self.logger.debug(f"历史记录加载成功，ID: {entry_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"加载历史记录失败: {e}")
            raise StorageError(f"Failed to load history entry {entry_id}: {e}")
    
    async def delete_history_entry(self, entry_id: str) -> bool:
        """删除历史记录
        
        Args:
            entry_id: 记录ID
            
        Returns:
            是否删除成功
            
        Raises:
            StorageError: 删除失败
        """
        try:
            # 验证记录存在
            entry = await self.load_history_entry(entry_id)
            if entry is None:
                return False
            
            # 删除记录
            result = await self.storage.delete(entry_id)
            
            if result:
                self.logger.debug(f"历史记录删除成功，ID: {entry_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"删除历史记录失败: {e}")
            raise StorageError(f"Failed to delete history entry {entry_id}: {e}")
    
    async def list_history_entries(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order_by: str = "timestamp",
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """列出历史记录
        
        Args:
            filters: 过滤条件
            limit: 限制数量
            order_by: 排序字段
            ascending: 是否升序
            
        Returns:
            历史记录列表
            
        Raises:
            StorageError: 查询失败
        """
        try:
            # 准备过滤条件
            query_filters = filters or {}
            query_filters["type"] = "history"
            
            # 查询历史记录
            entries = await self.storage.list(query_filters, None)  # 不限制，稍后手动排序
            
            # 排序
            if order_by in ["timestamp", "created_at"]:
                entries.sort(
                    key=lambda e: e.get(order_by, 0),
                    reverse=not ascending
                )
            
            # 应用数量限制
            if limit:
                entries = entries[:limit]
            
            self.logger.debug(f"列出历史记录成功，返回 {len(entries)} 条记录")
            return entries
            
        except Exception as e:
            self.logger.error(f"列出历史记录失败: {e}")
            raise StorageError(f"Failed to list history entries: {e}")
    
    async def query_history_entries(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """查询历史记录
        
        Args:
            query: 查询语句
            params: 查询参数
            
        Returns:
            历史记录列表
            
        Raises:
            StorageError: 查询失败
        """
        try:
            # 执行查询
            all_results = await self.storage.query(query, params or {})
            
            # 过滤历史类型
            entries = [
                result for result in all_results
                if result.get("type") == "history"
            ]
            
            # 按时间戳排序
            entries.sort(
                key=lambda e: e.get("timestamp", 0),
                reverse=True
            )
            
            self.logger.debug(f"查询历史记录成功，返回 {len(entries)} 条记录")
            return entries
            
        except Exception as e:
            self.logger.error(f"查询历史记录失败: {e}")
            raise StorageError(f"Failed to query history entries: {e}")
    
    async def count_history_entries(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """计数历史记录
        
        Args:
            filters: 过滤条件
            
        Returns:
            记录数量
            
        Raises:
            StorageError: 计数失败
        """
        try:
            # 准备过滤条件
            query_filters = filters or {}
            query_filters["type"] = "history"
            
            # 计数
            count = await self.storage.count(query_filters)
            
            self.logger.debug(f"计数历史记录成功，数量: {count}")
            return count
            
        except Exception as e:
            self.logger.error(f"计数历史记录失败: {e}")
            raise StorageError(f"Failed to count history entries: {e}")
    
    async def get_history_by_time_range(
        self,
        start_time: float,
        end_time: float,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """根据时间范围获取历史记录
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            filters: 额外过滤条件
            limit: 限制数量
            
        Returns:
            历史记录列表
        """
        try:
            # 获取所有历史记录
            all_entries = await self.list_history_entries(filters)
            
            # 时间过滤
            filtered_entries = [
                entry for entry in all_entries
                if start_time <= entry.get("timestamp", 0) <= end_time
            ]
            
            # 按时间排序
            filtered_entries.sort(
                key=lambda e: e.get("timestamp", 0),
                reverse=True
            )
            
            # 应用数量限制
            if limit:
                filtered_entries = filtered_entries[:limit]
            
            return filtered_entries
            
        except Exception as e:
            self.logger.error(f"根据时间范围获取历史记录失败: {e}")
            raise StorageError(f"Failed to get history by time range: {e}")
    
    async def get_recent_history(
        self,
        time_limit: Optional[float] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取最近的历史记录
        
        Args:
            time_limit: 时间限制（秒），None表示不限制
            limit: 数量限制
            filters: 额外过滤条件
            
        Returns:
            历史记录列表
        """
        current_time = time.time()
        
        if time_limit is not None:
            start_time = current_time - time_limit
            return await self.get_history_by_time_range(start_time, current_time, filters, limit)
        else:
            return await self.list_history_entries(filters, limit)
    
    async def get_history_by_metadata(
        self,
        metadata_filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """根据元数据过滤历史记录
        
        Args:
            metadata_filters: 元数据过滤条件
            limit: 限制数量
            
        Returns:
            历史记录列表
        """
        # 获取所有历史记录
        all_entries = await self.list_history_entries(limit=limit)
        
        # 过滤元数据
        filtered_entries = []
        for entry in all_entries:
            metadata = entry.get("metadata", {})
            match = True
            
            for key, value in metadata_filters.items():
                if metadata.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered_entries.append(entry)
        
        return filtered_entries
    
    async def batch_save_history_entries(self, entries: List[Dict[str, Any]]) -> List[str]:
        """批量保存历史记录
        
        Args:
            entries: 历史记录列表
            
        Returns:
            记录ID列表
            
        Raises:
            StorageError: 批量保存失败
        """
        try:
            # 准备数据
            prepared_entries = []
            current_time = time.time()
            
            for entry_data in entries:
                data = entry_data.copy()
                data["type"] = "history"
                
                # 添加时间戳
                if "timestamp" not in data:
                    data["timestamp"] = current_time
                
                # 添加创建时间
                data["created_at"] = current_time
                
                prepared_entries.append(data)
            
            # 批量保存
            entry_ids = await self.storage.batch_save(prepared_entries)
            
            self.logger.debug(f"批量保存历史记录成功，保存了 {len(entry_ids)} 条记录")
            return entry_ids
            
        except Exception as e:
            self.logger.error(f"批量保存历史记录失败: {e}")
            raise StorageError(f"Failed to batch save history entries: {e}")
    
    async def batch_delete_history_entries(self, entry_ids: List[str]) -> int:
        """批量删除历史记录
        
        Args:
            entry_ids: 记录ID列表
            
        Returns:
            删除的数量
            
        Raises:
            StorageError: 批量删除失败
        """
        try:
            # 验证所有记录都存在且类型正确
            valid_ids = []
            for entry_id in entry_ids:
                if await self.load_history_entry(entry_id):
                    valid_ids.append(entry_id)
            
            if not valid_ids:
                return 0
            
            # 批量删除
            count = await self.storage.batch_delete(valid_ids)
            
            self.logger.debug(f"批量删除历史记录成功，删除了 {count} 条记录")
            return count
            
        except Exception as e:
            self.logger.error(f"批量删除历史记录失败: {e}")
            raise StorageError(f"Failed to batch delete history entries: {e}")
    
    def stream_history_entries(
        self,
        filters: Optional[Dict[str, Any]] = None,
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列出历史记录
        
        Args:
            filters: 过滤条件
            batch_size: 批次大小
            
        Yields:
            历史记录批次列表
        """
        # 准备过滤条件
        query_filters = filters or {}
        query_filters["type"] = "history"
        
        # 流式查询
        return self.storage.stream_list(query_filters, batch_size)
    
    async def cleanup_old_history(
        self,
        retention_days: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """清理旧历史记录
        
        Args:
            retention_days: 保留天数
            filters: 额外过滤条件
            
        Returns:
            清理的记录数量
        """
        try:
            # 计算截止时间
            current_time = time.time()
            cutoff_time = current_time - (retention_days * 24 * 3600)
            
            # 获取需要清理的记录
            old_entries = await self.get_history_by_time_range(
                0, cutoff_time, filters
            )
            
            if not old_entries:
                return 0
            
            # 批量删除
            entry_ids = [entry["id"] for entry in old_entries]
            deleted_count = await self.batch_delete_history_entries(entry_ids)
            
            self.logger.info(f"清理旧历史记录完成，删除了 {deleted_count} 条记录")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"清理旧历史记录失败: {e}")
            raise StorageError(f"Failed to cleanup old history: {e}")
    
    async def get_history_statistics(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取历史记录统计信息
        
        Args:
            filters: 过滤条件
            
        Returns:
            统计信息字典
        """
        try:
            # 获取所有历史记录
            all_entries = await self.list_history_entries(filters)
            
            if not all_entries:
                return {
                    "total_entries": 0,
                    "time_range": None,
                    "metadata_summary": {}
                }
            
            # 计算时间范围
            timestamps = [entry.get("timestamp", 0) for entry in all_entries]
            min_time = min(timestamps)
            max_time = max(timestamps)
            
            # 统计元数据
            metadata_summary: Dict[str, Dict[str, int]] = {}
            for entry in all_entries:
                metadata = entry.get("metadata", {})
                for key, value in metadata.items():
                    if key not in metadata_summary:
                        metadata_summary[key] = {}
                    
                    value_str = str(value)
                    metadata_summary[key][value_str] = metadata_summary[key].get(value_str, 0) + 1
            
            return {
                "total_entries": len(all_entries),
                "time_range": {
                    "start": min_time,
                    "end": max_time,
                    "duration": max_time - min_time
                },
                "metadata_summary": metadata_summary
            }
            
        except Exception as e:
            self.logger.error(f"获取历史记录统计信息失败: {e}")
            raise StorageError(f"Failed to get history statistics: {e}")
