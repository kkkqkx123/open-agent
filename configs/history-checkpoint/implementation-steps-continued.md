
# Checkpoint 与 History 模块公用组件实施步骤（续）

## 阶段二：存储抽象层实施（第3-4周）

### 2.1 创建统一存储接口（续）

#### 步骤2.2.1: 创建Checkpoint存储适配器（续）
```python
            "workflow_id": workflow_id
        })
```

#### 步骤2.2.2: 创建History存储适配器
创建 `src/infrastructure/common/storage/history_storage_adapter.py`:

```python
"""History存储适配器"""

from typing import Dict, Any, Optional, List
from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageRecord, ToolCallRecord
from .base_storage import BaseStorage


class HistoryStorageAdapter(IHistoryManager):
    """History存储适配器，将IHistoryManager适配到BaseStorage"""
    
    def __init__(self, base_storage: BaseStorage):
        """初始化适配器
        
        Args:
            base_storage: 基础存储实例
        """
        self.base_storage = base_storage
    
    def record_message(self, record: MessageRecord) -> None:
        """记录消息"""
        # 将记录转换为存储格式
        data = {
            "id": record.record_id,
            "type": "message",
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),
            "message_type": record.message_type.value,
            "content": record.content,
            "metadata": record.metadata
        }
        
        # 异步保存（在同步方法中运行异步操作）
        import asyncio
        asyncio.create_task(self.base_storage.save_with_metadata(data))
    
    def record_tool_call(self, record: ToolCallRecord) -> None:
        """记录工具调用"""
        data = {
            "id": record.record_id,
            "type": "tool_call",
            "session_id": record.session_id,
            "timestamp": record.timestamp.isoformat(),
            "tool_name": record.tool_name,
            "tool_input": record.tool_input,
            "tool_output": record.tool_output,
            "metadata": record.metadata
        }
        
        import asyncio
        asyncio.create_task(self.base_storage.save_with_metadata(data))
    
    def query_history(self, query) -> 'HistoryResult':
        """查询历史记录"""
        # 实现查询逻辑
        import asyncio
        
        # 获取所有记录
        all_records = asyncio.run(self.base_storage.list({
            "session_id": query.session_id
        }))
        
        # 过滤和转换记录
        filtered_records = []
        for record in all_records:
            # 应用时间范围过滤
            if query.start_time and record.get("timestamp"):
                record_time = self.base_storage.temporal.parse_timestamp(
                    record["timestamp"], "iso"
                )
                if record_time < query.start_time:
                    continue
            
            if query.end_time and record.get("timestamp"):
                record_time = self.base_storage.temporal.parse_timestamp(
                    record["timestamp"], "iso"
                )
                if record_time > query.end_time:
                    continue
            
            # 应用记录类型过滤
            if query.record_types and record.get("type") not in query.record_types:
                continue
            
            filtered_records.append(record)
        
        # 应用分页
        total = len(filtered_records)
        if query.offset:
            filtered_records = filtered_records[query.offset:]
        if query.limit:
            filtered_records = filtered_records[:query.limit]
        
        # 转换为历史记录对象
        from src.domain.history.models import HistoryResult
        return HistoryResult(records=filtered_records, total=total)
    
    # 实现其他LLM相关方法...
    def record_llm_request(self, record) -> None:
        """记录LLM请求"""
        pass
    
    def record_llm_response(self, record) -> None:
        """记录LLM响应"""
        pass
    
    def record_token_usage(self, record) -> None:
        """记录Token使用"""
        pass
    
    def record_cost(self, record) -> None:
        """记录成本"""
        pass
    
    def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取Token使用统计"""
        pass
    
    def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取成本统计"""
        pass
    
    def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取LLM调用统计"""
        pass
```

### 2.2 实施ID生成器

#### 步骤2.2.1: 创建统一ID生成器
创建 `src/infrastructure/common/id_generator/id_generator.py`:

