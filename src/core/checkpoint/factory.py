"""
检查点工厂

提供检查点对象的创建和构建功能。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .models import Checkpoint, CheckpointMetadata, CheckpointTuple


class CheckpointFactory:
    """检查点工厂类
    
    负责创建和构建各种检查点相关对象。
    """
    
    @staticmethod
    def create_checkpoint(
        id: Optional[str] = None,
        channel_values: Optional[Dict[str, Any]] = None,
        channel_versions: Optional[Dict[str, Any]] = None,
        versions_seen: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Checkpoint:
        """创建检查点
        
        Args:
            id: 检查点ID
            channel_values: 通道值映射
            channel_versions: 通道版本映射
            versions_seen: 每个节点看到的通道版本映射
            **kwargs: 其他字段
            
        Returns:
            检查点实例
        """
        return Checkpoint(
            id=id,
            channel_values=channel_values,
            channel_versions=channel_versions,
            versions_seen=versions_seen,
            **kwargs
        )
    
    @staticmethod
    def create_metadata(
        source: Optional[str] = None,
        step: Optional[int] = None,
        parents: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> CheckpointMetadata:
        """创建检查点元数据
        
        Args:
            source: 检查点来源
            step: 检查点步数
            parents: 父检查点ID映射
            **kwargs: 其他元数据字段
            
        Returns:
            检查点元数据实例
        """
        metadata_data = {}
        
        if source is not None:
            metadata_data["source"] = source
        if step is not None:
            metadata_data["step"] = step
        if parents is not None:
            metadata_data["parents"] = parents
        
        metadata_data.update(kwargs)
        
        return CheckpointMetadata(**metadata_data)
    
    @staticmethod
    def create_tuple(
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        parent_config: Optional[Dict[str, Any]] = None,
        pending_writes: Optional[List[Any]] = None
    ) -> CheckpointTuple:
        """创建检查点元组
        
        Args:
            config: 可运行配置
            checkpoint: 检查点数据
            metadata: 检查点元数据
            parent_config: 父配置
            pending_writes: 待写入数据
            
        Returns:
            检查点元组实例
        """
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=pending_writes
        )
    
    @staticmethod
    def create_from_state(
        state: Dict[str, Any],
        config: Dict[str, Any],
        source: Optional[str] = None,
        step: Optional[int] = None
    ) -> CheckpointTuple:
        """从状态创建检查点元组
        
        Args:
            state: 状态数据
            config: 可运行配置
            source: 检查点来源
            step: 检查点步数
            
        Returns:
            检查点元组实例
        """
        # 创建检查点
        checkpoint = CheckpointFactory.create_checkpoint(
            channel_values=state.get("channel_values", {}),
            channel_versions=state.get("channel_versions", {}),
            versions_seen=state.get("versions_seen", {})
        )
        
        # 创建元数据
        metadata = CheckpointFactory.create_metadata(
            source=source,
            step=step,
            created_at=datetime.now()
        )
        
        # 创建元组
        return CheckpointFactory.create_tuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata
        )
    
    @staticmethod
    def create_config(
        thread_id: str,
        checkpoint_ns: str = "",
        checkpoint_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建检查点配置
        
        Args:
            thread_id: 线程ID
            checkpoint_ns: 检查点命名空间
            checkpoint_id: 检查点ID
            **kwargs: 其他配置字段
            
        Returns:
            配置字典
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns
            }
        }
        
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        
        # 添加其他配置
        if kwargs:
            config["configurable"].update(kwargs)
        
        return config
    
    @staticmethod
    def create_child_config(
        parent_config: Dict[str, Any],
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """创建子检查点配置
        
        Args:
            parent_config: 父配置
            checkpoint_id: 新的检查点ID
            
        Returns:
            子配置字典
        """
        child_config = parent_config.copy()
        child_config["configurable"] = child_config["configurable"].copy()
        child_config["configurable"]["checkpoint_id"] = checkpoint_id
        
        return child_config
    
    @staticmethod
    def extract_checkpoint_id(config: Dict[str, Any]) -> str:
        """从配置中提取检查点ID
        
        Args:
            config: 配置字典
            
        Returns:
            检查点ID
        """
        return config.get("configurable", {}).get("checkpoint_id", "")
    
    @staticmethod
    def extract_thread_id(config: Dict[str, Any]) -> str:
        """从配置中提取线程ID
        
        Args:
            config: 配置字典
            
        Returns:
            线程ID
        """
        return config.get("configurable", {}).get("thread_id", "")
    
    @staticmethod
    def extract_checkpoint_ns(config: Dict[str, Any]) -> str:
        """从配置中提取检查点命名空间
        
        Args:
            config: 配置字典
            
        Returns:
            检查点命名空间
        """
        return config.get("configurable", {}).get("checkpoint_ns", "")