"""存储后端基类

提供统一的存储后端基础实现，内置数据转换逻辑，使用基础设施组件。
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator, Union
from src.services.logger.injection import get_logger

from src.interfaces.storage.base import IStorage
from src.interfaces.storage.exceptions import StorageError, StorageConnectionError
from src.infrastructure.storage import (
    BaseStorage,
    StorageErrorHandler,
    StorageMetrics,
    MetricsCollector,
    TransactionManager,
    HealthChecker,
    StorageHealthChecker,
    HealthStatus
)


logger = get_logger(__name__)


class BaseStorageBackend(IStorage, ABC):
    """存储后端基类
    
    提供统一的存储后端基础实现，内置数据转换逻辑，
    使用基础设施组件进行错误处理、指标收集、事务管理和健康检查。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化存储后端
        
        Args:
            **config: 配置参数
        """
        self._config = config
        self._connected = False
        
        # 基础设施组件
        self._error_handler = StorageErrorHandler(
            max_retries=config.get("max_retries", 3),
            retry_delay=config.get("retry_delay", 1.0),
            backoff_factor=config.get("backoff_factor", 2.0),
            timeout=config.get("timeout", 30.0)
        )
        
        self._metrics = StorageMetrics(
            max_history_size=config.get("max_history_size", 1000),
            time_series_window=config.get("time_series_window", 3600)
        )
        
        self._transaction_manager = TransactionManager(
            max_concurrent_transactions=config.get("max_concurrent_transactions", 100),
            transaction_timeout=config.get("transaction_timeout", 300.0),
            auto_cleanup_interval=config.get("auto_cleanup_interval", 60.0)
        )
        
        self._health_checker = HealthChecker(
            check_interval=config.get("health_check_interval", 60.0),
            timeout=config.get("health_check_timeout", 10.0)
        )
        
        # 存储专用健康检查器
        self._storage_health_checker = StorageHealthChecker(self._health_checker)
        
        # 通用配置
        self.enable_compression = config.get("enable_compression", False)
        self.compression_threshold = config.get("compression_threshold", 1024)
        self.enable_ttl = config.get("enable_ttl", False)
        self.default_ttl_seconds = config.get("default_ttl_seconds", 3600)
        
        # 线程安全
        self._lock = asyncio.Lock()
        
        # 启动基础设施组件
        self._start_infrastructure()
    
    def _start_infrastructure(self) -> None:
        """启动基础设施组件"""
        # 启动事务管理器
        asyncio.create_task(self._transaction_manager.start())
        
        # 启动健康检查器
        asyncio.create_task(self._health_checker.start())
        
        # 注册存储健康检查
        self._storage_health_checker.register_storage_checks(self)
    
    async def connect(self) -> None:
        """连接到存储后端"""
        async with self._lock:
            if self._connected:
                return
            
            try:
                await self._connect_impl()
                self._connected = True
                logger.info(f"{self.__class__.__name__} connected")
                
            except Exception as e:
                raise StorageConnectionError(f"Failed to connect {self.__class__.__name__}: {e}")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        async with self._lock:
            if not self._connected:
                return
            
            try:
                # 停止基础设施组件
                await self._transaction_manager.stop()
                await self._health_checker.stop()
                
                # 断开连接
                await self._disconnect_impl()
                self._connected = False
                logger.info(f"{self.__class__.__name__} disconnected")
                
            except Exception as e:
                raise StorageConnectionError(f"Failed to disconnect {self.__class__.__name__}: {e}")
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    # 基础CRUD操作
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据"""
        return await self._error_handler.handle(
            "save",
            lambda: self._save_with_metrics(data)
        )
    
    async def _save_with_metrics(self, data: Dict[str, Any]) -> str:
        """带指标收集的保存实现"""
        with MetricsCollector(self._metrics, "save") as collector:
            # 数据转换和验证
            processed_data = self._transform_to_storage_format(data)
            
            # 执行保存
            result_id = await self._save_impl(processed_data)
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["data_id"] = result_id
                collector.metadata["data_size"] = len(str(processed_data))
            
            return result_id
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        return await self._error_handler.handle(
            "load",
            lambda: self._load_with_metrics(id)
        )
    
    async def _load_with_metrics(self, id: str) -> Optional[Dict[str, Any]]:
        """带指标收集的加载实现"""
        with MetricsCollector(self._metrics, "load") as collector:
            # 执行加载
            storage_data = await self._load_impl(id)
            
            if storage_data is None:
                return None
            
            # 数据转换
            domain_data = self._transform_from_storage_format(storage_data)
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["data_id"] = id
                collector.metadata["data_found"] = True
                collector.metadata["data_size"] = len(str(storage_data))
            
            return domain_data
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        return await self._error_handler.handle(
            "update",
            lambda: self._update_with_metrics(id, updates)
        )
    
    async def _update_with_metrics(self, id: str, updates: Dict[str, Any]) -> bool:
        """带指标收集的更新实现"""
        with MetricsCollector(self._metrics, "update") as collector:
            # 加载现有数据
            current_data = await self._load_impl(id)
            if current_data is None:
                return False
            
            # 更新数据
            current_data.update(updates)
            current_data["updated_at"] = time.time()
            
            # 转换并保存
            processed_data = self._transform_to_storage_format(current_data)
            result_id = await self._save_impl(processed_data)
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["data_id"] = id
                collector.metadata["update_success"] = (result_id == id)
            
            return result_id == id
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
        return await self._error_handler.handle(
            "delete",
            lambda: self._delete_with_metrics(id)
        )
    
    async def _delete_with_metrics(self, id: str) -> bool:
        """带指标收集的删除实现"""
        with MetricsCollector(self._metrics, "delete") as collector:
            # 执行删除
            result = await self._delete_impl(id)
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["data_id"] = id
                collector.metadata["delete_success"] = result
            
            return result
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        return await self._error_handler.handle(
            "exists",
            lambda: self._exists_with_metrics(id)
        )
    
    async def _exists_with_metrics(self, id: str) -> bool:
        """带指标收集的存在检查实现"""
        with MetricsCollector(self._metrics, "exists") as collector:
            # 执行存在检查
            result = await self._exists_impl(id)
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["data_id"] = id
                collector.metadata["data_exists"] = result
            
            return result
    
    # 查询操作
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        return await self._error_handler.handle(
            "list",
            lambda: self._list_with_metrics(filters, limit)
        )
    
    async def _list_with_metrics(self, filters: Dict[str, Any], limit: Optional[int]) -> List[Dict[str, Any]]:
        """带指标收集的列表实现"""
        with MetricsCollector(self._metrics, "list") as collector:
            # 执行列表查询
            storage_results = await self._list_impl(filters, limit)
            
            # 数据转换
            domain_results = []
            for storage_data in storage_results:
                try:
                    domain_data = self._transform_from_storage_format(storage_data)
                    domain_results.append(domain_data)
                except Exception as e:
                    logger.warning(f"转换数据失败，跳过: {e}")
                    continue
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["filter_count"] = len(filters)
                collector.metadata["limit"] = limit
                collector.metadata["result_count"] = len(domain_results)
            
            return domain_results
    
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询"""
        return await self._error_handler.handle(
            "query",
            lambda: self._query_with_metrics(query, params)
        )
    
    async def _query_with_metrics(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """带指标收集的查询实现"""
        with MetricsCollector(self._metrics, "query") as collector:
            # 执行查询
            storage_results = await self._query_impl(query, params)
            
            # 数据转换
            domain_results = []
            for storage_data in storage_results:
                try:
                    domain_data = self._transform_from_storage_format(storage_data)
                    domain_results.append(domain_data)
                except Exception as e:
                    logger.warning(f"转换数据失败，跳过: {e}")
                    continue
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["query_type"] = query.split()[0] if query else "unknown"
                collector.metadata["param_count"] = len(params)
                collector.metadata["result_count"] = len(domain_results)
            
            return domain_results
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        return await self._error_handler.handle(
            "count",
            lambda: self._count_with_metrics(filters)
        )
    
    async def _count_with_metrics(self, filters: Dict[str, Any]) -> int:
        """带指标收集的计数实现"""
        with MetricsCollector(self._metrics, "count") as collector:
            # 执行计数
            result = await self._count_impl(filters)
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["filter_count"] = len(filters)
                collector.metadata["count_result"] = result
            
            return result
    
    # 高级操作
    async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务"""
        return await self._error_handler.handle(
            "transaction",
            lambda: self._transaction_with_metrics(operations)
        )
    
    async def _transaction_with_metrics(self, operations: List[Dict[str, Any]]) -> bool:
        """带指标收集的事务实现"""
        with MetricsCollector(self._metrics, "transaction") as collector:
            # 创建事务
            transaction_id = self._transaction_manager.create_transaction()
            
            try:
                # 添加操作到事务
                for operation in operations:
                    operation_type = operation.get("type")
                    if operation_type is None:
                        raise ValueError("Operation must have a 'type' field")
                    self._transaction_manager.add_operation(
                        transaction_id,
                        operation_type,
                        operation.get("data", {})
                    )
                
                # 执行事务
                result = await self._transaction_manager.execute_transaction(
                    transaction_id,
                    self._execute_transaction_operations
                )
                
                # 更新元数据
                if collector.metadata is not None:
                    collector.metadata["transaction_id"] = transaction_id
                    collector.metadata["operation_count"] = len(operations)
                    collector.metadata["transaction_success"] = True
                
                return result
                
            except Exception as e:
                # 更新元数据
                if collector.metadata is not None:
                    collector.metadata["transaction_id"] = transaction_id
                    collector.metadata["operation_count"] = len(operations)
                    collector.metadata["transaction_success"] = False
                    collector.metadata["transaction_error"] = str(e)
                
                raise
    
    async def _execute_transaction_operations(self, operations: List) -> Any:
        """执行事务操作"""
        # 这里应该由具体实现类提供事务执行逻辑
        # 默认实现：顺序执行操作
        for operation in operations:
            op_type = operation.operation_type.value
            data = operation.data
            
            if op_type == "save":
                await self.save(data)
            elif op_type == "update":
                await self.update(data.get("id"), data.get("updates", {}))
            elif op_type == "delete":
                await self.delete(data.get("id"))
        
        return True
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存"""
        return await self._error_handler.handle(
            "batch_save",
            lambda: self._batch_save_with_metrics(data_list)
        )
    
    async def _batch_save_with_metrics(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """带指标收集的批量保存实现"""
        with MetricsCollector(self._metrics, "batch_save") as collector:
            # 转换数据
            processed_data_list = []
            for data in data_list:
                try:
                    processed_data = self._transform_to_storage_format(data)
                    processed_data_list.append(processed_data)
                except Exception as e:
                    logger.warning(f"转换数据失败，跳过: {e}")
                    continue
            
            # 执行批量保存
            result_ids = await self._batch_save_impl(processed_data_list)
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["input_count"] = len(data_list)
                collector.metadata["processed_count"] = len(processed_data_list)
                collector.metadata["result_count"] = len(result_ids)
            
            return result_ids
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除"""
        return await self._error_handler.handle(
            "batch_delete",
            lambda: self._batch_delete_with_metrics(ids)
        )
    
    async def _batch_delete_with_metrics(self, ids: List[str]) -> int:
        """带指标收集的批量删除实现"""
        with MetricsCollector(self._metrics, "batch_delete") as collector:
            # 执行批量删除
            count = await self._batch_delete_impl(ids)
            
            # 更新元数据
            if collector.metadata is not None:
                collector.metadata["input_count"] = len(ids)
                collector.metadata["deleted_count"] = count
            
            return count
    
    # 流式操作
    async def stream_list(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列出数据"""
        async for batch in self._stream_list_with_metrics(filters, batch_size):
            yield batch
    
    async def _stream_list_with_metrics(
        self,
        filters: Dict[str, Any],
        batch_size: int
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """带指标收集的流式列表实现"""
        operation_id = self._metrics.start_operation("stream_list")
        
        try:
            async for storage_batch in self._stream_list_impl(filters, batch_size):
                # 数据转换
                domain_batch = []
                for storage_data in storage_batch:
                    try:
                        domain_data = self._transform_from_storage_format(storage_data)
                        domain_batch.append(domain_data)
                    except Exception as e:
                        logger.warning(f"转换数据失败，跳过: {e}")
                        continue
                
                if domain_batch:  # 只返回非空批次
                    yield domain_batch
            
            # 记录成功指标
            self._metrics.record_operation(
                "stream_list",
                True,
                time.time(),  # 这里应该记录实际持续时间
                metadata={"batch_size": batch_size}
            )
            
        except Exception as e:
            # 记录失败指标
            self._metrics.record_operation(
                "stream_list",
                False,
                time.time(),  # 这里应该记录实际持续时间
                error=str(e)
            )
            raise
    
    # 健康检查
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 获取基础健康信息
            health_info = await self._health_check_impl()
            
            # 添加基础设施组件状态
            health_info["infrastructure"] = {
                "error_handler": {
                    "error_stats": self._error_handler.get_error_stats()
                },
                "metrics": {
                    "summary": self._metrics.get_summary_report()
                },
                "transaction_manager": {
                    "statistics": self._transaction_manager.get_statistics()
                },
                "health_checker": {
                    "overall_health": self._health_checker.get_overall_health().__dict__
                }
            }
            
            # 添加配置信息
            health_info["config"] = {
                "enable_compression": self.enable_compression,
                "compression_threshold": self.compression_threshold,
                "enable_ttl": self.enable_ttl,
                "default_ttl_seconds": self.default_ttl_seconds,
            }
            
            return health_info
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    # 数据转换方法（内置转换逻辑）
    def _transform_to_storage_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """领域对象转存储格式
        
        Args:
            data: 领域数据
            
        Returns:
            存储格式数据
        """
        # 基础转换逻辑
        storage_data = data.copy()
        
        # 添加时间戳
        current_time = time.time()
        if "created_at" not in storage_data:
            storage_data["created_at"] = current_time
        storage_data["updated_at"] = current_time
        
        # 添加ID（如果没有）
        if "id" not in storage_data:
            storage_data["id"] = str(uuid.uuid4())
        
        # TTL处理
        if self.enable_ttl and "expires_at" not in storage_data:
            storage_data["expires_at"] = current_time + self.default_ttl_seconds
        
        # 压缩处理（如果需要）
        if self.enable_compression:
            storage_data = self._compress_data(storage_data)
        
        return storage_data
    
    def _transform_from_storage_format(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """存储格式转领域对象
        
        Args:
            storage_data: 存储格式数据
            
        Returns:
            领域数据
        """
        # 基础转换逻辑
        domain_data = storage_data.copy()
        
        # 解压缩处理（如果需要）
        if self.enable_compression and self._is_compressed_data(domain_data):
            domain_data = self._decompress_data(domain_data)
        
        # 移除内部字段
        internal_fields = ["created_at", "updated_at", "expires_at"]
        for field in internal_fields:
            domain_data.pop(field, None)
        
        return domain_data
    
    def _compress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """压缩数据"""
        # 这里应该实现具体的压缩逻辑
        # 默认实现：不压缩
        return data
    
    def _decompress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解压缩数据"""
        # 这里应该实现具体的解压缩逻辑
        # 默认实现：不解压缩
        return data
    
    def _is_compressed_data(self, data: Dict[str, Any]) -> bool:
        """检查数据是否已压缩"""
        # 这里应该实现具体的压缩检查逻辑
        # 默认实现：返回False
        return False
    
    # 抽象方法 - 必须由子类实现
    @abstractmethod
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        pass
    
    @abstractmethod
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        pass
    
    @abstractmethod
    async def _save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现"""
        pass
    
    @abstractmethod
    async def _load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        pass
    
    @abstractmethod
    async def _delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        pass
    
    @abstractmethod
    async def _exists_impl(self, id: str) -> bool:
        """实际存在检查实现"""
        pass
    
    @abstractmethod
    async def _list_impl(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """实际列表实现"""
        pass
    
    @abstractmethod
    async def _query_impl(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """实际查询实现"""
        pass
    
    @abstractmethod
    async def _count_impl(self, filters: Dict[str, Any]) -> int:
        """实际计数实现"""
        pass
    
    @abstractmethod
    async def _batch_save_impl(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """实际批量保存实现"""
        pass
    
    @abstractmethod
    async def _batch_delete_impl(self, ids: List[str]) -> int:
        """实际批量删除实现"""
        pass
    
    @abstractmethod
    def _stream_list_impl(
        self,
        filters: Dict[str, Any],
        batch_size: int
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """实际流式列表实现"""
        pass
    
    @abstractmethod
    async def _health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        pass