```python
"""统一ID生成器"""

import uuid
import hashlib
import random
import string
from typing import Optional


class IDGenerator:
    """统一ID生成器"""
    
    @staticmethod
    def generate_id(prefix: str = "", length: int = 8) -> str:
        """生成唯一ID
        
        Args:
            prefix: ID前缀
            length: 随机部分长度
            
        Returns:
            生成的ID
        """
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return f"{prefix}{random_part}" if prefix else random_part
    
    @staticmethod
    def generate_uuid() -> str:
        """生成UUID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_uuid(length: int = 8) -> str:
        """生成短UUID
        
        Args:
            length: UUID长度
            
        Returns:
            短UUID
        """
        return str(uuid.uuid4()).replace('-', '')[:length]
    
    @staticmethod
    def generate_hash(content: str, algorithm: str = "md5") -> str:
        """生成内容哈希
        
        Args:
            content: 要哈希的内容
            algorithm: 哈希算法 ("md5", "sha1", "sha256")
            
        Returns:
            哈希值
        """
        if algorithm == "md5":
            return hashlib.md5(content.encode()).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(content.encode()).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(content.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    @staticmethod
    def generate_session_id() -> str:
        """生成会话ID"""
        return IDGenerator.generate_id("session_", 12)
    
    @staticmethod
    def generate_thread_id() -> str:
        """生成线程ID"""
        return IDGenerator.generate_id("thread_", 12)
    
    @staticmethod
    def generate_checkpoint_id() -> str:
        """生成检查点ID"""
        return IDGenerator.generate_id("cp_", 16)
    
    @staticmethod
    def generate_workflow_id() -> str:
        """生成工作流ID"""
        return IDGenerator.generate_id("wf_", 12)
    
    @staticmethod
    def generate_event_id() -> str:
        """生成事件ID"""
        return IDGenerator.generate_id("event_", 16)
    
    @staticmethod
    def is_valid_id(id_str: str, pattern: Optional[str] = None) -> bool:
        """验证ID格式
        
        Args:
            id_str: ID字符串
            pattern: 验证模式（正则表达式）
            
        Returns:
            是否有效
        """
        if not id_str:
            return False
        
        if pattern:
            import re
            return bool(re.match(pattern, id_str))
        
        # 默认验证：只包含字母、数字、下划线和连字符
        return all(c.isalnum() or c in '_-' for c in id_str)
```

### 2.3 创建性能监控器

#### 步骤2.3.1: 创建性能监控器
创建 `src/infrastructure/common/monitoring/performance_monitor.py`:

