"""Thread检查点向后兼容适配器

提供旧接口到新接口的适配，确保平滑迁移。
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .checkpoint import (
    IThreadCheckpointStorage,
    IThreadCheckpointManager,
    IThreadCheckpointSerializer,
    IThreadCheckpointPolicy
)
from src.core.threads.checkpoints.storage.models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointType,
    CheckpointStatistics
)
from ..checkpoint import (
    ICheckpointStore,
    ICheckpointManager,
    ICheckpointSerializer,
    ICheckpointPolicy
)


class LegacyCheckpointStoreAdapter(IThreadCheckpointStorage):
    """旧ICheckpointStore适配器
    
    将旧的ICheckpointStore接口适配到新的IThreadCheckpointStorage接口。
    """
    
    def __init__(self, legacy_store: ICheckpointStore):
        """初始化适配器
        
        Args:
            legacy_store: 旧的检查点存储实例
        """
        self._legacy_store = legacy_store
    
    async def save_checkpoint(self, thread_id: str, checkpoint: ThreadCheckpoint) -> str:
        """保存Thread检查点"""
        # 转换为旧格式
        legacy_data = checkpoint.to_dict()
        return await self._legacy_store.save(legacy_data)
    
    async def load_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """加载Thread检查点"""
        legacy_data = await self._legacy_store.load_by_thread(thread_id, checkpoint_id)
        if legacy_data:
            return ThreadCheckpoint.from_dict(legacy_data)
        return None
    
    async def list_checkpoints(self, thread_id: str, status: Optional[CheckpointStatus] = None) -> List[ThreadCheckpoint]:
        """列出Thread的所有检查点"""
        legacy_list = await self._legacy_store.list_by_thread(thread_id)
        
        # 转换为新格式并过滤状态
        checkpoints = []
        for legacy_data in legacy_list:
            checkpoint = ThreadCheckpoint.from_dict(legacy_data)
            if status is None or checkpoint.status == status:
                checkpoints.append(checkpoint)
        
        return checkpoints
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除Thread检查点"""
        return await self._legacy_store.delete_by_thread(thread_id, checkpoint_id)
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点"""
        legacy_data = await self._legacy_store.get_latest(thread_id)
        if legacy_data:
            return ThreadCheckpoint.from_dict(legacy_data)
        return None
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点"""
        return await self._legacy_store.cleanup_old_checkpoints(thread_id, max_count)
    
    async def get_checkpoint_statistics(self, thread_id: str) -> CheckpointStatistics:
        """获取Thread检查点统计信息"""
        # 获取所有检查点
        checkpoints = await self.list_checkpoints(thread_id)
        
        # 计算统计信息
        stats = CheckpointStatistics()
        stats.total_checkpoints = len(checkpoints)
        
        for checkpoint in checkpoints:
            # 状态统计
            if checkpoint.status == CheckpointStatus.ACTIVE:
                stats.active_checkpoints += 1
            elif checkpoint.status == CheckpointStatus.EXPIRED:
                stats.expired_checkpoints += 1
            elif checkpoint.status == CheckpointStatus.CORRUPTED:
                stats.corrupted_checkpoints += 1
            elif checkpoint.status == CheckpointStatus.ARCHIVED:
                stats.archived_checkpoints += 1
            
            # 大小统计
            stats.total_size_bytes += checkpoint.size_bytes
            if checkpoint.size_bytes > stats.largest_checkpoint_bytes:
                stats.largest_checkpoint_bytes = checkpoint.size_bytes
            if stats.smallest_checkpoint_bytes == 0 or checkpoint.size_bytes < stats.smallest_checkpoint_bytes:
                stats.smallest_checkpoint_bytes = checkpoint.size_bytes
            
            # 恢复统计
            stats.total_restores += checkpoint.restore_count
            
            # 年龄统计
            age_hours = checkpoint.get_age_hours()
            if stats.oldest_checkpoint_age_hours == 0 or age_hours > stats.oldest_checkpoint_age_hours:
                stats.oldest_checkpoint_age_hours = age_hours
            if stats.newest_checkpoint_age_hours == 0 or age_hours < stats.newest_checkpoint_age_hours:
                stats.newest_checkpoint_age_hours = age_hours
        
        # 计算平均值
        if stats.total_checkpoints > 0:
            stats.average_size_bytes = stats.total_size_bytes / stats.total_checkpoints
            stats.average_restores = stats.total_restores / stats.total_checkpoints
            stats.average_age_hours = (stats.oldest_checkpoint_age_hours + stats.newest_checkpoint_age_hours) / 2
        
        return stats


