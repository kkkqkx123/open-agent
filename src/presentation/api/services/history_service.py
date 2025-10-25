"""历史服务"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import io
import csv

from ..data_access.history_dao import HistoryDAO
from ..cache.memory_cache import MemoryCache
from ..models.requests import HistorySearchRequest, BookmarkCreateRequest
from ..models.responses import HistoryResponse, SearchResponse, BookmarkResponse
from ..utils.validation import (
    validate_session_id, validate_search_query, validate_record_types,
    validate_time_range, validate_export_format, sanitize_string
)


class HistoryService:
    """历史服务"""
    
    def __init__(
        self,
        history_dao: HistoryDAO,
        cache: MemoryCache
    ):
        self.history_dao = history_dao
        self.cache = cache
        self._bookmarks: Dict[str, List[Dict[str, Any]]] = {}  # 简化的书签存储
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        message_types: Optional[List[str]] = None
    ) -> HistoryResponse:
        """获取会话消息历史"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 验证时间范围
        start_str = start_time.isoformat() if start_time else None
        end_str = end_time.isoformat() if end_time else None
        is_valid, error_msg = validate_time_range(start_str, end_str)
        if not is_valid:
            raise ValueError(error_msg)
        
        # 验证记录类型
        if message_types:
            is_valid, error_msg = validate_record_types(message_types)
            if not is_valid:
                raise ValueError(error_msg)
        
        # 检查缓存
        cache_key = f"history:messages:{session_id}:{limit}:{offset}:{start_str}:{end_str}:{message_types}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return HistoryResponse(**cached_result)
        
        # 获取历史记录
        records = self.history_dao.get_session_records(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            record_types=message_types,
            limit=limit,
            offset=offset
        )
        
        # 获取总记录数（用于分页）
        all_records = self.history_dao.get_session_records(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            record_types=message_types,
            limit=10000  # 获取足够多的记录来计算总数
        )
        total = len(all_records)
        
        result = HistoryResponse(
            session_id=session_id,
            records=records,
            total=total,
            limit=limit,
            offset=offset
        )
        
        # 缓存结果
        await self.cache.set(cache_key, result.model_dump(), ttl=60)
        
        return result
    
    async def search_session_messages(
        self,
        session_id: str,
        query: str,
        limit: int = 20
    ) -> SearchResponse:
        """搜索会话消息"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 验证搜索查询
        is_valid, error_msg = validate_search_query(query)
        if not is_valid:
            raise ValueError(error_msg)
        
        query = sanitize_string(query, 500)
        
        # 检查缓存
        cache_key = f"history:search:{session_id}:{query}:{limit}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return SearchResponse(**cached_result)
        
        # 搜索记录
        results = self.history_dao.search_session_records(
            session_id=session_id,
            query=query,
            limit=limit
        )
        
        result = SearchResponse(
            session_id=session_id,
            query=query,
            results=results,
            total=len(results)
        )
        
        # 缓存结果
        await self.cache.set(cache_key, result.model_dump(), ttl=300)
        
        return result
    
    async def export_session_data(
        self,
        session_id: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """导出会话数据"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        if not validate_export_format(format):
            raise ValueError("不支持的导出格式")
        
        # 检查缓存
        cache_key = f"history:export:{session_id}:{format}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result  # type: ignore
        
        # 导出数据
        try:
            export_data = self.history_dao.export_session_data(session_id, format)
            
            # 缓存结果（较短的TTL，因为导出数据可能很大）
            await self.cache.set(cache_key, export_data, ttl=60)
            
            return export_data
        except Exception as e:
            raise ValueError(f"导出失败: {str(e)}")
    
    async def bookmark_message(
        self,
        session_id: str,
        message_id: str,
        note: Optional[str] = None
    ) -> BookmarkResponse:
        """添加消息书签"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        if not message_id:
            raise ValueError("消息ID不能为空")
        
        # 创建书签
        bookmark_id = f"bookmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{message_id}"
        
        bookmark = {
            "bookmark_id": bookmark_id,
            "session_id": session_id,
            "message_id": message_id,
            "note": sanitize_string(note, 500) if note else None,
            "created_at": datetime.now()
        }
        
        # 存储书签
        if session_id not in self._bookmarks:
            self._bookmarks[session_id] = []
        self._bookmarks[session_id].append(bookmark)
        
        # 清除相关缓存
        await self.cache.delete(f"history:bookmarks:{session_id}")
        
        return BookmarkResponse(
            bookmark_id=str(bookmark["bookmark_id"]),
            session_id=str(bookmark["session_id"]),
            message_id=str(bookmark["message_id"]),
            note=bookmark["note"] if bookmark["note"] is None else str(bookmark["note"]),
            created_at=bookmark["created_at"]  # type: ignore
        )
    
    async def get_bookmarks(
        self,
        session_id: Optional[str] = None
    ) -> List[BookmarkResponse]:
        """获取书签列表"""
        # 检查缓存
        cache_key = f"history:bookmarks:{session_id or 'all'}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return [BookmarkResponse(**bookmark) for bookmark in cached_result]
        
        bookmarks = []
        
        if session_id:
            # 获取特定会话的书签
            if session_id in self._bookmarks:
                bookmarks = self._bookmarks[session_id]
        else:
            # 获取所有书签
            for session_bookmarks in self._bookmarks.values():
                bookmarks.extend(session_bookmarks)
        
        # 按创建时间倒序排列
        bookmarks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 缓存结果
        await self.cache.set(cache_key, bookmarks, ttl=300)
        
        return [BookmarkResponse(**bookmark) for bookmark in bookmarks]
    
    async def delete_bookmark(self, bookmark_id: str) -> bool:
        """删除书签"""
        if not bookmark_id:
            raise ValueError("书签ID不能为空")
        
        # 查找并删除书签
        for session_id, bookmarks in self._bookmarks.items():
            for i, bookmark in enumerate(bookmarks):
                if bookmark.get("bookmark_id") == bookmark_id:
                    bookmarks.pop(i)
                    
                    # 清除相关缓存
                    await self.cache.delete(f"history:bookmarks:{session_id}")
                    await self.cache.delete("history:bookmarks:all")
                    
                    return True
        
        return False
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计信息"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 检查缓存
        cache_key = f"history:stats:{session_id}"
        cached_stats = await self.cache.get(cache_key)
        if cached_stats:
            return cached_stats  # type: ignore
        
        # 获取统计信息
        stats = self.history_dao.get_session_statistics(session_id)
        
        # 缓存结果
        await self.cache.set(cache_key, stats, ttl=300)
        
        return stats
    
    async def get_recent_activity(
        self,
        limit: int = 50,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取最近活动"""
        # 这里简化实现，实际应该从多个会话中获取最新记录
        if session_id:
            if not validate_session_id(session_id):
                raise ValueError("无效的会话ID格式")
            
            records = self.history_dao.get_session_records(
                session_id=session_id,
                limit=limit
            )
        else:
            # 获取所有会话的最新记录
            # 这里简化实现，实际应该更高效
            records = []
            # 可以通过遍历所有会话文件来实现
        
        # 按时间倒序排列
        records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return records[:limit]
    
    async def cleanup_old_records(
        self,
        days_to_keep: int = 30
    ) -> Dict[str, Any]:
        """清理旧记录"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # 这里应该实现清理逻辑
        # 遍历所有历史文件，删除超过指定天数的记录
        
        cleaned_files = 0
        cleaned_records = 0
        
        # 简化实现
        return {
            "cleaned_files": cleaned_files,
            "cleaned_records": cleaned_records,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    async def aggregate_session_data(
        self,
        session_id: str,
        aggregation_type: str = "daily"
    ) -> Dict[str, Any]:
        """聚合会话数据"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 获取所有记录
        records = self.history_dao.get_session_records(
            session_id=session_id,
            limit=10000
        )
        
        # 按日期聚合
        daily_data = {}
        for record in records:
            timestamp = record.get("timestamp", "")
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date().isoformat()
                    if date not in daily_data:
                        daily_data[date] = {
                            "message_count": 0,
                            "tool_call_count": 0,
                            "error_count": 0,
                            "token_usage": 0
                        }
                    
                    record_type = record.get("record_type", "")
                    if record_type == "message":
                        daily_data[date]["message_count"] += 1
                    elif record_type == "tool_call":
                        daily_data[date]["tool_call_count"] += 1
                    elif record_type == "error":
                        daily_data[date]["error_count"] += 1
                    elif record_type == "token_usage":
                        daily_data[date]["token_usage"] += record.get("total_tokens", 0)
                        
                except ValueError:
                    continue
        
        return {
            "session_id": session_id,
            "aggregation_type": aggregation_type,
            "data": daily_data,
            "total_days": len(daily_data)
        }