```python
"""性能监控器"""

import threading
import time
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class OperationMetric:
    """操作指标"""
    name: str
    duration: float
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """性能统计"""
    total_operations: int = 0
    total_duration: float = 0.0
    successful_operations: int = 0
    failed_operations: int = 0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations
    
    @property
    def failure_rate(self) -> float:
        """失败率"""
        return 1.0 - self.success_rate


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        """初始化性能监控器
        
        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self._lock = threading.RLock()
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._stats: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self._start_times: Dict[str, float] = {}
    
    def start_operation(self, operation_name: str) -> str:
        """开始操作计时
        
        Args:
            operation_name: 操作名称
            
        Returns:
            操作ID
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"
        with self._lock:
            self._start_times[operation_id] = time.time()
        return operation_id
    
    def end_operation(
        self,
        operation_id: str,
        operation_name: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """结束操作计时
        
        Args:
            operation_id: 操作ID
            operation_name: 操作名称
            success: 是否成功
            metadata: 元数据
            
        Returns:
            操作持续时间（秒）
        """
        start_time = self._start_times.pop(operation_id, None)
        if start_time is None:
            return 0.0
        
        duration = time.time() - start_time
        
        # 记录指标
        metric = OperationMetric(
            name=operation_name,
            duration=duration,
            timestamp=datetime.now(),
            success=success,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics[operation_name].append(metric)
            self._update_stats(operation_name, metric)
        
        return duration
    
    def record_operation(
        self,
        operation_name: str,
        duration: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """直接记录操作指标
        
        Args:
            operation_name: 操作名称
            duration: 持续时间
            success: 是否成功
            metadata: 元数据
        """
        metric = OperationMetric(
            name=operation_name,
            duration=duration,
            timestamp=datetime.now(),
            success=success,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics[operation_name].append(metric)
            self._update_stats(operation_name, metric)
    
    def _update_stats(self, operation_name: str, metric: OperationMetric) -> None:
        """更新统计信息"""
        stats = self._stats[operation_name]
        stats.total_operations += 1
        stats.total_duration += metric.duration
        
        if metric.success:
            stats.successful_operations += 1
        else:
            stats.failed_operations += 1
        
        stats.min_duration = min(stats.min_duration, metric.duration)
        stats.max_duration = max(stats.max_duration, metric.duration)
        stats.avg_duration = stats.total_duration / stats.total_operations
    
    def get_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计
        
        Args:
            operation_name: 操作名称，如果为None则返回所有统计
            
        Returns:
            性能统计信息
        """
        with self._lock:
            if operation_name:
                stats = self._stats.get(operation_name)
                if not stats:
                    return {}
                
                return {
                    "operation": operation_name,
                    "total_operations": stats.total_operations,
                    "successful_operations": stats.successful_operations,
                    "failed_operations": stats.failed_operations,
                    "success_rate": stats.success_rate,
                    "failure_rate": stats.failure_rate,
                    "min_duration": stats.min_duration,
                    "max_duration": stats.max_duration,
                    "avg_duration": stats.avg_duration,
                    "total_duration": stats.total_duration
                }
            else:
                return {
                    name: self.get_stats(name)
                    for name in self._stats.keys()
                }
    
    def get_recent_metrics(
        self,
        operation_name: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[OperationMetric]:
        """获取最近的指标
        
        Args:
            operation_name: 操作名称
            limit: 限制数量
            since: 起始时间
            
        Returns:
            指标列表
        """
        with self._lock:
            metrics = list(self._metrics.get(operation_name, []))
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            return metrics[-limit:] if limit else metrics
    
    def reset_stats(self, operation_name: Optional[str] = None) -> None:
        """重置统计信息
        
        Args:
            operation_name: 操作名称，如果为None则重置所有统计
        """
        with self._lock:
            if operation_name:
                self._metrics[operation_name].clear()
                self._stats[operation_name] = PerformanceStats()
            else:
                self._metrics.clear()
                self._stats.clear()
    
    def get_slow_operations(
        self,
        threshold: float = 1.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取慢操作
        
        Args:
            threshold: 时间阈值（秒）
            limit: 限制数量
            
        Returns:
            慢操作列表
        """
        slow_operations = []
        
        with self._lock:
            for operation_name, metrics in self._metrics.items():
                for metric in metrics:
                    if metric.duration >= threshold:
                        slow_operations.append({
                            "operation": operation_name,
                            "duration": metric.duration,
                            "timestamp": metric.timestamp.isoformat(),
                            "success": metric.success,
                            "metadata": metric.metadata
                        })
        
        # 按持续时间排序
        slow_operations.sort(key=lambda x: x["duration"], reverse=True)
        return slow_operations[:limit]
    
    def get_error_rate_trend(
        self,
        operation_name: str,
        window_minutes: int = 60
    ) -> Dict[str, Any]:
        """获取错误率趋势
        
        Args:
            operation_name: 操作名称
            window_minutes: 时间窗口（分钟）
            
        Returns:
            错误率趋势信息
        """
        since = datetime.now() - timedelta(minutes=window_minutes)
        metrics = self.get_recent_metrics(operation_name, since=since)
        
        if not metrics:
            return {"error_rate": 0.0, "total_operations": 0}
        
        total = len(metrics)
        errors = sum(1 for m in metrics if not m.success)
        
        return {
            "error_rate": errors / total,
            "total_operations": total,
            "error_operations": errors,
            "window_minutes": window_minutes
        }
```