class LegacyCheckpointManagerAdapter(IThreadCheckpointManager):
    """旧ICheckpointManager适配器
    
    将旧的ICheckpointManager接口适配到新的IThreadCheckpointManager接口。
    """
    
    def __init__(self, legacy_manager: ICheckpointManager):
        """初始化适配器
        
        Args:
            legacy_manager: 旧的检查点管理器实例
        """
        self._legacy_manager = legacy_manager
    
    async def create_checkpoint(
        self, 
        thread_id: str, 
        state: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建Thread检查点"""
        # 生成一个workflow_id（旧接口需要）
        workflow_id = f"thread_{thread_id}"
        
        # 转换检查点类型
        if checkpoint_type == CheckpointType.MANUAL:
            metadata = metadata or {}
            metadata["checkpoint_type"] = "manual"
        elif checkpoint_type == CheckpointType.ERROR:
            metadata = metadata or {}
            metadata["checkpoint_type"] = "error"
        elif checkpoint_type == CheckpointType.MILESTONE:
            metadata = metadata or {}
            metadata["checkpoint_type"] = "milestone"
        
        return await self._legacy_manager.create_checkpoint(thread_id, workflow_id, state, metadata)
    
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread检查点"""
        legacy_data = await self._legacy_manager.get_checkpoint(thread_id, checkpoint_id)
        if legacy_data:
            return ThreadCheckpoint.from_dict(legacy_data)
        return None
    
    async def list_checkpoints(self, thread_id: str) -> List[ThreadCheckpoint]:
        """列出Thread的所有检查点"""
        legacy_list = await self._legacy_manager.list_checkpoints(thread_id)
        
        # 转换为新格式
        checkpoints = []
        for legacy_data in legacy_list:
            checkpoint = ThreadCheckpoint.from_dict(legacy_data)
            checkpoints.append(checkpoint)
        
        return checkpoints
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除Thread检查点"""
        return await self._legacy_manager.delete_checkpoint(thread_id, checkpoint_id)
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点"""
        legacy_data = await self._legacy_manager.get_latest_checkpoint(thread_id)
        if legacy_data:
            return ThreadCheckpoint.from_dict(legacy_data)
        return None
    
    async def restore_from_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """从检查点恢复状态"""
        return await self._legacy_manager.restore_from_checkpoint(thread_id, checkpoint_id)
    
    async def auto_save_checkpoint(
        self, 
        thread_id: str, 
        state: Dict[str, Any],
        trigger_reason: str
    ) -> Optional[str]:
        """自动保存检查点"""
        # 生成一个workflow_id（旧接口需要）
        workflow_id = f"thread_{thread_id}"
        
        return await self._legacy_manager.auto_save_checkpoint(thread_id, workflow_id, state, trigger_reason)
    
    async def cleanup_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点"""
        return await self._legacy_manager.cleanup_checkpoints(thread_id, max_count)
    
    async def copy_checkpoint(
        self,
        source_thread_id: str,
        source_checkpoint_id: str,
        target_thread_id: str
    ) -> str:
        """复制检查点到另一个Thread"""
        return await self._legacy_manager.copy_checkpoint(source_thread_id, source_checkpoint_id, target_thread_id)
    
    async def export_checkpoint(self, thread_id: str, checkpoint_id: str) -> Dict[str, Any]:
        """导出检查点数据"""
        return await self._legacy_manager.export_checkpoint(thread_id, checkpoint_id)
    
    async def import_checkpoint(self, thread_id: str, checkpoint_data: Dict[str, Any]) -> str:
        """导入检查点数据"""
        return await self._legacy_manager.import_checkpoint(thread_id, checkpoint_data)


class LegacyCheckpointSerializerAdapter(IThreadCheckpointSerializer):
    """旧ICheckpointSerializer适配器
    
    将旧的ICheckpointSerializer接口适配到新的IThreadCheckpointSerializer接口。
    """
    
    def __init__(self, legacy_serializer: ICheckpointSerializer):
        """初始化适配器
        
        Args:
            legacy_serializer: 旧的检查点序列化器实例
        """
        self._legacy_serializer = legacy_serializer
    
    def serialize_checkpoint(self, checkpoint: ThreadCheckpoint) -> str:
        """序列化检查点到字符串格式"""
        # 转换为字典格式
        checkpoint_dict = checkpoint.to_dict()
        # 使用旧接口的序列化方法
        serialized_dict = self._legacy_serializer.serialize(checkpoint_dict)
        # 转换为JSON字符串
        import json
        return json.dumps(serialized_dict)
    
    def deserialize_checkpoint(self, data: str) -> ThreadCheckpoint:
        """从字符串格式反序列化检查点"""
        import json
        # 从JSON字符串解析
        serialized_dict = json.loads(data)
        # 使用旧接口的反序列化方法
        checkpoint_dict = self._legacy_serializer.deserialize(serialized_dict)
        # 转换为ThreadCheckpoint对象
        return ThreadCheckpoint.from_dict(checkpoint_dict)
    
    def serialize_state(self, state: Dict[str, Any]) -> str:
        """序列化状态到字符串格式"""
        # 使用旧接口的工作流状态序列化
        serialized = self._legacy_serializer.serialize_workflow_state(state)
        # 如果返回的不是字符串，转换为JSON字符串
        if not isinstance(serialized, str):
            import json
            return json.dumps(serialized)
        return serialized
    
    def deserialize_state(self, data: str) -> Dict[str, Any]:
        """从字符串格式反序列化状态"""
        # 使用旧接口的工作流状态反序列化
        state = self._legacy_serializer.deserialize_workflow_state(data)
        # 确保返回字典类型
        if not isinstance(state, dict):
            return {"state": state}
        return state


class LegacyCheckpointPolicyAdapter(IThreadCheckpointPolicy):
    """旧ICheckpointPolicy适配器
    
    将旧的ICheckpointPolicy接口适配到新的IThreadCheckpointPolicy接口。
    """
    
    def __init__(self, legacy_policy: ICheckpointPolicy):
        """初始化适配器
        
        Args:
            legacy_policy: 旧的检查点策略实例
        """
        self._legacy_policy = legacy_policy
    
    def should_save_checkpoint(self, thread_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """判断是否应该保存检查点"""
        # 生成一个workflow_id（旧接口需要）
        workflow_id = context.get("workflow_id", f"thread_{thread_id}")
        return self._legacy_policy.should_save_checkpoint(thread_id, workflow_id, state, context)
    
    def get_checkpoint_metadata(self, thread_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """获取检查点元数据"""
        # 生成一个workflow_id（旧接口需要）
        workflow_id = context.get("workflow_id", f"thread_{thread_id}")
        return self._legacy_policy.get_checkpoint_metadata(thread_id, workflow_id, state, context)
    
    def get_checkpoint_type(self, thread_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> CheckpointType:
        """获取检查点类型"""
        # 从元数据中推断检查点类型
        metadata = self.get_checkpoint_metadata(thread_id, state, context)
        checkpoint_type_str = metadata.get("checkpoint_type", "auto")
        
        try:
            return CheckpointType(checkpoint_type_str)
        except ValueError:
            return CheckpointType.AUTO
    
    def get_expiration_hours(self, thread_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> Optional[int]:
        """获取检查点过期时间（小时）"""
        # 从元数据中获取过期时间
        metadata = self.get_checkpoint_metadata(thread_id, state, context)
        return metadata.get("expiration_hours")


class CheckpointCompatibilityWrapper:
    """Checkpoint兼容性包装器
    
    提供创建兼容适配器的静态方法。
    """
    
    @staticmethod
    def create_legacy_storage_adapter(new_storage: IThreadCheckpointStorage) -> ICheckpointStore:
        """创建兼容的存储适配器
        
        Args:
            new_storage: 新的存储接口
            
        Returns:
            ICheckpointStore: 兼容的旧存储接口
        """
        return NewToLegacyStorageAdapter(new_storage)
    
    @staticmethod
    def create_legacy_manager_adapter(new_manager: IThreadCheckpointManager) -> ICheckpointManager:
        """创建兼容的管理器适配器
        
        Args:
            new_manager: 新的管理器接口
            
        Returns:
            ICheckpointManager: 兼容的旧管理器接口
        """
        return NewToLegacyManagerAdapter(new_manager)
    
    @staticmethod
    def create_legacy_serializer_adapter(new_serializer: IThreadCheckpointSerializer) -> ICheckpointSerializer:
        """创建兼容的序列化器适配器
        
        Args:
            new_serializer: 新的序列化器接口
            
        Returns:
            ICheckpointSerializer: 兼容的旧序列化器接口
        """
        return NewToLegacySerializerAdapter(new_serializer)
    
    @staticmethod
    def create_legacy_policy_adapter(new_policy: IThreadCheckpointPolicy) -> ICheckpointPolicy:
        """创建兼容的策略适配器
        
        Args:
            new_policy: 新的策略接口
            
        Returns:
            ICheckpointPolicy: 兼容的旧策略接口
        """
        return NewToLegacyPolicyAdapter(new_policy)


class NewToLegacyStorageAdapter(ICheckpointStore):
    """新到旧存储适配器"""
    
    def __init__(self, new_storage: IThreadCheckpointStorage):
        self._new_storage = new_storage
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存checkpoint数据"""
        thread_id = data.get("thread_id")
        if not thread_id:
            raise ValueError("数据必须包含thread_id")
        
        checkpoint = ThreadCheckpoint.from_dict(data)
        return await self._new_storage.save_checkpoint(thread_id, checkpoint)
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        checkpoints = await self._new_storage.list_checkpoints(thread_id)
        return [checkpoint.to_dict() for checkpoint in checkpoints]
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint"""
        if checkpoint_id:
            checkpoint = await self._new_storage.load_checkpoint(thread_id, checkpoint_id)
            return checkpoint.to_dict() if checkpoint else None
        else:
            checkpoint = await self._new_storage.get_latest_checkpoint(thread_id)
            return checkpoint.to_dict() if checkpoint else None
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint"""
        if checkpoint_id:
            return await self._new_storage.delete_checkpoint(thread_id, checkpoint_id)
        else:
            # 删除所有检查点
            checkpoints = await self._new_storage.list_checkpoints(thread_id)
            for checkpoint in checkpoints:
                await self._new_storage.delete_checkpoint(thread_id, checkpoint.id)
            return True
    
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        checkpoint = await self._new_storage.get_latest_checkpoint(thread_id)
        return checkpoint.to_dict() if checkpoint else None
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint"""
        return await self._new_storage.cleanup_old_checkpoints(thread_id, max_count)
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        # 新接口中没有workflow概念，返回所有检查点
        return await self.list_by_thread(thread_id)


class NewToLegacyManagerAdapter(ICheckpointManager):
    """新到旧管理器适配器"""
    
    def __init__(self, new_manager: IThreadCheckpointManager):
        self._new_manager = new_manager
    
    async def create_checkpoint(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建checkpoint"""
        # 从元数据中推断检查点类型
        checkpoint_type = CheckpointType.AUTO
        if metadata and "checkpoint_type" in metadata:
            try:
                checkpoint_type = CheckpointType(metadata["checkpoint_type"])
            except ValueError:
                pass
        
        return await self._new_manager.create_checkpoint(thread_id, state, checkpoint_type, metadata)
    
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint"""
        checkpoint = await self._new_manager.get_checkpoint(thread_id, checkpoint_id)
        return checkpoint.to_dict() if checkpoint else None
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        checkpoints = await self._new_manager.list_checkpoints(thread_id)
        return [checkpoint.to_dict() for checkpoint in checkpoints]
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        return await self._new_manager.delete_checkpoint(thread_id, checkpoint_id)
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        checkpoint = await self._new_manager.get_latest_checkpoint(thread_id)
        return checkpoint.to_dict() if checkpoint else None
    
    async def restore_from_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Any]:
        """从checkpoint恢复状态"""
        return await self._new_manager.restore_from_checkpoint(thread_id, checkpoint_id)
    
    async def auto_save_checkpoint(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state: Any,
        trigger_reason: str
    ) -> Optional[str]:
        """自动保存checkpoint"""
        return await self._new_manager.auto_save_checkpoint(thread_id, state, trigger_reason)
    
    async def cleanup_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint"""
        return await self._new_manager.cleanup_checkpoints(thread_id, max_count)
    
    async def copy_checkpoint(
        self,
        source_thread_id: str,
        source_checkpoint_id: str,
        target_thread_id: str
    ) -> str:
        """复制checkpoint到另一个thread"""
        return await self._new_manager.copy_checkpoint(source_thread_id, source_checkpoint_id, target_thread_id)
    
    async def export_checkpoint(self, thread_id: str, checkpoint_id: str) -> Dict[str, Any]:
        """导出checkpoint数据"""
        return await self._new_manager.export_checkpoint(thread_id, checkpoint_id)
    
    async def import_checkpoint(self, thread_id: str, checkpoint_data: Dict[str, Any]) -> str:
        """导入checkpoint数据"""
        return await self._new_manager.import_checkpoint(thread_id, checkpoint_data)


class NewToLegacySerializerAdapter(ICheckpointSerializer):
    """新到旧序列化器适配器"""
    
    def __init__(self, new_serializer: IThreadCheckpointSerializer):
        self._new_serializer = new_serializer
    
    def serialize_workflow_state(self, state: Any) -> str:
        """序列化工作流状态到字符串格式"""
        return self._new_serializer.serialize_state(state)
    
    def deserialize_workflow_state(self, data: str) -> Any:
        """从字符串格式反序列化工作流状态"""
        return self._new_serializer.deserialize_state(data)
    
    def serialize_messages(self, messages: list) -> str:
        """序列化消息列表到字符串格式"""
        import json
        return json.dumps(messages)
    
    def deserialize_messages(self, data: str) -> list:
        """从字符串格式反序列化消息"""
        import json
        return json.loads(data)
    
    def serialize_tool_results(self, tool_results: Dict[str, Any]) -> str:
        """序列化工具结果到字符串格式"""
        import json
        return json.dumps(tool_results)
    
    def deserialize_tool_results(self, data: str) -> Dict[str, Any]:
        """从字符串格式反序列化工具结果"""
        import json
        return json.loads(data)
    
    def serialize(self, state: Any) -> Dict[str, Any]:
        """序列化工作流状态（向后兼容）"""
        serialized_str = self._new_serializer.serialize_state(state)
        import json
        return {"serialized_state": serialized_str}
    
    def deserialize(self, state_data: Dict[str, Any]) -> Any:
        """反序列化工作流状态（向后兼容）"""
        serialized_str = state_data.get("serialized_state", "{}")
        return self._new_serializer.deserialize_state(serialized_str)


class NewToLegacyPolicyAdapter(ICheckpointPolicy):
    """新到旧策略适配器"""
    
    def __init__(self, new_policy: IThreadCheckpointPolicy):
        self._new_policy = new_policy
    
    def should_save_checkpoint(self, thread_id: str, workflow_id: str, 
                              state: Any, context: Dict[str, Any]) -> bool:
        """判断是否应该保存checkpoint"""
        return self._new_policy.should_save_checkpoint(thread_id, state, context)
    
    def get_checkpoint_metadata(self, thread_id: str, workflow_id: str,
                                state: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取checkpoint元数据"""
        metadata = self._new_policy.get_checkpoint_metadata(thread_id, state, context)
        
        # 添加检查点类型信息
        checkpoint_type = self._new_policy.get_checkpoint_type(thread_id, state, context)
        metadata["checkpoint_type"] = checkpoint_type.value
        
        # 添加过期时间信息
        expiration_hours = self._new_policy.get_expiration_hours(thread_id, state, context)
        if expiration_hours:
            metadata["expiration_hours"] = expiration_hours
        
        return metadata