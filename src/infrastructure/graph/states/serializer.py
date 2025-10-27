"""状态序列化器

提供高效的状态序列化和反序列化功能。
"""

import json
import pickle
import hashlib
import time
import threading
from typing import Dict, Any, List, Optional, Union, Type, Set
from datetime import datetime
from dataclasses import dataclass
from collections import OrderedDict

from .base import BaseGraphState, BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from .workflow import WorkflowState
from .react import ReActState
from .plan_execute import PlanExecuteState


@dataclass
class CacheEntry:
    """缓存条目"""
    serialized_data: Union[str, bytes]
    state_hash: str
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > ttl_seconds


@dataclass
class StateDiff:
    """状态差异"""
    added: Dict[str, Any]
    modified: Dict[str, Any]
    removed: Set[str]
    timestamp: float


class StateSerializer:
    """增强的状态序列化器
    
    提供高效的状态序列化和反序列化功能，支持多种格式。
    新增功能：
    - 状态序列化缓存
    - 差异序列化
    - 内存优化
    - 性能监控
    """
    
    # 支持的序列化格式
    FORMAT_JSON = "json"
    FORMAT_PICKLE = "pickle"
    FORMAT_COMPACT_JSON = "compact_json"
    
    def __init__(
        self,
        max_cache_size: int = 1000,
        cache_ttl_seconds: int = 3600,
        enable_compression: bool = True,
        enable_diff_serialization: bool = True
    ):
        """初始化增强序列化器
        
        Args:
            max_cache_size: 最大缓存大小
            cache_ttl_seconds: 缓存过期时间（秒）
            enable_compression: 是否启用压缩
            enable_diff_serialization: 是否启用差异序列化
        """
        self._max_cache_size = max_cache_size
        self._cache_ttl_seconds = cache_ttl_seconds
        self._enable_compression = enable_compression
        self._enable_diff_serialization = enable_diff_serialization
        
        # 缓存相关
        self._serialization_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._cache_lock = threading.RLock()
        
        # 差异缓存
        self._diff_cache: Dict[str, StateDiff] = {}
        self._diff_lock = threading.RLock()
        
        # 消息序列化缓存
        self._message_cache: Dict[int, Dict[str, Any]] = {}
        self._message_lock = threading.RLock()
        
        # 性能统计
        self._stats = {
            "total_serializations": 0,
            "total_deserializations": 0,
            "total_diff_computations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "bytes_saved": 0
        }
    
    @staticmethod
    def serialize_message(message: BaseMessage) -> Dict[str, Any]:
        """序列化消息
        
        Args:
            message: 消息对象
            
        Returns:
            序列化后的消息字典
        """
        message_data = {
            "content": message.content,
            "type": message.type
        }
        
        # 添加特定类型的字段
        if isinstance(message, ToolMessage):
            tool_call_id = getattr(message, 'tool_call_id', '')
            if tool_call_id:
                message_data["tool_call_id"] = tool_call_id
        
        return message_data
    
    @staticmethod
    def deserialize_message(message_data: Dict[str, Any]) -> BaseMessage:
        """反序列化消息
        
        Args:
            message_data: 消息数据字典
            
        Returns:
            消息对象
        """
        content = message_data["content"]
        message_type = message_data["type"]
        
        if message_type == "human":
            return HumanMessage(content=content)
        elif message_type == "ai":
            return AIMessage(content=content)
        elif message_type == "system":
            return SystemMessage(content=content)
        elif message_type == "tool":
            tool_call_id = message_data.get("tool_call_id", "")
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        else:
            return BaseMessage(content=content, type=message_type)
    
    def serialize(
        self,
        state: Dict[str, Any],
        format: str = FORMAT_COMPACT_JSON,
        enable_cache: bool = True,
        include_metadata: bool = True
    ) -> Union[str, bytes]:
        """序列化状态（带缓存和优化）
        
        Args:
            state: 状态字典
            format: 序列化格式 ("json", "compact_json" 或 "pickle")
            enable_cache: 是否启用缓存
            include_metadata: 是否包含元数据
            
        Returns:
            序列化后的数据
            
        Raises:
            ValueError: 当格式不支持时
        """
        start_time = time.time()
        
        # 计算状态哈希（基于原始状态，不包含时间戳）
        state_hash = self._calculate_state_hash(state)
        
        # 检查缓存
        if enable_cache and self._enable_cache:
            cached_result = self._get_from_cache(state_hash)
            if cached_result:
                self._stats["cache_hits"] += 1
                # 如果启用元数据，我们需要重新添加元数据
                if include_metadata:
                    # 从缓存中获取的数据已经包含了元数据
                    return cached_result
                else:
                    # 如果不包含元数据，需要序列化原始状态但不包含元数据
                    serialized_data = self._prepare_state_for_serialization(
                        state, include_metadata=False
                    )
                    if format == self.FORMAT_JSON:
                        return json.dumps(serialized_data, ensure_ascii=False, indent=2, default=str)
                    elif format == self.FORMAT_COMPACT_JSON:
                        return json.dumps(serialized_data, ensure_ascii=False, separators=(',', ':'))
                    elif format == self.FORMAT_PICKLE:
                        return pickle.dumps(serialized_data)
        
        self._stats["cache_misses"] += 1
        
        # 准备序列化数据（会处理所有嵌套的消息对象）
        serialized_data = self._prepare_state_for_serialization(
            state, include_metadata
        )
        
        # 执行序列化
        result: Union[str, bytes]
        if format == self.FORMAT_JSON:
            result = json.dumps(serialized_data, ensure_ascii=False, indent=2, default=str)
        elif format == self.FORMAT_COMPACT_JSON:
            result = json.dumps(serialized_data, ensure_ascii=False, separators=(',', ':'))
        elif format == self.FORMAT_PICKLE:
            result = pickle.dumps(serialized_data)
        else:
            raise ValueError(f"不支持的序列化格式: {format}")
        
        # 添加到缓存
        if enable_cache and self._enable_cache:
            self._add_to_cache(state_hash, result)
        
        # 更新统计
        self._stats["total_serializations"] += 1
        execution_time = time.time() - start_time
        
        return result
    
    def deserialize(
        self,
        serialized_data: Union[str, bytes],
        format: str = FORMAT_COMPACT_JSON,
        state_type: Optional[Type] = None
    ) -> Dict[str, Any]:
        """反序列化状态（带优化）
        
        Args:
            serialized_data: 序列化的数据
            format: 序列化格式 ("json", "compact_json" 或 "pickle")
            state_type: 状态类型（用于验证）
            
        Returns:
            反序列化后的状态字典
            
        Raises:
            ValueError: 当格式不支持时
        """
        start_time = time.time()
        
        # 反序列化基础数据
        if format == self.FORMAT_JSON or format == self.FORMAT_COMPACT_JSON:
            data = json.loads(serialized_data)
        elif format == self.FORMAT_PICKLE:
            if isinstance(serialized_data, str):
                serialized_data = serialized_data.encode('latin1')
            data = pickle.loads(serialized_data)
        else:
            raise ValueError(f"不支持的序列化格式: {format}")
        
        # 恢复状态对象
        restored_state = self._restore_state_from_serialization(data)
        
        # 验证状态类型
        if state_type:
            from .factory import StateFactory
            errors = StateFactory.validate_state(restored_state, state_type)
            if errors:
                raise ValueError(f"状态验证失败: {errors}")
        
        # 更新统计
        self._stats["total_deserializations"] += 1
        execution_time = time.time() - start_time
        
        return restored_state
    
    def serialize_diff(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        format: str = FORMAT_COMPACT_JSON
    ) -> Union[str, bytes]:
        """序列化状态差异（高性能）
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            format: 序列化格式
            
        Returns:
            序列化后的差异数据
        """
        if not self._enable_diff_serialization:
            # 如果禁用差异序列化，回退到完整序列化
            return self.serialize(new_state, format)
        
        start_time = time.time()
        
        # 计算差异
        diff = self._compute_state_diff(old_state, new_state)
        
        # 序列化差异（先处理消息对象）
        added_serialized = self._prepare_state_for_serialization(diff.added, include_metadata=False)
        modified_serialized = self._prepare_state_for_serialization(diff.modified, include_metadata=False)
        
        # 序列化差异
        diff_dict = {
            "added": added_serialized,
            "modified": modified_serialized,
            "removed": list(diff.removed),  # 转换set为list
            "timestamp": diff.timestamp
        }
        
        result: Union[str, bytes]
        if format == self.FORMAT_JSON:
            result = json.dumps(diff_dict, ensure_ascii=False, indent=2, default=str)
        elif format == self.FORMAT_COMPACT_JSON:
            result = json.dumps(diff_dict, ensure_ascii=False, separators=(',', ':'))
        elif format == self.FORMAT_PICKLE:
            result = pickle.dumps(diff)
        else:
            raise ValueError(f"不支持的序列化格式: {format}")
        
        # 更新统计
        self._stats["total_diff_computations"] += 1
        execution_time = time.time() - start_time
        
        return result
    
    def apply_diff(
        self,
        base_state: Dict[str, Any],
        diff_data: Union[str, bytes],
        format: str = FORMAT_COMPACT_JSON
    ) -> Dict[str, Any]:
        """应用状态差异
        
        Args:
            base_state: 基础状态
            diff_data: 差异数据
            format: 序列化格式
            
        Returns:
            应用差异后的状态
        """
        # 反序列化差异
        if format == self.FORMAT_JSON or format == self.FORMAT_COMPACT_JSON:
            diff_dict = json.loads(diff_data)
        elif format == self.FORMAT_PICKLE:
            if isinstance(diff_data, str):
                diff_data = diff_data.encode('latin1')
            diff_dict = pickle.loads(diff_data)
        else:
            raise ValueError(f"不支持的序列化格式: {format}")
        
        diff = StateDiff(
            added=diff_dict.get("added", {}),
            modified=diff_dict.get("modified", {}),
            removed=set(diff_dict.get("removed", [])),
            timestamp=diff_dict.get("timestamp", time.time())
        )
        
        return self._apply_diff_to_state(base_state, diff)
    
    def optimize_state_for_storage(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """优化状态用于存储（增强版本）
        
        Args:
            state: 原始状态
            
        Returns:
            优化后的状态
        """
        # 使用准备用于序列化的方法，这会处理消息对象
        prepared_state = self._prepare_state_for_serialization(state, include_metadata=False)
        
        optimized = prepared_state.copy()
        
        # 移除空的可累加字段
        additive_fields = ["messages", "tool_calls", "tool_results", "errors", "steps", "step_results"]
        fields_to_remove = []
        for field in additive_fields:
            if field in optimized and not optimized[field]:
                fields_to_remove.append(field)
        
        for field in fields_to_remove:
            del optimized[field]
        
        # 移除空列表
        empty_list_fields = [key for key, value in optimized.items()
                            if isinstance(value, list) and len(value) == 0]
        for field in empty_list_fields:
            del optimized[field]
        
        # 移除None值
        none_fields = [key for key, value in optimized.items() if value is None]
        for field in none_fields:
            del optimized[field]
        
        # 压缩大消息列表（此时消息已经序列化为字典）
        if "messages" in optimized and len(optimized["messages"]) > 100:
            optimized["messages"] = optimized["messages"][-50:]  # 保留最近50条
        
        # 压缩大图状态
        if "graph_states" in optimized and len(optimized["graph_states"]) > 50:
            # 对图状态进行采样
            graph_state_items = list(optimized["graph_states"].items())
            sampled_items = graph_state_items[-25:]  # 保留最近25个
            optimized["graph_states"] = {k: v for k, v in sampled_items}
        
        return optimized
        return optimized
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            性能统计信息
        """
        total_requests = self._stats["cache_hits"] + self._stats["cache_misses"]
        cache_hit_rate = (self._stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_stats": {
                "hits": self._stats["cache_hits"],
                "misses": self._stats["cache_misses"],
                "hit_rate": f"{cache_hit_rate:.2f}%",
                "cache_size": len(self._serialization_cache),
                "max_cache_size": self._max_cache_size
            },
            "serialization_stats": {
                "total_serializations": self._stats["total_serializations"],
                "total_deserializations": self._stats["total_deserializations"],
                "total_diff_computations": self._stats["total_diff_computations"]
            },
            "memory_stats": {
                "bytes_saved": self._stats["bytes_saved"],
                "message_cache_size": len(self._message_cache)
            }
        }
    
    def clear_cache(self) -> None:
        """清除缓存"""
        with self._cache_lock:
            self._serialization_cache.clear()
            self._stats["cache_hits"] = 0
            self._stats["cache_misses"] = 0
    
    def _calculate_state_hash(self, state: Dict[str, Any]) -> str:
        """计算状态哈希
        
        Args:
            state: 状态
            
        Returns:
            状态哈希
        """
        # 使用稳定的序列化格式计算哈希
        try:
            # 准备状态用于序列化（会处理消息对象）
            prepared_state = self._prepare_state_for_serialization(state, include_metadata=False)
            serialized = json.dumps(prepared_state, sort_keys=True, separators=(',', ':'), default=str)
            return hashlib.md5(serialized.encode()).hexdigest()
        except (TypeError, ValueError):
            # 如果序列化失败，使用字符串表示
            state_str = str(sorted(state.items()))
            return hashlib.md5(state_str.encode()).hexdigest()
    
    def _prepare_state_for_serialization(
        self,
        state: Dict[str, Any],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """准备状态用于序列化（优化版本）
        
        Args:
            state: 原始状态
            include_metadata: 是否包含元数据
            
        Returns:
            准备好的序列化数据
        """
        serialized = {}
        
        # 递归处理状态中的所有字段
        for key, value in state.items():
            serialized[key] = self._process_value_for_serialization(value)
        
        # 处理日期时间对象
        datetime_fields = ["start_time", "end_time"]
        for field in datetime_fields:
            if field in serialized and serialized[field] is not None:
                if isinstance(serialized[field], datetime):
                    serialized[field] = serialized[field].isoformat()
        
        # 添加序列化元数据
        if include_metadata:
            serialized["_serialization_metadata"] = {
                "serialized_at": datetime.now().isoformat(),
                "version": "2.0",
                "serializer": "EnhancedStateSerializer"
            }
        
        return serialized
    
    def _process_value_for_serialization(self, value: Any) -> Any:
        """递归处理值以用于序列化
        
        Args:
            value: 要处理的值
            
        Returns:
            处理后的值
        """
        if isinstance(value, list):
            # 处理列表
            return [self._process_value_for_serialization(item) for item in value]
        elif isinstance(value, dict):
            # 处理字典
            processed_dict = {}
            for k, v in value.items():
                processed_dict[k] = self._process_value_for_serialization(v)
            return processed_dict
        elif hasattr(value, 'content') and hasattr(value, 'type'):
            # 处理消息对象
            return self.serialize_message(value)
        else:
            # 其他值保持不变
            return value
    
    def _serialize_messages_cached(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """序列化消息列表（带缓存）
        
        Args:
            messages: 消息列表
            
        Returns:
            序列化后的消息数据
        """
        result = []
        
        for message in messages:
            # 处理字典格式的消息（兼容性）
            if isinstance(message, dict):
                message_data = message.copy()
                result.append(message_data)
                continue
            
            # 计算消息哈希
            content = getattr(message, 'content', '')
            msg_type = getattr(message, 'type', 'base')
            message_hash = hash(content + msg_type)
            
            # 检查消息缓存
            with self._message_lock:
                if message_hash in self._message_cache:
                    result.append(self._message_cache[message_hash])
                    continue
            
            # 序列化消息
            message_data = self.serialize_message(message)
            
            # 添加到缓存
            with self._message_lock:
                self._message_cache[message_hash] = message_data
            
            result.append(message_data)
        
        return result
    
    def _restore_state_from_serialization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从序列化数据恢复状态（优化版本）
        
        Args:
            data: 序列化数据
            
        Returns:
            恢复后的状态
        """
        state = data.copy()
        
        # 移除序列化元数据
        if "_serialization_metadata" in state:
            del state["_serialization_metadata"]
        
        # 恢复消息列表
        if "messages" in state:
            state["messages"] = [
                self.deserialize_message(msg_data)
                for msg_data in state["messages"]
            ]
        
        # 恢复日期时间对象
        datetime_fields = ["start_time", "end_time"]
        for field in datetime_fields:
            if field in state and state[field] is not None:
                if isinstance(state[field], str):
                    try:
                        state[field] = datetime.fromisoformat(state[field])
                    except ValueError:
                        pass
        
        # 恢复图状态字典
        if "graph_states" in state:
            graph_states = {}
            for graph_id, graph_state_data in state["graph_states"].items():
                graph_states[graph_id] = self._restore_state_from_serialization(
                    graph_state_data
                )
            state["graph_states"] = graph_states
        
        return state
    
    def _compute_state_diff(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> StateDiff:
        """计算状态差异（优化版本）
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            
        Returns:
            状态差异
        """
        added = {}
        modified = {}
        removed = set()
        
        # 检查新增和修改的字段
        for key, new_value in new_state.items():
            if key not in old_state:
                added[key] = new_value
            elif self._deep_equal(old_state[key], new_value) is False:
                # 对于大列表，只记录差异部分
                if isinstance(new_value, list) and len(new_value) > 100:
                    old_list = old_state[key]
                    if isinstance(old_list, list):
                        # 只记录新增的元素
                        added_elements = new_value[len(old_list):]
                        if added_elements:
                            modified[key] = {"added": added_elements}
                    else:
                        modified[key] = new_value  # type: ignore
                else:
                    modified[key] = new_value
        
        # 检查删除的字段
        for key in old_state:
            if key not in new_state:
                removed.add(key)
        
        return StateDiff(
            added=added,
            modified=modified,
            removed=removed,
            timestamp=time.time()
        )
    
    def _deep_equal(self, obj1: Any, obj2: Any) -> bool:
        """深度比较两个对象是否相等，特别处理消息对象
        
        Args:
            obj1: 对象1
            obj2: 对象2
            
        Returns:
            是否相等
        """
        if type(obj1) != type(obj2):
            return False
        
        if isinstance(obj1, (str, int, float, bool, type(None))):
            return obj1 == obj2
        
        if isinstance(obj1, (list, tuple)):
            if len(obj1) != len(obj2):
                return False
            return all(self._deep_equal(a, b) for a, b in zip(obj1, obj2))
        
        if isinstance(obj1, dict):
            if set(obj1.keys()) != set(obj2.keys()):
                return False
            return all(self._deep_equal(obj1[key], obj2[key]) for key in obj1.keys())
        
        # 处理消息对象
        if hasattr(obj1, '__dict__') and hasattr(obj2, '__dict__'):
            # 如果是消息对象，比较其属性
            if hasattr(obj1, 'content') and hasattr(obj2, 'content'):
                return obj1.content == obj2.content and obj1.type == obj2.type
            # 对于其他自定义对象，比较其字典表示
            return self._deep_equal(obj1.__dict__, obj2.__dict__)
        
        return obj1 == obj2
    
    def _apply_state_diff(
        self,
        base_state: Dict[str, Any],
        diff: StateDiff
    ) -> Dict[str, Any]:
        """应用状态差异
        
        Args:
            base_state: 基础状态
            diff: 状态差异
            
        Returns:
            应用差异后的状态
        """
        result = base_state.copy()
        
        # 应用新增字段
        for key, value in diff.added.items():
            result[key] = value
        
        # 应用修改字段
        for key, change in diff.modified.items():
            if isinstance(change, dict) and "added" in change:
                # 列表增量更新
                if key in result and isinstance(result[key], list):
                    result[key].extend(change["added"])
                else:
                    result[key] = change["added"]
            else:
                result[key] = change
        
        # 移除删除字段
        for key in diff.removed:
            if key in result:
                del result[key]
        
        return result
    
    def _get_from_cache(self, state_hash: str) -> Optional[Union[str, bytes]]:
        """从缓存获取
        
        Args:
            state_hash: 状态哈希
            
        Returns:
            缓存的数据，如果不存在则返回None
        """
        with self._cache_lock:
            if state_hash in self._serialization_cache:
                entry = self._serialization_cache[state_hash]
                if not entry.is_expired(self._cache_ttl_seconds):
                    # 更新访问信息
                    entry.access_count += 1
                    entry.last_accessed = time.time()
                    
                    # 移动到末尾（LRU）
                    self._serialization_cache.move_to_end(state_hash)
                    
                    return entry.serialized_data
                else:
                    # 移除过期条目
                    del self._serialization_cache[state_hash]
        
        return None
    
    def _add_to_cache(self, state_hash: str, serialized_data: Union[str, bytes]) -> None:
        """添加到缓存
        
        Args:
            state_hash: 状态哈希
            serialized_data: 序列化数据
        """
        with self._cache_lock:
            # 检查缓存大小
            if len(self._serialization_cache) >= self._max_cache_size:
                # 移除最久未使用的条目
                self._serialization_cache.popitem(last=False)
            
            # 创建缓存条目
            entry = CacheEntry(
                serialized_data=serialized_data,
                state_hash=state_hash,
                created_at=time.time(),
                access_count=1,
                last_accessed=time.time()
            )
            
            self._serialization_cache[state_hash] = entry
    
    def _compress_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """压缩消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            压缩后的消息列表
        """
        if len(messages) <= 100:
            return messages
        
        # 保留最近的消息和关键消息
        recent_messages = messages[-50:]  # 最近50条
        system_messages = [msg for msg in messages if isinstance(msg, SystemMessage)]
        
        # 合并系统消息
        if system_messages:
            combined_system_content = "\n".join(msg.content for msg in system_messages)
            combined_system = SystemMessage(content=combined_system_content)
            return [combined_system] + recent_messages
        
        return recent_messages
    
    def _compress_graph_states(self, graph_states: Dict[str, Any]) -> Dict[str, Any]:
        """压缩图状态
        
        Args:
            graph_states: 图状态字典
            
        Returns:
            压缩后的图状态
        """
        if len(graph_states) <= 50:
            return graph_states
        
        # 只保留最近更新的图状态
        # 这里可以实现更复杂的压缩逻辑
        recent_states = {}
        for graph_id, state in list(graph_states.items())[-25:]:  # 保留最近25个
            recent_states[graph_id] = state
        
        return recent_states
    
    @property
    def _enable_cache(self) -> bool:
        """是否启用缓存"""
        return self._max_cache_size > 0
    
    def compute_state_diff_static(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算状态差异（静态方法，保持向后兼容）
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            
        Returns:
            状态差异字典
        """
        diff_obj = self._compute_state_diff(old_state, new_state)
        return {
            "added": diff_obj.added,
            "modified": diff_obj.modified,
            "removed": list(diff_obj.removed),
            "timestamp": diff_obj.timestamp
        }
    
    def _apply_diff_to_state(
        self,
        base_state: Dict[str, Any],
        diff: StateDiff
    ) -> Dict[str, Any]:
        """应用状态差异到状态对象
        
        Args:
            base_state: 基础状态
            diff: 状态差异对象
            
        Returns:
            应用差异后的状态
        """
        result = base_state.copy()
        
        # 应用新增字段
        for key, value in diff.added.items():
            result[key] = value
        
        # 应用修改字段
        for key, change in diff.modified.items():
            if isinstance(change, dict) and "added" in change:
                # 列表增量更新
                if key in result and isinstance(result[key], list):
                    result[key].extend(change["added"])
                else:
                    result[key] = change["added"]
            else:
                result[key] = change
        
        # 移除删除字段
        for key in diff.removed:
            if key in result:
                del result[key]
        
        return result
    
    def apply_state_diff_static(
        self,
        base_state: Dict[str, Any],
        diff: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用状态差异（静态方法，保持向后兼容）
        
        Args:
            base_state: 基础状态
            diff: 状态差异
            
        Returns:
            应用差异后的状态
        """
        # 将字典格式的diff转换为StateDiff对象
        state_diff = StateDiff(
            added=diff.get("added", {}),
            modified=diff.get("modified", {}),
            removed=set(diff.get("removed", [])),
            timestamp=diff.get("timestamp", time.time())
        )
        return self._apply_diff_to_state(base_state, state_diff)