## 阶段三：迁移和集成（第5-6周）

### 3.1 迁移Checkpoint模块

#### 步骤3.1.1: 更新Checkpoint管理器
修改 `src/application/checkpoint/manager.py`:

```python
"""Checkpoint管理器 - 重构版本"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ...domain.checkpoint.interfaces import ICheckpointManager, ICheckpointStore, ICheckpointPolicy
from ...domain.checkpoint.config import CheckpointConfig
from ...infrastructure.common.serialization.universal_serializer import UniversalSerializer
from ...infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from ...infrastructure.common.temporal.temporal_manager import TemporalManager
from ...infrastructure.common.metadata.metadata_manager import MetadataManager
from ...infrastructure.common.id_generator.id_generator import IDGenerator
from ...infrastructure.common.monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class CheckpointManager(ICheckpointManager):
    """Checkpoint管理器实现 - 重构版本"""
    
    def __init__(
        self,
        checkpoint_store: ICheckpointStore,
        config: CheckpointConfig,
        policy: Optional[ICheckpointPolicy] = None,
        serializer: Optional[UniversalSerializer] = None,
        cache_manager: Optional[EnhancedCacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化checkpoint管理器
        
        Args:
            checkpoint_store: checkpoint存储
            config: checkpoint配置
            policy: checkpoint策略
            serializer: 序列化器
            cache_manager: 缓存管理器
            performance_monitor: 性能监控器
        """
        self.checkpoint_store = checkpoint_store
        self.config = config
        self.policy = policy or DefaultCheckpointPolicy(config)
        self.serializer = serializer or UniversalSerializer()
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        
        # 公用组件
        self.temporal = TemporalManager()
        self.metadata = MetadataManager()
        self.id_generator = IDGenerator()
        
        logger.debug(f"Checkpoint管理器初始化完成，存储类型: {config.storage_type}")
    
    async def create_checkpoint(
        self,
        thread_id: str,
        workflow_id: str,
        state: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建checkpoint"""
        operation_id = self.monitor.start_operation("create_checkpoint")
        
        try:
            # 生成checkpoint ID
            checkpoint_id = self.id_generator.generate_checkpoint_id()
            
            # 准备checkpoint数据
            checkpoint_data = {
                'id': checkpoint_id,
                'thread_id': thread_id,
                'workflow_id': workflow_id,
                'state_data': state,
                'metadata': metadata or {},
                'created_at': self.temporal.now(),
                'updated_at': self.temporal.now()
            }
            
            # 序列化状态数据
            serialized_state = self.serializer.serialize(state, "compact_json")
            checkpoint_data['serialized_state'] = serialized_state
            
            # 保存checkpoint
            success = await self.checkpoint_store.save(checkpoint_data)
            
            if success:
                # 缓存checkpoint
                if self.cache:
                    await self.cache.set(checkpoint_id, checkpoint_data, ttl=3600)
                
                logger.debug(f"Checkpoint创建成功: {checkpoint_id}")
                
                # 记录性能指标
                duration = self.monitor.end_operation(
                    operation_id, "create_checkpoint", True,
                    {"thread_id": thread_id, "workflow_id": workflow_id}
                )
                
                return checkpoint_id
            else:
                raise RuntimeError("创建checkpoint失败")
                
        except Exception as e:
            logger.error(f"创建checkpoint失败: {e}")
            
            # 记录失败指标
            self.monitor.end_operation(
                operation_id, "create_checkpoint", False,
                {"error": str(e)}
            )
            
            raise
    
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint"""
        operation_id = self.monitor.start_operation("get_checkpoint")
        
        try:
            # 先从缓存获取
            if self.cache:
                cached_checkpoint = await self.cache.get(checkpoint_id)
                if cached_checkpoint:
                    self.monitor.end_operation(
                        operation_id, "get_checkpoint", True,
                        {"cache_hit": True}
                    )
                    return cached_checkpoint
            
            # 从存储加载
            checkpoint = await self.checkpoint_store.load_by_thread(thread_id, checkpoint_id)
            
            if checkpoint:
                # 反序列化状态数据
                if 'serialized_state' in checkpoint:
                    checkpoint['state_data'] = self.serializer.deserialize(
                        checkpoint['serialized_state'], "compact_json"
                    )
                
                # 缓存结果
                if self.cache:
                    await self.cache.set(checkpoint_id, checkpoint, ttl=3600)
                
                self.monitor.end_operation(
                    operation_id, "get_checkpoint", True,
                    {"cache_hit": False}
                )
                
                return checkpoint
            
            return None
            
        except Exception as e:
            logger.error(f"获取checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "get_checkpoint", False,
                {"error": str(e)}
            )
            
            return None
    
    # 实现其他方法...
```

