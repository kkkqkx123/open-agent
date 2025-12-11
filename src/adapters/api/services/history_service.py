"""历史服务"""
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import json
from src.interfaces.dependency_injection import get_logger

from ..data_access.history_dao import HistoryDAO
from ..cache.memory_cache import MemoryCache
from ..cache.cache_manager import CacheManager
from ..models.requests import HistorySearchRequest, BookmarkCreateRequest
from ..models.responses import HistoryResponse, SearchResponse, BookmarkResponse
from ..utils.validation import (
    validate_session_id, validate_search_query, validate_record_types,
    validate_time_range, validate_export_format, sanitize_string
)

# 导入HistoryManager相关类型
HISTORY_MANAGER_AVAILABLE = False
CoreRecordType: Any = None
CoreHistoryQuery: Any = None

try:
    from ....services.history.manager import HistoryManager
    from ....interfaces.history import IHistoryManager
    from ....core.history.entities import (
        MessageRecord, ToolCallRecord, HistoryQuery as CoreHistoryQuery,
        HistoryResult, RecordType as CoreRecordType
    )
    HISTORY_MANAGER_AVAILABLE = True
            
except ImportError:
    logger = get_logger(__name__)
    logger.warning("HistoryManager不可用，使用基础历史服务")

# 创建兼容性的RecordType
class RecordType:
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOKEN_USAGE = "token_usage"
    COST = "cost"

# 创建兼容性的HistoryQuery
class HistoryQuery:
    def __init__(self, session_id=None, record_type=None, start_time=None, end_time=None, limit=100, offset=0):  # type: ignore
        self.session_id = session_id
        self.record_type = record_type
        self.start_time = start_time
        self.end_time = end_time
        self.limit = limit
        self.offset = offset

# 兼容性类定义 - 在新架构中缺失的类
class MessageType:
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class SearchQuery:
    def __init__(self, session_id: str, search_text: str, limit: int = 20):
        self.session_id = session_id
        self.search_text = search_text
        self.limit = limit

class SearchResult:
    def __init__(self, results: List[Dict[str, Any]], total: int):
        self.results = results
        self.total = total


