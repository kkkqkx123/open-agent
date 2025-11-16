# Checkpoint模块接口设计

## 概述

Checkpoint模块负责管理工作流执行状态的检查点存储和恢复。基于分析，Checkpoint模块目前过度依赖LangGraph的checkpoint机制，需要完全移除LangGraph依赖，实现独立的存储功能。

## 现有接口分析

### 当前接口 (ICheckpointStore)

```python
class ICheckpointStore(ABC):
    """Checkpoint存储接口"""
    
    @abstractmethod
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        pass
    
    @abstractmethod
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        pass
    
    @abstractmethod
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint"""
        pass
    
    @abstractmethod
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint"""
        pass
    
    @abstractmethod
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        pass
    
    @abstractmethod
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        pass
```

### 问题分析

1. **LangGraph依赖**：当前实现完全依赖LangGraph的checkpoint机制
2. **数据格式限制**：受LangGraph的数据格式限制，不够灵活
3. **序列化问题**：LangGraph的序列化机制与通用需求不匹配
4. **功能限制**：缺少版本管理、压缩、加密等功能

## 新接口设计

### 独立的Checkpoint存储接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, BinaryIO
from datetime import datetime
from enum import Enum

class CheckpointStatus(str, Enum):
    """Checkpoint状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CORRUPTED = "corrupted"
    DELETED = "deleted"

class CompressionType(str, Enum):
    """压缩类型枚举"""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"

class ICheckpointStore(ABC):
    """独立的Checkpoint存储接口"""
    
    # 基本CRUD操作
    @abstractmethod
    async def save(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state_data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        compression: CompressionType = CompressionType.NONE
    ) -> str:
        """保存checkpoint
        
        Args:
            thread_id: 线程ID
            workflow_id: 工作流ID
            state_data: 状态数据
            metadata: 元数据
            compression: 压缩类型
            
        Returns:
            checkpoint ID
        """
        pass
    
    @abstractmethod
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            checkpoint数据
        """
        pass
    
    @abstractmethod
    async def load_by_thread(
        self, 
        thread_id: str, 
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 可选的checkpoint ID，None表示最新
            
        Returns:
            checkpoint数据
        """
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def delete_by_thread(
        self, 
        thread_id: str, 
        checkpoint_id: Optional[str] = None
    ) -> bool:
        """根据thread ID删除checkpoint
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 可选的checkpoint ID，None表示删除所有
            
        Returns:
            是否删除成功
        """
        pass
    
    # 查询操作
    @abstractmethod
    async def list_by_thread(
        self, 
        thread_id: str, 
        limit: Optional[int] = None,
        status: Optional[CheckpointStatus] = None
    ) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: 线程ID
            limit: 限制数量
            status: 状态过滤
            
        Returns:
            checkpoint列表
        """
        pass
    
    @abstractmethod
    async def list_by_workflow(
        self, 
        thread_id: str, 
        workflow_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint
        
        Args:
            thread_id: 线程ID
            workflow_id: 工作流ID
            limit: 限制数量
            
        Returns:
            checkpoint列表
        """
        pass
    
    @abstractmethod
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最新的checkpoint数据
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_info(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint信息（不包含状态数据）
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            checkpoint信息
        """
        pass
    
    # 版本管理
    @abstractmethod
    async def create_version(
        self, 
        checkpoint_id: str, 
        version_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建checkpoint版本
        
        Args:
            checkpoint_id: checkpoint ID
            version_name: 版本名称
            description: 版本描述
            
        Returns:
            版本ID
        """
        pass
    
    @abstractmethod
    async def list_versions(self, checkpoint_id: str) -> List[Dict[str, Any]]:
        """列出checkpoint的所有版本
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            版本列表
        """
        pass
    
    @abstractmethod
    async def load_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """加载指定版本的checkpoint
        
        Args:
            version_id: 版本ID
            
        Returns:
            checkpoint数据
        """
        pass
    
    # 批量操作
    @abstractmethod
    async def batch_save(
        self, 
        checkpoints: List[Dict[str, Any]]
    ) -> List[str]:
        """批量保存checkpoint
        
        Args:
            checkpoints: checkpoint数据列表
            
        Returns:
            checkpoint ID列表
        """
        pass
    
    @abstractmethod
    async def batch_delete(self, checkpoint_ids: List[str]) -> int:
        """批量删除checkpoint
        
        Args:
            checkpoint_ids: checkpoint ID列表
            
        Returns:
            删除数量
        """
        pass
    
    # 维护操作
    @abstractmethod
    async def cleanup_old_checkpoints(
        self, 
        thread_id: str, 
        max_count: int,
        keep_latest: bool = True
    ) -> int:
        """清理旧的checkpoint
        
        Args:
            thread_id: 线程ID
            max_count: 保留的最大数量
            keep_latest: 是否保留最新的
            
        Returns:
            删除数量
        """
        pass
    
    @abstractmethod
    async def archive_checkpoints(
        self, 
        thread_id: str,
        before_date: datetime
    ) -> int:
        """归档checkpoint
        
        Args:
            thread_id: 线程ID
            before_date: 归档此日期之前的checkpoint
            
        Returns:
            归档数量
        """
        pass
    
    @abstractmethod
    async def validate_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """验证checkpoint完整性
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    async def repair_checkpoint(self, checkpoint_id: str) -> bool:
        """修复损坏的checkpoint
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            是否修复成功
        """
        pass
    
    # 导入导出
    @abstractmethod
    async def export_checkpoint(
        self, 
        checkpoint_id: str,
        format: str = "json"
    ) -> Union[str, bytes]:
        """导出checkpoint
        
        Args:
            checkpoint_id: checkpoint ID
            format: 导出格式 (json, binary, pickle)
            
        Returns:
            导出数据
        """
        pass
    
    @abstractmethod
    async def import_checkpoint(
        self, 
        data: Union[str, bytes],
        format: str = "json",
        thread_id: Optional[str] = None
    ) -> str:
        """导入checkpoint
        
        Args:
            data: 导入数据
            format: 导入格式
            thread_id: 可选的线程ID
            
        Returns:
            checkpoint ID
        """
        pass
    
    # 统计和监控
    @abstractmethod
    async def get_storage_statistics(self, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """获取存储统计信息
        
        Args:
            thread_id: 可选的线程ID
            
        Returns:
            统计信息
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_history(
        self, 
        checkpoint_id: str
    ) -> List[Dict[str, Any]]:
        """获取checkpoint历史记录
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            历史记录列表
        """
        pass
```

### 基于统一存储的实现

```python
from typing import Dict, Any, Optional, List, Union, BinaryIO
from datetime import datetime
import uuid
import gzip
import pickle
import json
from ...domain.storage.interfaces import IUnifiedStorage
from ...domain.storage.exceptions import StorageError, StorageNotFoundError
from ...common.serialization.serializer import Serializer

class CheckpointStore(ICheckpointStore):
    """独立的Checkpoint存储实现"""
    
    def __init__(self, storage: IUnifiedStorage, serializer: Optional[Serializer] = None):
        self._storage = storage
        self._serializer = serializer or Serializer()
    
    # 基本CRUD操作实现
    async def save(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state_data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        compression: CompressionType = CompressionType.NONE
    ) -> str:
        """保存checkpoint"""
        try:
            checkpoint_id = str(uuid.uuid4())
            now = datetime.now()
            
            # 序列化状态数据
            serialized_state = self._serialize_state(state_data, compression)
            
            # 压缩数据
            if compression != CompressionType.NONE:
                serialized_state = self._compress_data(serialized_state, compression)
            
            # 构建存储数据
            data = {
                "id": checkpoint_id,
                "type": "checkpoint",
                "thread_id": thread_id,
                "workflow_id": workflow_id,
                "state_data": serialized_state,
                "compression": compression.value,
                "status": CheckpointStatus.ACTIVE.value,
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now
            }
            
            await self._storage.save(data)
            return checkpoint_id
        except Exception as e:
            raise StorageError(f"Failed to save checkpoint: {e}")
    
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint"""
        try:
            data = await self._storage.load(checkpoint_id)
            if not data or data.get("type") != "checkpoint":
                return None
            
            # 检查状态
            if data.get("status") == CheckpointStatus.DELETED.value:
                return None
            
            # 解压缩数据
            compression = CompressionType(data.get("compression", CompressionType.NONE.value))
            serialized_state = data.get("state_data")
            
            if compression != CompressionType.NONE:
                serialized_state = self._decompress_data(serialized_state, compression)
            
            # 反序列化状态数据
            state_data = self._deserialize_state(serialized_state)
            
            return {
                "id": data["id"],
                "thread_id": data["thread_id"],
                "workflow_id": data["workflow_id"],
                "state_data": state_data,
                "compression": compression.value,
                "status": data["status"],
                "metadata": data.get("metadata", {}),
                "created_at": data["created_at"],
                "updated_at": data["updated_at"]
            }
        except Exception as e:
            raise StorageError(f"Failed to load checkpoint {checkpoint_id}: {e}")
    
    async def load_by_thread(
        self, 
        thread_id: str, 
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint"""
        if checkpoint_id:
            return await self.load(checkpoint_id)
        else:
            # 获取最新的checkpoint
            latest = await self.get_latest(thread_id)
            if latest:
                return await self.load(latest["id"])
            return None
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        try:
            # 软删除：标记为已删除
            await self._storage.update(checkpoint_id, {
                "status": CheckpointStatus.DELETED.value,
                "updated_at": datetime.now()
            })
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete checkpoint {checkpoint_id}: {e}")
    
    async def delete_by_thread(
        self, 
        thread_id: str, 
        checkpoint_id: Optional[str] = None
    ) -> bool:
        """根据thread ID删除checkpoint"""
        try:
            if checkpoint_id:
                return await self.delete(checkpoint_id)
            else:
                # 删除thread的所有checkpoint
                checkpoints = await self.list_by_thread(thread_id)
                for checkpoint in checkpoints:
                    await self.delete(checkpoint["id"])
                return True
        except Exception as e:
            raise StorageError(f"Failed to delete checkpoints for thread {thread_id}: {e}")
    
    # 查询操作实现
    async def list_by_thread(
        self, 
        thread_id: str, 
        limit: Optional[int] = None,
        status: Optional[CheckpointStatus] = None
    ) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        try:
            filters = {
                "type": "checkpoint",
                "thread_id": thread_id
            }
            
            if status:
                filters["status"] = status.value
            
            results = await self._storage.list(filters, limit)
            
            # 按创建时间倒序排列
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # 返回基本信息（不包含状态数据）
            return [
                {
                    "id": result["id"],
                    "thread_id": result["thread_id"],
                    "workflow_id": result["workflow_id"],
                    "compression": result.get("compression", CompressionType.NONE.value),
                    "status": result.get("status", CheckpointStatus.ACTIVE.value),
                    "metadata": result.get("metadata", {}),
                    "created_at": result["created_at"],
                    "updated_at": result["updated_at"]
                }
                for result in results
            ]
        except Exception as e:
            raise StorageError(f"Failed to list checkpoints for thread {thread_id}: {e}")
    
    async def list_by_workflow(
        self, 
        thread_id: str, 
        workflow_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        try:
            filters = {
                "type": "checkpoint",
                "thread_id": thread_id,
                "workflow_id": workflow_id
            }
            
            results = await self._storage.list(filters, limit)
            
            # 按创建时间倒序排列
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return [
                {
                    "id": result["id"],
                    "thread_id": result["thread_id"],
                    "workflow_id": result["workflow_id"],
                    "compression": result.get("compression", CompressionType.NONE.value),
                    "status": result.get("status", CheckpointStatus.ACTIVE.value),
                    "metadata": result.get("metadata", {}),
                    "created_at": result["created_at"],
                    "updated_at": result["updated_at"]
                }
                for result in results
            ]
        except Exception as e:
            raise StorageError(f"Failed to list checkpoints for workflow {workflow_id}: {e}")
    
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        try:
            checkpoints = await self.list_by_thread(thread_id, limit=1)
            return checkpoints[0] if checkpoints else None
        except Exception as e:
            raise StorageError(f"Failed to get latest checkpoint for thread {thread_id}: {e}")
    
    async def get_checkpoint_info(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint信息（不包含状态数据）"""
        try:
            data = await self._storage.load(checkpoint_id)
            if not data or data.get("type") != "checkpoint":
                return None
            
            return {
                "id": data["id"],
                "thread_id": data["thread_id"],
                "workflow_id": data["workflow_id"],
                "compression": data.get("compression", CompressionType.NONE.value),
                "status": data.get("status", CheckpointStatus.ACTIVE.value),
                "metadata": data.get("metadata", {}),
                "created_at": data["created_at"],
                "updated_at": data["updated_at"]
            }
        except Exception:
            return None
    
    # 版本管理实现
    async def create_version(
        self, 
        checkpoint_id: str, 
        version_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建checkpoint版本"""
        try:
            # 加载原始checkpoint
            original = await self.load(checkpoint_id)
            if not original:
                raise StorageNotFoundError(f"Checkpoint not found: {checkpoint_id}")
            
            # 创建版本
            version_id = str(uuid.uuid4())
            now = datetime.now()
            
            version_data = {
                "id": version_id,
                "type": "checkpoint_version",
                "checkpoint_id": checkpoint_id,
                "version_name": version_name,
                "description": description,
                "state_data": original["state_data"],
                "compression": original["compression"],
                "created_at": now
            }
            
            await self._storage.save(version_data)
            return version_id
        except Exception as e:
            raise StorageError(f"Failed to create version for checkpoint {checkpoint_id}: {e}")
    
    async def list_versions(self, checkpoint_id: str) -> List[Dict[str, Any]]:
        """列出checkpoint的所有版本"""
        try:
            filters = {
                "type": "checkpoint_version",
                "checkpoint_id": checkpoint_id
            }
            
            results = await self._storage.list(filters)
            
            # 按创建时间倒序排列
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return [
                {
                    "id": result["id"],
                    "checkpoint_id": result["checkpoint_id"],
                    "version_name": result["version_name"],
                    "description": result.get("description"),
                    "compression": result.get("compression"),
                    "created_at": result["created_at"]
                }
                for result in results
            ]
        except Exception as e:
            raise StorageError(f"Failed to list versions for checkpoint {checkpoint_id}: {e}")
    
    async def load_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """加载指定版本的checkpoint"""
        try:
            data = await self._storage.load(version_id)
            if not data or data.get("type") != "checkpoint_version":
                return None
            
            # 解压缩数据
            compression = CompressionType(data.get("compression", CompressionType.NONE.value))
            serialized_state = data.get("state_data")
            
            if compression != CompressionType.NONE:
                serialized_state = self._decompress_data(serialized_state, compression)
            
            # 反序列化状态数据
            state_data = self._deserialize_state(serialized_state)
            
            return {
                "id": data["id"],
                "checkpoint_id": data["checkpoint_id"],
                "version_name": data["version_name"],
                "description": data.get("description"),
                "state_data": state_data,
                "compression": compression.value,
                "created_at": data["created_at"]
            }
        except Exception as e:
            raise StorageError(f"Failed to load version {version_id}: {e}")
    
    # 批量操作实现
    async def batch_save(
        self, 
        checkpoints: List[Dict[str, Any]]
    ) -> List[str]:
        """批量保存checkpoint"""
        try:
            operations = []
            checkpoint_ids = []
            
            for checkpoint in checkpoints:
                checkpoint_id = str(uuid.uuid4())
                checkpoint_ids.append(checkpoint_id)
                
                now = datetime.now()
                
                # 序列化状态数据
                compression = CompressionType(checkpoint.get("compression", CompressionType.NONE.value))
                serialized_state = self._serialize_state(checkpoint["state_data"], compression)
                
                # 压缩数据
                if compression != CompressionType.NONE:
                    serialized_state = self._compress_data(serialized_state, compression)
                
                data = {
                    "id": checkpoint_id,
                    "type": "checkpoint",
                    "thread_id": checkpoint["thread_id"],
                    "workflow_id": checkpoint["workflow_id"],
                    "state_data": serialized_state,
                    "compression": compression.value,
                    "status": CheckpointStatus.ACTIVE.value,
                    "metadata": checkpoint.get("metadata", {}),
                    "created_at": now,
                    "updated_at": now
                }
                
                operations.append({"type": "save", "data": data})
            
            await self._storage.transaction(operations)
            return checkpoint_ids
        except Exception as e:
            raise StorageError(f"Failed to batch save checkpoints: {e}")
    
    async def batch_delete(self, checkpoint_ids: List[str]) -> int:
        """批量删除checkpoint"""
        try:
            operations = []
            
            for checkpoint_id in checkpoint_ids:
                operations.append({
                    "type": "update",
                    "id": checkpoint_id,
                    "data": {
                        "status": CheckpointStatus.DELETED.value,
                        "updated_at": datetime.now()
                    }
                })
            
            await self._storage.transaction(operations)
            return len(checkpoint_ids)
        except Exception as e:
            raise StorageError(f"Failed to batch delete checkpoints: {e}")
    
    # 维护操作实现
    async def cleanup_old_checkpoints(
        self, 
        thread_id: str, 
        max_count: int,
        keep_latest: bool = True
    ) -> int:
        """清理旧的checkpoint"""
        try:
            checkpoints = await self.list_by_thread(thread_id)
            
            if len(checkpoints) <= max_count:
                return 0
            
            # 保留最新的checkpoint
            if keep_latest:
                checkpoints_to_keep = checkpoints[:max_count]
                checkpoints_to_delete = checkpoints[max_count:]
            else:
                checkpoints_to_delete = checkpoints[max_count:]
            
            # 批量删除
            checkpoint_ids = [cp["id"] for cp in checkpoints_to_delete]
            await self.batch_delete(checkpoint_ids)
            
            return len(checkpoint_ids)
        except Exception as e:
            raise StorageError(f"Failed to cleanup old checkpoints for thread {thread_id}: {e}")
    
    async def archive_checkpoints(
        self, 
        thread_id: str,
        before_date: datetime
    ) -> int:
        """归档checkpoint"""
        try:
            filters = {
                "type": "checkpoint",
                "thread_id": thread_id,
                "created_at": {"$lt": before_date}
            }
            
            results = await self._storage.list(filters)
            
            # 批量归档
            operations = []
            for result in results:
                operations.append({
                    "type": "update",
                    "id": result["id"],
                    "data": {
                        "status": CheckpointStatus.ARCHIVED.value,
                        "updated_at": datetime.now()
                    }
                })
            
            if operations:
                await self._storage.transaction(operations)
            
            return len(results)
        except Exception as e:
            raise StorageError(f"Failed to archive checkpoints for thread {thread_id}: {e}")
    
    async def validate_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """验证checkpoint完整性"""
        try:
            info = await self.get_checkpoint_info(checkpoint_id)
            if not info:
                return {"valid": False, "error": "Checkpoint not found"}
            
            # 尝试加载checkpoint
            try:
                checkpoint = await self.load(checkpoint_id)
                if not checkpoint:
                    return {"valid": False, "error": "Failed to load checkpoint"}
                
                return {
                    "valid": True,
                    "size": len(str(checkpoint["state_data"])),
                    "compression": checkpoint["compression"],
                    "status": checkpoint["status"]
                }
            except Exception as e:
                return {"valid": False, "error": str(e)}
        except Exception as e:
            raise StorageError(f"Failed to validate checkpoint {checkpoint_id}: {e}")
    
    async def repair_checkpoint(self, checkpoint_id: str) -> bool:
        """修复损坏的checkpoint"""
        try:
            # 标记为已损坏
            await self._storage.update(checkpoint_id, {
                "status": CheckpointStatus.CORRUPTED.value,
                "updated_at": datetime.now()
            })
            
            # TODO: 实现修复逻辑
            # 可以尝试从版本中恢复
            return False
        except Exception as e:
            raise StorageError(f"Failed to repair checkpoint {checkpoint_id}: {e}")
    
    # 导入导出实现
    async def export_checkpoint(
        self, 
        checkpoint_id: str,
        format: str = "json"
    ) -> Union[str, bytes]:
        """导出checkpoint"""
        try:
            checkpoint = await self.load(checkpoint_id)
            if not checkpoint:
                raise StorageNotFoundError(f"Checkpoint not found: {checkpoint_id}")
            
            if format == "json":
                return json.dumps(checkpoint, indent=2, default=str)
            elif format == "binary":
                return pickle.dumps(checkpoint)
            elif format == "pickle":
                return pickle.dumps(checkpoint)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            raise StorageError(f"Failed to export checkpoint {checkpoint_id}: {e}")
    
    async def import_checkpoint(
        self, 
        data: Union[str, bytes],
        format: str = "json",
        thread_id: Optional[str] = None
    ) -> str:
        """导入checkpoint"""
        try:
            if format == "json":
                checkpoint = json.loads(data)
            elif format == "binary" or format == "pickle":
                checkpoint = pickle.loads(data)
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            # 使用导入的数据或覆盖thread_id
            if thread_id:
                checkpoint["thread_id"] = thread_id
            
            return await self.save(
                checkpoint["thread_id"],
                checkpoint["workflow_id"],
                checkpoint["state_data"],
                checkpoint.get("metadata")
            )
        except Exception as e:
            raise StorageError(f"Failed to import checkpoint: {e}")
    
    # 统计和监控实现
    async def get_storage_statistics(self, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            filters = {"type": "checkpoint"}
            if thread_id:
                filters["thread_id"] = thread_id
            
            results = await self._storage.list(filters)
            
            total_count = len(results)
            total_size = 0
            status_counts = {}
            compression_counts = {}
            
            for result in results:
                # 估算大小
                size = len(str(result.get("state_data", "")))
                total_size += size
                
                # 状态统计
                status = result.get("status", CheckpointStatus.ACTIVE.value)
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # 压缩统计
                compression = result.get("compression", CompressionType.NONE.value)
                compression_counts[compression] = compression_counts.get(compression, 0) + 1
            
            return {
                "total_checkpoints": total_count,
                "total_size": total_size,
                "average_size": total_size / total_count if total_count > 0 else 0,
                "status_distribution": status_counts,
                "compression_distribution": compression_counts
            }
        except Exception as e:
            raise StorageError(f"Failed to get storage statistics: {e}")
    
    async def get_checkpoint_history(
        self, 
        checkpoint_id: str
    ) -> List[Dict[str, Any]]:
        """获取checkpoint历史记录"""
        try:
            # TODO: 实现历史记录功能
            # 可以记录checkpoint的修改历史
            return []
        except Exception as e:
            raise StorageError(f"Failed to get checkpoint history: {e}")
    
    # 辅助方法
    def _serialize_state(self, state_data: Any, compression: CompressionType) -> Union[str, bytes]:
        """序列化状态数据"""
        try:
            if compression == CompressionType.NONE:
                return self._serializer.serialize(state_data)
            else:
                # 对于压缩数据，使用pickle序列化
                return pickle.dumps(state_data)
        except Exception as e:
            raise StorageError(f"Failed to serialize state: {e}")
    
    def _deserialize_state(self, serialized_state: Union[str, bytes]) -> Any:
        """反序列化状态数据"""
        try:
            if isinstance(serialized_state, str):
                return self._serializer.deserialize(serialized_state)
            else:
                return pickle.loads(serialized_state)
        except Exception as e:
            raise StorageError(f"Failed to deserialize state: {e}")
    
    def _compress_data(self, data: Union[str, bytes], compression: CompressionType) -> bytes:
        """压缩数据"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            if compression == CompressionType.GZIP:
                return gzip.compress(data)
            elif compression == CompressionType.LZ4:
                import lz4.frame
                return lz4.frame.compress(data)
            elif compression == CompressionType.ZSTD:
                import zstandard as zstd
                compressor = zstd.ZstdCompressor()
                return compressor.compress(data)
            else:
                return data
        except Exception as e:
            raise StorageError(f"Failed to compress data: {e}")
    
    def _decompress_data(self, data: bytes, compression: CompressionType) -> Union[str, bytes]:
        """解压缩数据"""
        try:
            if compression == CompressionType.GZIP:
                return gzip.decompress(data)
            elif compression == CompressionType.LZ4:
                import lz4.frame
                return lz4.frame.decompress(data)
            elif compression == CompressionType.ZSTD:
                import zstandard as zstd
                decompressor = zstd.ZstdDecompressor()
                return decompressor.decompress(data)
            else:
                return data
        except Exception as e:
            raise StorageError(f"Failed to decompress data: {e}")
```

## 数据模型

### Checkpoint数据模型

```python
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class CheckpointMetadata(BaseModel):
    """Checkpoint元数据"""
    checkpoint_id: str
    thread_id: str
    workflow_id: str
    status: str = "active"
    compression: str = "none"
    size: Optional[int] = None
    checksum: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

class CheckpointVersion(BaseModel):
    """Checkpoint版本"""
    version_id: str
    checkpoint_id: str
    version_name: str
    description: Optional[str] = None
    created_at: datetime
```

## 迁移策略

### 从LangGraph迁移

1. **数据格式转换**：将LangGraph的checkpoint格式转换为新的格式
2. **状态序列化**：使用自定义序列化器替代LangGraph的序列化
3. **功能映射**：将LangGraph的功能映射到新接口

```python
# 迁移工具
class LangGraphMigrationTool:
    """LangGraph迁移工具"""
    
    def __init__(self, old_store, new_store: CheckpointStore):
        self.old_store = old_store
        self.new_store = new_store
    
    async def migrate_thread(self, thread_id: str) -> int:
        """迁移thread的所有checkpoint"""
        # 获取旧checkpoint
        old_checkpoints = await self.old_store.list_by_thread(thread_id)
        
        count = 0
        for old_cp in old_checkpoints:
            # 转换格式
            new_checkpoint = self._convert_checkpoint(old_cp)
            
            # 保存到新存储
            await self.new_store.save(
                new_checkpoint["thread_id"],
                new_checkpoint["workflow_id"],
                new_checkpoint["state_data"],
                new_checkpoint.get("metadata")
            )
            count += 1
        
        return count
    
    def _convert_checkpoint(self, old_checkpoint: Dict[str, Any]) -> Dict[str, Any]:
        """转换checkpoint格式"""
        # 提取状态数据
        state_data = old_checkpoint.get("state_data", {})
        
        # 转换元数据
        metadata = old_checkpoint.get("metadata", {})
        
        return {
            "thread_id": old_checkpoint["thread_id"],
            "workflow_id": old_checkpoint.get("workflow_id", "unknown"),
            "state_data": state_data,
            "metadata": metadata
        }
```

## 性能优化

### 存储优化

1. **压缩策略**：
   - 对大型状态数据使用压缩
   - 支持多种压缩算法
   - 根据数据特征选择最佳压缩方式

2. **索引策略**：
   - 按thread_id索引
   - 按workflow_id索引
   - 按创建时间索引
   - 按状态索引

3. **分区策略**：
   - 按thread_id分区
   - 按时间分区

### 查询优化

1. **缓存策略**：
   - 缓存最新的checkpoint
   - 缓存checkpoint元数据
   - 缓存版本信息

2. **预加载**：
   - 预加载相关checkpoint
   - 预加载版本数据

## 评估结论

### 可行性评估

1. **技术可行性**：高
   - 完全独立于LangGraph，灵活性高
   - 支持多种压缩和序列化方式
   - 提供了完整的版本管理功能

2. **迁移风险**：中
   - 需要完全重写现有实现
   - 需要处理数据格式转换
   - 需要保证功能兼容性

3. **性能影响**：中
   - 自定义实现可能比LangGraph慢
   - 但压缩和优化可以提高性能
   - 更好的控制能力

### 推荐方案

**推荐使用独立的Checkpoint存储接口**

理由：
1. 完全摆脱LangGraph的限制
2. 提供了更丰富的功能
3. 更好的性能优化空间
4. 更灵活的数据格式支持

### 实现优先级

1. **高优先级**：
   - 基本CRUD操作
   - 状态序列化/反序列化
   - 压缩支持

2. **中优先级**：
   - 版本管理
   - 批量操作
   - 维护操作

3. **低优先级**：
   - 导入导出功能
   - 高级压缩算法
   - 监控和统计