#### 步骤3.1.2: 更新Checkpoint存储实现
修改 `src/infrastructure/checkpoint/memory_store.py`:

```python
"""基于LangGraph标准的内存checkpoint存储实现 - 重构版本"""

import logging
import uuid
import time
from typing import Dict, Any, Optional, List, Tuple, Union, cast
from datetime import datetime

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import CheckpointTuple

from ...domain.checkpoint.interfaces import ICheckpointSerializer
from ...infrastructure.common.serialization.universal_serializer import UniversalSerializer
from ...infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from ...infrastructure.common.temporal.temporal_manager import TemporalManager
from ...infrastructure.common.metadata.metadata_manager import MetadataManager
from ...infrastructure.common.monitoring.performance_monitor import PerformanceMonitor
from .types import CheckpointError, CheckpointNotFoundError, CheckpointStorageError

logger = logging.getLogger(__name__)


class MemoryCheckpointStore(BaseCheckpointStore):
    """基于LangGraph标准的内存checkpoint存储实现 - 重构版本"""
    
    def __init__(
        self,
        serializer: Optional[ICheckpointSerializer] = None,
        max_checkpoints_per_thread: int = 1000,
        enable_performance_monitoring: bool = True,
        universal_serializer: Optional[UniversalSerializer] = None,
        cache_manager: Optional[EnhancedCacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化内存存储"""
        super().__init__(serializer, max_checkpoints_per_thread, enable_performance_monitoring)
        
        # 使用公用组件
        self.universal_serializer = universal_serializer or UniversalSerializer()
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        self.temporal = TemporalManager()
        self.metadata = MetadataManager()
        
        # 使用内存存储，适合开发和测试环境
        self._checkpointer = InMemorySaver()
        logger.info("使用内存存储")
        
        self._adapter = MemoryCheckpointAdapter(self._checkpointer, serializer)
        
        # 内部checkpoint_id到thread_id的映射，用于支持load和delete方法
        self._checkpoint_thread_mapping: Dict[str, str] = {}
        
        logger.debug("checkpoint存储初始化完成")
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        operation_id = self.monitor.start_operation("save_checkpoint")
        
        try:
            # 检查checkpoint数量限制
            thread_id = checkpoint_data.get('thread_id')
            if not thread_id:
                raise ValueError("checkpoint_data必须包含'thread_id'")
            
            current_count = await self.get_checkpoint_count(thread_id)
            if current_count >= self.max_checkpoints_per_thread:
                logger.warning(f"线程 {thread_id} 的checkpoint数量已达到最大限制 {self.max_checkpoints_per_thread}")
                # 清理旧的checkpoint
                await self.cleanup_old_checkpoints(thread_id, self.max_checkpoints_per_thread - 1)
            
            workflow_id = checkpoint_data['workflow_id']
            state = checkpoint_data['state_data']
            metadata = checkpoint_data.get('metadata', {})
            
            # 使用公用组件处理元数据
            normalized_metadata = self.metadata.normalize_metadata(metadata)
            checkpoint_data['metadata'] = normalized_metadata
            
            # 创建LangGraph配置
            config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
            
            # 创建LangGraph checkpoint
            checkpoint, enhanced_metadata = self._adapter._create_langgraph_checkpoint(
                state, workflow_id, normalized_metadata
            )
            
            # 更新映射关系
            self._update_checkpoint_mapping(thread_id, checkpoint['id'])
            
            # 保存checkpoint
            success = self._adapter.put(config, checkpoint, enhanced_metadata, {})
            
            if success:
                # 缓存checkpoint
                if self.cache:
                    await self.cache.set(checkpoint['id'], checkpoint_data, ttl=3600)
                
                logger.debug(f"成功保存checkpoint，thread_id: {thread_id}, workflow_id: {workflow_id}")
                
                # 记录性能指标
                self.monitor.end_operation(
                    operation_id, "save_checkpoint", True,
                    {"thread_id": thread_id, "workflow_id": workflow_id}
                )
                
                return success
            else:
                raise RuntimeError("保存checkpoint失败")
                
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "save_checkpoint", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"保存checkpoint失败: {e}")
    
    # 实现其他方法...
```