class HistoryService:
    """历史服务 - 支持HistoryManager高级功能"""
    
    def __init__(
        self,
        history_dao: HistoryDAO,
        cache: Union[MemoryCache, CacheManager],
        history_manager: Optional['IHistoryManager'] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        self.history_dao = history_dao
        self.cache = cache
        self.history_manager = history_manager
        self.cache_manager = cache_manager
        self._bookmarks: Dict[str, List[Dict[str, Any]]] = {}  # 简化的书签存储
        self.logger = get_logger(__name__)
        self.cache_key_prefix = "history"  # 缓存键前缀
        
        # 检查HistoryManager可用性
        self.use_advanced_features = HISTORY_MANAGER_AVAILABLE and history_manager is not None
        if self.use_advanced_features:
            self.logger.info("HistoryService已启用高级功能（HistoryManager集成）")
        else:
            self.logger.info("HistoryService使用基础功能（仅DAO和缓存）")
        
        # 如果提供了缓存管理器，优先使用它
        if cache_manager:
            self.logger.info("HistoryService使用缓存管理器")
            self.cache = cache_manager
    
    async def get_all_sessions(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取所有会话列表 - 支持HistoryManager高级查询"""
        
        # 优先使用HistoryManager的高级功能
        if self.use_advanced_features and self.history_manager:
            try:
                self.logger.debug(f"使用HistoryManager获取所有会话列表: limit={limit}, offset={offset}")
                
                # 构建查询参数 - 获取所有会话的基础信息
                query = HistoryQuery(
                    record_type=RecordType.MESSAGE,  # 只查询消息来确定会话
                    limit=1000  # 获取足够多的记录来分析会话
                )
                
                # 执行查询
                # 如果使用HistoryManager，需要转换查询对象
                if CoreHistoryQuery and HISTORY_MANAGER_AVAILABLE:
                    core_query = CoreHistoryQuery(
                        session_id=query.session_id,
                        record_type=CoreRecordType.MESSAGE if (CoreRecordType and query.record_type == RecordType.MESSAGE) else None,
                        start_time=query.start_time,
                        end_time=query.end_time,
                        limit=query.limit,
                        offset=query.offset
                    )
                    result = await self.history_manager.query_history(core_query)
                else:
                    result = await self.history_manager.query_history(query)  # type: ignore
                
                # 分析会话信息
                sessions_dict = {}
                for record in result.records:
                    session_id = getattr(record, 'session_id', None)
                    if not session_id:
                        continue
                    
                    if session_id not in sessions_dict:
                        sessions_dict[session_id] = {
                            "session_id": session_id,
                            "message_count": 0,
                            "last_activity": None,
                            "created_at": None
                        }
                    
                    # 更新消息计数
                    sessions_dict[session_id]["message_count"] += 1
                    
                    # 更新时间戳
                    timestamp = getattr(record, 'timestamp', None)
                    if timestamp:
                        if not sessions_dict[session_id]["last_activity"] or timestamp > sessions_dict[session_id]["last_activity"]:
                            sessions_dict[session_id]["last_activity"] = timestamp
                        if not sessions_dict[session_id]["created_at"] or timestamp < sessions_dict[session_id]["created_at"]:
                            sessions_dict[session_id]["created_at"] = timestamp
                
                # 转换格式并排序
                sessions = list(sessions_dict.values())
                sessions.sort(key=lambda x: x["last_activity"] or datetime.min, reverse=True)
                
                # 应用分页
                total_sessions = len(sessions)
                start_idx = offset
                end_idx = min(offset + limit, total_sessions)
                
                return sessions[start_idx:end_idx]  # type: ignore
                
            except Exception as e:
                self.logger.warning(f"HistoryManager获取会话列表失败，回退到缓存: {e}")
        
        # 回退到基础缓存查询
        self.logger.debug(f"使用基础缓存获取所有会话列表: limit={limit}, offset={offset}")
        
        # 从缓存获取会话列表
        cache_key = f"{self.cache_key_prefix}:sessions:list"
        cached_sessions = await self.cache.get(cache_key)
        if cached_sessions:
            total_sessions = len(cached_sessions)
            start_idx = offset
            end_idx = min(offset + limit, total_sessions)
            return cached_sessions[start_idx:end_idx]
        
        # 如果缓存中没有，返回空列表
        return []
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        message_types: Optional[List[str]] = None
    ) -> HistoryResponse:
        """获取会话消息历史 - 支持HistoryManager高级查询"""
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
        
        # 优先使用HistoryManager的高级功能
        if self.use_advanced_features and self.history_manager:
            try:
                self.logger.debug(f"使用HistoryManager查询会话历史: {session_id}")
                
                # 构建查询参数
                query = HistoryQuery(
                    session_id=session_id,
                    start_time=start_time,
                    end_time=end_time,
                    record_type=RecordType.MESSAGE,  # 简化处理
                    limit=limit,
                    offset=offset
                )
                
                # 执行查询
                # 如果使用HistoryManager，需要转换查询对象
                if CoreHistoryQuery and HISTORY_MANAGER_AVAILABLE:
                    core_query = CoreHistoryQuery(
                        session_id=query.session_id,
                        record_type=CoreRecordType.MESSAGE if (CoreRecordType and query.record_type == RecordType.MESSAGE) else None,
                        start_time=query.start_time,
                        end_time=query.end_time,
                        limit=query.limit,
                        offset=query.offset
                    )
                    result = await self.history_manager.query_history(core_query)
                else:
                    result = await self.history_manager.query_history(query)  # type: ignore
                
                # 转换结果格式
                records = []
                for record in result.records:
                    if hasattr(record, 'to_dict'):
                        records.append(record.to_dict())
                    else:
                        # 兼容旧格式
                        record_dict = record.__dict__ if hasattr(record, '__dict__') else {}
                        records.append(record_dict)
                
                return HistoryResponse(
                    session_id=session_id,
                    records=records,
                    total=result.total_count,
                    limit=limit,
                    offset=offset
                )
                
            except Exception as e:
                self.logger.warning(f"HistoryManager查询失败，回退到DAO: {e}")
        
        # 回退到基础DAO查询
        self.logger.debug(f"使用基础DAO查询会话历史: {session_id}")
        
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
        """搜索会话消息 - 支持HistoryManager高级搜索"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 验证搜索查询
        is_valid, error_msg = validate_search_query(query)
        if not is_valid:
            raise ValueError(error_msg)
        
        query = sanitize_string(query, 500)
        
        # 优先使用HistoryManager的高级搜索功能
        if self.use_advanced_features and self.history_manager:
            try:
                self.logger.debug(f"使用HistoryManager搜索会话消息: {session_id}, 查询: {query}")
                
                # 新架构中HistoryManager不支持搜索功能，直接回退到DAO搜索
                self.logger.debug("HistoryManager不支持搜索功能，回退到DAO搜索")
                    
            except Exception as e:
                self.logger.warning(f"HistoryManager搜索失败，回退到DAO: {e}")
        
        # 回退到基础DAO搜索
        self.logger.debug(f"使用基础DAO搜索会话消息: {session_id}, 查询: {query}")
        
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
    ) -> str:
        """导出会话数据 - 支持HistoryManager高级导出"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        if not validate_export_format(format):
            raise ValueError("不支持的导出格式")
        
        # 优先使用HistoryManager的高级导出功能
        if self.use_advanced_features and self.history_manager:
            try:
                self.logger.debug(f"使用HistoryManager导出会话数据: session_id={session_id}, format={format}")
                
                # 构建查询获取所有相关数据
                query = HistoryQuery(
                    session_id=session_id,
                    limit=10000  # 获取足够多的记录
                )
                
                # 执行查询获取所有记录
                # 如果使用HistoryManager，需要转换查询对象
                if CoreHistoryQuery and HISTORY_MANAGER_AVAILABLE:
                    core_query = CoreHistoryQuery(
                        session_id=query.session_id,
                        record_type=query.record_type,
                        start_time=query.start_time,
                        end_time=query.end_time,
                        limit=query.limit,
                        offset=query.offset
                    )
                    result = await self.history_manager.query_history(core_query)
                else:
                    result = await self.history_manager.query_history(query)  # type: ignore
                
                # 分离不同类型的记录
                messages: List[Dict[str, Any]] = []
                bookmarks: List[Dict[str, Any]] = []
                tool_calls: List[Dict[str, Any]] = []
                errors: List[Dict[str, Any]] = []
                
                for record in result.records:
                    record_dict = record.to_dict() if hasattr(record, 'to_dict') else record.__dict__ if hasattr(record, '__dict__') else {}
                    
                    if record.record_type == "message":
                        messages.append(record_dict)
                    elif record.record_type == "bookmark":
                        bookmarks.append(record_dict)
                    elif record.record_type == "tool_call":
                        tool_calls.append(record_dict)
                    elif record.record_type == "error":
                        errors.append(record_dict)
                
                # 计算统计信息
                stats = {
                    "total_messages": len(messages),
                    "total_bookmarks": len(bookmarks),
                    "total_tool_calls": len(tool_calls),
                    "total_errors": len(errors),
                    "session_duration": self._calculate_session_duration(messages)
                }
                
                # 构建导出数据
                export_data = {
                    "session_id": session_id,
                    "export_timestamp": datetime.now().isoformat(),
                    "messages": messages,
                    "bookmarks": bookmarks,
                    "tool_calls": tool_calls,
                    "errors": errors,
                    "statistics": stats
                }
                
                # 根据格式导出
                return self._format_export_data(export_data, format)
                
            except Exception as e:
                self.logger.warning(f"HistoryManager导出会话数据失败，回退到基础方法: {e}")
        
        # 回退到基础DAO导出
        self.logger.debug(f"使用基础DAO导出会话数据: session_id={session_id}, format={format}")
        
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
            
            if format.lower() == "json":
                return str(export_data)
            else:
                if format.lower() == "json":
                    return json.dumps(export_data, ensure_ascii=False, indent=2)
                else:
                    return str(export_data)
        except Exception as e:
            raise ValueError(f"导出失败: {str(e)}")
    
    def _format_export_data(self, export_data: Dict[str, Any], format: str) -> str:
        """格式化导出数据"""
        import json
        
        if format.lower() == "json":
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        elif format.lower() == "csv":
            # 简化CSV导出
            messages = export_data.get("messages", [])
            csv_data = "timestamp,role,content\n"
            for msg in messages:
                csv_data += f"{msg.get('timestamp', '')},{msg.get('role', '')},{msg.get('content', '')}\n"
            return csv_data
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _calculate_session_duration(self, messages: List[Dict[str, Any]]) -> str:
        """计算会话持续时间"""
        if not messages:
            return "00:00:00"
        
        try:
            timestamps = [msg.get("timestamp") for msg in messages if msg.get("timestamp")]
            if not timestamps:
                return "00:00:00"
            
            # 解析时间戳 - 过滤掉None值
            valid_timestamps = [ts for ts in timestamps if ts is not None]
            if not valid_timestamps:
                return "00:00:00"
            
            start_time = datetime.fromisoformat(min(valid_timestamps))
            end_time = datetime.fromisoformat(max(valid_timestamps))
            
            duration = end_time - start_time
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            seconds = duration.seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
        except (ValueError, TypeError):
            return "00:00:00"
    
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
        """获取会话统计信息 - 支持HistoryManager高级统计"""
        if not validate_session_id(session_id):
            raise ValueError("无效的会话ID格式")
        
        # 优先使用HistoryManager的高级统计功能
        if self.use_advanced_features and self.history_manager:
            try:
                self.logger.debug(f"使用HistoryManager获取会话统计: {session_id}")
                
                # 获取详细历史记录用于统计
                query = HistoryQuery(
                    session_id=session_id,
                    limit=10000  # 获取足够多的记录
                )
                
                # 如果使用HistoryManager，需要转换查询对象
                if CoreHistoryQuery and HISTORY_MANAGER_AVAILABLE:
                    core_query = CoreHistoryQuery(
                        session_id=query.session_id,
                        record_type=query.record_type,
                        start_time=query.start_time,
                        end_time=query.end_time,
                        limit=query.limit,
                        offset=query.offset
                    )
                    result = await self.history_manager.query_history(core_query)
                else:
                    result = await self.history_manager.query_history(query)  # type: ignore
                
                # 计算统计信息
                stats = {
                    "total_messages": 0,
                    "total_tool_calls": 0,
                    "total_errors": 0,
                    "total_tokens": 0,
                    "message_types": {},
                    "tool_usage": {},
                    "time_range": {
                        "start": None,
                        "end": None
                    }
                }
                
                timestamps = []
                for record in result.records:
                    record_type = getattr(record, 'record_type', '')
                    
                    if record_type == 'message':
                        stats["total_messages"] += 1  # type: ignore
                        message_type = getattr(record, 'message_type', 'unknown')
                        message_type_str = str(message_type)
                        stats["message_types"][message_type_str] = stats["message_types"].get(message_type_str, 0) + 1  # type: ignore
                    
                    elif record_type == 'tool_call':
                        stats["total_tool_calls"] += 1  # type: ignore
                        tool_name = getattr(record, 'tool_name', 'unknown')
                        stats["tool_usage"][tool_name] = stats["tool_usage"].get(tool_name, 0) + 1  # type: ignore
                    
                    elif record_type == 'error':
                        stats["total_errors"] += 1  # type: ignore
                    
                    elif record_type == 'token_usage':
                        stats["total_tokens"] += getattr(record, 'total_tokens', 0)  # type: ignore
                    
                    # 收集时间戳
                    timestamp = getattr(record, 'timestamp', None)
                    if timestamp:
                        timestamps.append(timestamp)
                
                # 计算时间范围
                if timestamps:
                    stats["time_range"]["start"] = min(timestamps).isoformat()  # type: ignore
                    stats["time_range"]["end"] = max(timestamps).isoformat()  # type: ignore
                
                # 添加缓存
                cache_key = f"history:stats:{session_id}"
                await self.cache.set(cache_key, stats, ttl=300)
                
                return stats
                
            except Exception as e:
                self.logger.warning(f"HistoryManager统计失败，回退到DAO: {e}")
        
        # 回退到基础DAO统计
        self.logger.debug(f"使用基础DAO获取会话统计: {session_id}")
        
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
        """获取最近活动 - 支持HistoryManager高级查询"""
        
        # 优先使用HistoryManager的高级查询功能
        if self.use_advanced_features and self.history_manager:
            try:
                self.logger.debug(f"使用HistoryManager获取最近活动: limit={limit}, session_id={session_id}")
                
                # 构建查询参数
                query = HistoryQuery(
                    session_id=session_id,
                    limit=limit
                )
                
                # 执行查询
                # 如果使用HistoryManager，需要转换查询对象
                if CoreHistoryQuery and HISTORY_MANAGER_AVAILABLE:
                    core_query = CoreHistoryQuery(
                        session_id=query.session_id,
                        record_type=query.record_type,
                        start_time=query.start_time,
                        end_time=query.end_time,
                        limit=query.limit,
                        offset=query.offset
                    )
                    result = await self.history_manager.query_history(core_query)
                else:
                    result = await self.history_manager.query_history(query)  # type: ignore
                
                # 转换结果格式
                records = []
                for record in result.records:
                    if hasattr(record, 'to_dict'):
                        records.append(record.to_dict())
                    else:
                        record_dict = record.__dict__ if hasattr(record, '__dict__') else {}
                        records.append(record_dict)
                
                return records
                
            except Exception as e:
                self.logger.warning(f"HistoryManager查询最近活动失败，回退到DAO: {e}")
        
        # 回退到基础DAO查询
        self.logger.debug(f"使用基础DAO获取最近活动: limit={limit}, session_id={session_id}")
        
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
        """清理旧记录 - 支持HistoryManager高级清理"""
        if days_to_keep <= 0:
            raise ValueError("days_to_keep必须为正数")
        
        # 优先使用HistoryManager的高级清理功能
        if self.use_advanced_features and self.history_manager:
            try:
                self.logger.debug(f"使用HistoryManager清理旧记录: days_to_keep={days_to_keep}")
                
                # 计算截止时间
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                # 使用HistoryManager的清理功能
                result = await self.history_manager.cleanup_old_records(older_than=cutoff_date)
                cleaned_count = result.get("deleted_count", 0)
                
                # 同时清理相关缓存
                cache_keys = await self.cache.get_all_keys()
                cache_cleaned = 0
                
                for cache_key in cache_keys:
                    if cache_key.startswith("history:"):
                        data = await self.cache.get(cache_key)
                        if data:
                            timestamp = data.get("timestamp")
                            if timestamp:
                                try:
                                    record_date = datetime.fromisoformat(timestamp)
                                    if record_date < cutoff_date:
                                        await self.cache.delete(cache_key)
                                        cache_cleaned += 1
                                except (ValueError, TypeError):
                                    await self.cache.delete(cache_key)
                                    cache_cleaned += 1
                
                return {
                    "cleaned_files": cleaned_count,
                    "cleaned_records": cleaned_count + cache_cleaned,
                    "cutoff_date": cutoff_date.isoformat()
                }
                
            except Exception as e:
                self.logger.warning(f"HistoryManager清理旧记录失败，回退到DAO: {e}")
        
        # 回退到基础DAO清理
        self.logger.debug(f"使用基础DAO清理旧记录: days_to_keep={days_to_keep}")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # 清理缓存
        cache_keys = await self.cache.get_all_keys()
        cleaned_count = 0
        
        for cache_key in cache_keys:
            if cache_key.startswith("history:"):
                # 获取缓存数据
                data = await self.cache.get(cache_key)
                if data:
                    # 检查是否过期
                    timestamp = data.get("timestamp")
                    if timestamp:
                        try:
                            record_date = datetime.fromisoformat(timestamp)
                            if record_date < cutoff_date:
                                await self.cache.delete(cache_key)
                                cleaned_count += 1
                        except (ValueError, TypeError):
                            # 无效的日期格式，删除该记录
                            await self.cache.delete(cache_key)
                            cleaned_count += 1
        
        # 清理数据库中的旧记录
        db_cleaned = self.history_dao.cleanup_old_records(cutoff_date)
        cleaned_count += db_cleaned
        
        return {
            "cleaned_files": db_cleaned,
            "cleaned_records": cleaned_count,
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