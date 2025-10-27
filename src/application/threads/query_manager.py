"""Thread查询管理器实现"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re

from ...domain.threads.interfaces import IThreadManager

logger = logging.getLogger(__name__)


class ThreadQueryManager:
    """Thread查询管理器，提供高级搜索和过滤功能"""
    
    def __init__(self, thread_manager: IThreadManager):
        """初始化查询管理器
        
        Args:
            thread_manager: Thread管理器
        """
        self.thread_manager = thread_manager
    
    async def search_threads(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """高级搜索Threads
        
        Args:
            filters: 过滤条件
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            搜索结果列表
        """
        filters = filters or {}
        
        # 获取所有threads
        all_threads = await self.thread_manager.list_threads()
        
        # 应用过滤器
        filtered_threads = []
        for thread in all_threads:
            if await self._matches_filters(thread, filters):
                filtered_threads.append(thread)
        
        # 应用分页
        if offset:
            filtered_threads = filtered_threads[offset:]
        if limit:
            filtered_threads = filtered_threads[:limit]
        
        logger.info(f"搜索Threads完成，共{len(filtered_threads)}个匹配结果")
        return filtered_threads
    
    async def _matches_filters(self, thread: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查Thread是否匹配过滤条件
        
        Args:
            thread: Thread信息
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        for key, value in filters.items():
            if key == "status":
                if not self._match_status(thread, value):
                    return False
            elif key == "metadata":
                if not self._match_metadata(thread, value):
                    return False
            elif key == "created_after":
                if not self._match_created_after(thread, value):
                    return False
            elif key == "created_before":
                if not self._match_created_before(thread, value):
                    return False
            elif key == "graph_id":
                if not self._match_graph_id(thread, value):
                    return False
            elif key == "thread_id":
                if not self._match_thread_id(thread, value):
                    return False
            elif key == "contains_text":
                if not await self._match_contains_text(thread, value):
                    return False
        return True
    
    def _match_status(self, thread: Dict[str, Any], status: str) -> bool:
        """匹配状态"""
        thread_status = thread.get("status", "unknown")
        return thread_status == status
    
    def _match_metadata(self, thread: Dict[str, Any], metadata_filters: Dict[str, Any]) -> bool:
        """匹配元数据"""
        thread_metadata = thread.get("metadata", {})
        
        for key, expected_value in metadata_filters.items():
            actual_value = thread_metadata.get(key)
            
            # 如果是字典，递归匹配
            if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                if not self._match_nested_dict(actual_value, expected_value):
                    return False
            # 如果是列表，检查是否包含期望值
            elif isinstance(expected_value, list) and isinstance(actual_value, list):
                if not all(item in actual_value for item in expected_value):
                    return False
            # 简单值匹配
            else:
                if actual_value != expected_value:
                    return False
        
        return True
    
    def _match_nested_dict(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """匹配嵌套字典"""
        for key, expected_value in expected.items():
            if key not in actual:
                return False
            
            actual_value = actual[key]
            if isinstance(expected_value, dict) and isinstance(actual_value, dict):
                if not self._match_nested_dict(actual_value, expected_value):
                    return False
            elif actual_value != expected_value:
                return False
        
        return True
    
    def _match_created_after(self, thread: Dict[str, Any], created_after: datetime) -> bool:
        """匹配创建时间（之后）"""
        created_at_str = thread.get("created_at")
        if not created_at_str:
            return True  # 如果没有创建时间，认为匹配
        
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            return created_at >= created_after
        except ValueError:
            return True  # 解析失败时认为匹配
    
    def _match_created_before(self, thread: Dict[str, Any], created_before: datetime) -> bool:
        """匹配创建时间（之前）"""
        created_at_str = thread.get("created_at")
        if not created_at_str:
            return True  # 如果没有创建时间，认为匹配
        
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            return created_at <= created_before
        except ValueError:
            return True  # 解析失败时认为匹配
    
    def _match_graph_id(self, thread: Dict[str, Any], graph_id: str) -> bool:
        """匹配图ID"""
        return thread.get("graph_id", "") == graph_id
    
    def _match_thread_id(self, thread: Dict[str, Any], thread_id: str) -> bool:
        """匹配Thread ID"""
        return thread.get("thread_id", "") == thread_id
    
    async def _match_contains_text(self, thread: Dict[str, Any], text: str) -> bool:
        """匹配包含文本"""
        # 搜索thread的所有字段中是否包含文本
        thread_str = str(thread).lower()
        return text.lower() in thread_str
    
    async def aggregate_threads_by_status(self) -> Dict[str, int]:
        """按状态聚合Threads统计
        
        Returns:
            状态统计字典
        """
        all_threads = await self.thread_manager.list_threads()
        
        status_counts = {}
        for thread in all_threads:
            status = thread.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return status_counts
    
    async def aggregate_threads_by_graph_id(self) -> Dict[str, int]:
        """按图ID聚合Threads统计
        
        Returns:
            图ID统计字典
        """
        all_threads = await self.thread_manager.list_threads()
        
        graph_counts = {}
        for thread in all_threads:
            graph_id = thread.get("graph_id", "unknown")
            graph_counts[graph_id] = graph_counts.get(graph_id, 0) + 1
        
        return graph_counts
    
    async def get_thread_statistics(self) -> Dict[str, Any]:
        """获取Thread统计信息
        
        Returns:
            统计信息字典
        """
        all_threads = await self.thread_manager.list_threads()
        
        total_count = len(all_threads)
        
        # 按状态统计
        status_counts = await self.aggregate_threads_by_status()
        
        # 按图ID统计
        graph_counts = await self.aggregate_threads_by_graph_id()
        
        # 计算活跃度（基于最后更新时间）
        active_threads = 0
        inactive_threads = 0
        current_time = datetime.now()
        
        for thread in all_threads:
            last_active_str = thread.get("last_active") or thread.get("created_at")
            if last_active_str:
                try:
                    last_active = datetime.fromisoformat(last_active_str.replace('Z', '+00:00'))
                    # 假设30天内有活动为活跃
                    if (current_time - last_active).days <= 30:
                        active_threads += 1
                    else:
                        inactive_threads += 1
                except ValueError:
                    inactive_threads += 1
            else:
                inactive_threads += 1
        
        stats = {
            "total_threads": total_count,
            "active_threads": active_threads,
            "inactive_threads": inactive_threads,
            "status_distribution": status_counts,
            "graph_distribution": graph_counts,
            "calculated_at": datetime.now().isoformat()
        }
        
        return stats
    
    async def search_threads_advanced(
        self,
        text: Optional[str] = None,
        status: Optional[str] = None,
        graph_ids: Optional[List[str]] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",  # "asc" or "desc"
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """高级搜索Threads
        
        Args:
            text: 搜索文本
            status: 状态过滤
            graph_ids: 图ID列表过滤
            metadata_filters: 元数据过滤
            created_after: 创建时间范围（之后）
            created_before: 创建时间范围（之前）
            sort_by: 排序字段
            sort_order: 排序顺序
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            搜索结果和元数据
        """
        # 构建过滤器
        filters = {}
        if text:
            filters["contains_text"] = text
        if status:
            filters["status"] = status
        if metadata_filters:
            filters["metadata"] = metadata_filters
        
        # 获取所有匹配的threads
        all_matching = await self.search_threads(filters)
        
        # 应用graph_id过滤
        if graph_ids:
            all_matching = [
                thread for thread in all_matching
                if thread.get("graph_id") in graph_ids
            ]
        
        # 应用时间范围过滤
        if created_after or created_before:
            filtered_by_time = []
            for thread in all_matching:
                created_at_str = thread.get("created_at")
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        if created_after and created_at < created_after:
                            continue
                        if created_before and created_at > created_before:
                            continue
                    except ValueError:
                        continue
                filtered_by_time.append(thread)
            all_matching = filtered_by_time
        
        # 排序
        if sort_by:
            reverse = sort_order.lower() == "desc"
            all_matching.sort(
                key=lambda x: x.get(sort_by, ""), 
                reverse=reverse
            )
        
        # 应用分页
        total_count = len(all_matching)
        if offset:
            all_matching = all_matching[offset:]
        if limit:
            all_matching = all_matching[:limit]
        
        result = {
            "threads": all_matching,
            "total_count": total_count,
            "returned_count": len(all_matching),
            "filters_applied": {
                "text": text,
                "status": status,
                "graph_ids": graph_ids,
                "metadata_filters": metadata_filters,
                "created_after": created_after.isoformat() if created_after else None,
                "created_before": created_before.isoformat() if created_before else None,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
        logger.info(f"高级搜索完成，共{result['returned_count']}个结果，总计{result['total_count']}个匹配")
        return result