### 3.2 迁移History模块

#### 步骤3.2.1: 更新History管理器
修改 `src/application/history/manager.py`:

```python
"""历史管理器 - 重构版本"""

from typing import Dict, Any
from datetime import datetime
import json

from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult, MessageType
from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord
from src.infrastructure.history.storage.file_storage import FileHistoryStorage

# 导入公用组件
from src.infrastructure.common.serialization.universal_serializer import UniversalSerializer
from src.infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from src.infrastructure.common.temporal.temporal_manager import TemporalManager
from src.infrastructure.common.metadata.metadata_manager import MetadataManager
from src.infrastructure.common.id_generator.id_generator import IDGenerator
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor


class HistoryManager(IHistoryManager):
    """历史管理器实现 - 重构版本"""
    
    def __init__(
        self,
        storage: FileHistoryStorage,
        serializer: Optional[UniversalSerializer] = None,
        cache_manager: Optional[EnhancedCacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化历史管理器"""
        self.storage = storage
        
        # 公用组件
        self.serializer = serializer or UniversalSerializer()
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        self.temporal = TemporalManager()
        self.metadata = MetadataManager()
        self.id_generator = IDGenerator()
    
    def record_message(self, record: MessageRecord) -> None:
        """记录消息"""
        operation_id = self.monitor.start_operation("record_message")
        
        try:
            # 使用公用组件处理记录
            processed_record = self._process_record(record)
            
            # 序列化记录
            serialized_record = self.serializer.serialize(processed_record, "compact_json")
            
            # 存储记录
            self.storage.store_record(processed_record)
            
            # 缓存记录
            if self.cache:
                cache_key = f"message:{record.record_id}"
                import asyncio
                asyncio.create_task(self.cache.set(cache_key, processed_record, ttl=1800))
            
            self.monitor.end_operation(operation_id, "record_message", True)
            
        except Exception as e:
            self.monitor.end_operation(operation_id, "record_message", False, {"error": str(e)})
            raise
    
    def _process_record(self, record) -> Any:
        """处理记录，使用公用组件"""
        # 标准化元数据
        if hasattr(record, 'metadata'):
            record.metadata = self.metadata.normalize_metadata(record.metadata)
        
        # 处理时间戳
        if hasattr(record, 'timestamp'):
            record.timestamp = self.temporal.format_timestamp(record.timestamp, "iso")
        
        return record
    
    # 实现其他方法...
```

### 3.3 集成测试

#### 步骤3.3.1: 创建集成测试
创建 `tests/integration/test_checkpoint_history_integration.py`:

```python
"""Checkpoint与History模块集成测试"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.application.checkpoint.manager import CheckpointManager
from src.application.history.manager import HistoryManager
from src.infrastructure.common.serialization.universal_serializer import UniversalSerializer
from src.infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from pathlib import Path


class TestCheckpointHistoryIntegration:
    """Checkpoint与History模块集成测试"""
    
    @pytest.fixture
    async def setup_components(self):
        """设置测试组件"""
        # 创建公用组件
        serializer = UniversalSerializer()
        cache_manager = EnhancedCacheManager(max_size=100, default_ttl=300)
        performance_monitor = PerformanceMonitor()
        
        # 创建存储
        checkpoint_store = MemoryCheckpointStore(universal_serializer=serializer)
        history_storage = FileHistoryStorage(Path("./test_history"))
        
        # 创建管理器
        checkpoint_manager = CheckpointManager(
            checkpoint_store=checkpoint_store,
            config=None,  # 使用默认配置
            serializer=serializer,
            cache_manager=cache_manager,
            performance_monitor=performance_monitor
        )
        
        history_manager = HistoryManager(
            storage=history_storage,
            serializer=serializer,
            cache_manager=cache_manager,
            performance_monitor=performance_monitor
        )
        
        return checkpoint_manager, history_manager, performance_monitor
    
    @pytest.mark.asyncio
    async def test_shared_components_usage(self, setup_components):
        """测试共享组件使用"""
        checkpoint_manager, history_manager, monitor = setup_components
        
        # 测试序列化器共享
        test_data = {"test": "data", "timestamp": datetime.now()}
        serialized = checkpoint_manager.serializer.serialize(test_data)
        deserialized = history_manager.serializer.deserialize(serialized)
        assert deserialized["test"] == test_data["test"]
        
        # 测试缓存共享
        cache_key = "test_key"
        await checkpoint_manager.cache.set(cache_key, test_data)
        cached_data = await history_manager.cache.get(cache_key)
        assert cached_data == test_data
        
        # 测试性能监控共享
        operation_id = monitor.start_operation("test_operation")
        monitor.end_operation(operation_id, "test_operation", True)
        
        stats = monitor.get_stats("test_operation")
        assert stats["total_operations"] == 1
        assert stats["successful_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_checkpoint_history_workflow(self, setup_components):
        """测试Checkpoint与History工作流"""
        checkpoint_manager, history_manager, monitor = setup_components
        
        thread_id = "test_thread"
        workflow_id = "test_workflow"
        
        # 1. 创建checkpoint
        state = {"step": 1, "data": "test"}
        checkpoint_id = await checkpoint_manager.create_checkpoint(
            thread_id, workflow_id, state
        )
        
        # 2. 记录历史消息
        from src.domain.history.models import MessageRecord, MessageType
        
        message = MessageRecord(
            record_id=checkpoint_manager.id_generator.generate_id(),
            session_id="test_session",
            timestamp=datetime.now(),
            record_type="message",
            message_type=MessageType.USER,
            content="Test message",
            metadata={"checkpoint_id": checkpoint_id}
        )
        
        history_manager.record_message(message)
        
        # 3. 验证性能指标
        checkpoint_stats = monitor.get_stats("create_checkpoint")
        history_stats = monitor.get_stats("record_message")
        
        assert checkpoint_stats["total_operations"] == 1
        assert history_stats["total_operations"] == 1
        
        # 4. 验证数据一致性
        retrieved_checkpoint = await checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
        assert retrieved_checkpoint is not None
        assert retrieved_checkpoint["workflow_id"] == workflow_id
```

### 3.4 性能验证

#### 步骤3.4.1: 创建性能基准测试
创建 `tests/performance/test_shared_components_performance.py`:

```python
"""共享组件性能基准测试"""

import pytest
import asyncio
import time
from datetime import datetime
from src.infrastructure.common.serialization.universal_serializer import UniversalSerializer
from src.infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor


class TestSharedComponentsPerformance:
    """共享组件性能测试"""
    
    @pytest.fixture
    def setup_components(self):
        """设置测试组件"""
        serializer = UniversalSerializer()
        cache_manager = EnhancedCacheManager(max_size=1000, default_ttl=300)
        monitor = PerformanceMonitor()
        
        return serializer, cache_manager, monitor
    
    def test_serialization_performance(self, setup_components):
        """测试序列化性能"""
        serializer, _, _ = setup_components
        
        # 准备测试数据
        large_data = {
            "messages": [{"content": f"Message {i}"} for i in range(1000)],
            "metadata": {"key": "value" for _ in range(100)},
            "timestamp": datetime.now()
        }
        
        # 测试JSON序列化性能
        start_time = time.time()
        for _ in range(100):
            serialized = serializer.serialize(large_data, "json")
            deserialized = serializer.deserialize(serialized, "json")
        json_duration = time.time() - start_time
        
        # 测试紧凑JSON序列化性能
        start_time = time.time()
        for _ in range(100):
            serialized = serializer.serialize(large_data, "compact_json")
            deserialized = serializer.deserialize(serialized, "compact_json")
        compact_duration = time.time() - start_time
        
        # 测试Pickle序列化性能
        start_time = time.time()
        for _ in range(100):
            serialized = serializer.serialize(large_data, "pickle")
            deserialized = serializer.deserialize(serialized, "pickle")
        pickle_duration = time.time() - start_time
        
        print(f"JSON序列化: {json_duration:.3f}s")
        print(f"紧凑JSON序列化: {compact_duration:.3f}s")
        print(f"Pickle序列化: {pickle_duration:.3f}s")
        
        # 验证性能要求
        assert json_duration < 5.0  # 5秒内完成100次序列化
        assert compact_duration < 5.0
        assert pickle_duration < 5.0
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, setup_components):
        """测试缓存性能"""
        _, cache_manager, _ = setup_components
        
        # 准备测试数据
        test_data = {"key": "value", "data": "x" * 1000}
        
        # 测试写入性能
        start_time = time.time()
        for i in range(1000):
            await cache_manager.set(f"key_{i}", test_data)
        write_duration = time.time() - start_time
        
        # 测试读取性能
        start_time = time.time()
        for i in range(1000):
            await cache_manager.get(f"key_{i}")
        read_duration = time.time() - start_time
        
        # 测试缓存命中率
        stats = cache_manager.get_stats()
        
        print(f"缓存写入: {write_duration:.3f}s (1000次)")
        print(f"缓存读取: {read_duration:.3f}s (1000次)")
        print(f"缓存命中率: {stats['hit_rate']:.2%}")
        
        # 验证性能要求
        assert write_duration < 2.0  # 2秒内完成1000次写入
        assert read_duration < 1.0    # 1秒内完成1000次读取
        assert stats["hit_rate"] > 0.99  # 命中率超过99%
    
    def test_monitoring_performance(self, setup_components):
        """测试性能监控开销"""
        _, _, monitor = setup_components
        
        # 测试监控开销
        start_time = time.time()
        for i in range(10000):
            operation_id = monitor.start_operation("test_operation")
            # 模拟操作
            time.sleep(0.0001)  # 0.1ms
            monitor.end_operation(operation_id, "test_operation", True)
        monitoring_duration = time.time() - start_time
        
        stats = monitor.get_stats("test_operation")
        
        print(f"监控开销: {monitoring_duration:.3f}s (10000次操作)")
        print(f"平均操作时间: {stats['avg_duration']:.6f}s")
        
        # 验证监控开销
        assert monitoring_duration < 5.0  # 5秒内完成10000次监控
        assert stats["total_operations"] == 10000
```

## 验收标准

### 4.1 功能验收标准
- [ ] 所有公用组件实现完成
- [ ] Checkpoint和History模块成功迁移
- [ ] 共享组件正常工作
- [ ] 现有功能保持兼容

### 4.2 性能验收标准
- [ ] 序列化