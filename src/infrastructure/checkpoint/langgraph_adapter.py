"""LangGraph适配器实现

将LangGraph的checkpoint接口适配到项目的接口。
注意：由于LangGraph checkpoint机制与工作流schema绑定，
我们采用一种特殊方法来存储任意状态。
"""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, cast

from langgraph.checkpoint.base import Checkpoint, CheckpointTuple
from langchain_core.runnables.config import RunnableConfig

from ...domain.checkpoint.interfaces import ICheckpointSerializer
from ..common.serialization.serializer import Serializer
from ..common.temporal.temporal_manager import TemporalManager
from ..common.metadata.metadata_manager import MetadataManager
from .types import CheckpointNotFoundError, CheckpointStorageError

logger = logging.getLogger(__name__)


class ILangGraphAdapter(ABC):
    """LangGraph适配器接口"""
    
    @abstractmethod
    def create_config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> RunnableConfig:
        """创建LangGraph标准配置
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            RunnableConfig: LangGraph配置
        """
        pass
    
    @abstractmethod
    def create_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Checkpoint:
        """创建LangGraph标准checkpoint
        
        Args:
            state: 工作流状态
            workflow_id: 工作流ID
            metadata: 元数据
            
        Returns:
            Checkpoint: LangGraph checkpoint
        """
        pass
    
    @abstractmethod
    def extract_state(self, checkpoint: Any, metadata: Optional[Any] = None) -> Any:
        """从LangGraph checkpoint提取状态
        
        Args:
            checkpoint: LangGraph checkpoint
            metadata: 可选的元数据
            
        Returns:
            Any: 提取的状态
        """
        pass


class LangGraphAdapter(ILangGraphAdapter):
    """LangGraph适配器实现"""
    
    def __init__(
        self,
        serializer: Optional[ICheckpointSerializer] = None,
        universal_serializer: Optional[Serializer] = None
    ):
        """初始化适配器
        
        Args:
            serializer: 状态序列化器
            universal_serializer: 通用序列化器
        """
        self.serializer = serializer
        self.universal_serializer = universal_serializer or Serializer()
        
        # 公用组件
        self.temporal = TemporalManager()
        self.metadata = MetadataManager()
    
    def create_config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> RunnableConfig:
        """创建LangGraph标准配置"""
        config: RunnableConfig = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        return config
    
    def create_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Checkpoint:
        """创建LangGraph标准checkpoint"""
        # 序列化整个状态
        try:
            serialized_state = self.universal_serializer.serialize(state, "compact_json")
        except Exception as e:
            logger.error(f"状态序列化失败: {e}")
            raise CheckpointStorageError(f"状态序列化失败: {e}")
        
        # 创建一个最小化的LangGraph兼容checkpoint结构
        # 由于我们无法控制工作流schema，我们将使用LangGraph内置的通道
        # 实际上，对于通用checkpoint存储，我们需要使用LangGraph支持的通用通道
        timestamp_iso = self.temporal.format_timestamp(self.temporal.now(), "iso")
        
        # 为了解决LangGraph过滤通道的问题，我们创建一个与LangGraph内部机制兼容的结构
        # 这里我们使用一个通用的方法，将整个序列化状态作为特殊格式存储
        checkpoint: Checkpoint = {
            "v": 4,
            "ts": timestamp_iso,
            "id": str(uuid.uuid4()),
            # 关键：使用LangGraph通常会保留的通道名
            "channel_values": {
                # 使用一个在多数工作流中都会存在的通道名
                "__root__": serialized_state,  # 使用特殊通道名存储序列化状态
                "workflow_id": workflow_id
            },
            "channel_versions": {
                "__root__": 1,
                "workflow_id": 1
            },
            "versions_seen": {
                "__root__": {"__start__": 1},
                "workflow_id": {"__start__": 1}
            },
            "updated_channels": ["__root__", "workflow_id"]
        }
        
        return checkpoint
    
    def extract_state(self, checkpoint: Any, metadata: Optional[Any] = None) -> Any:
        """从LangGraph checkpoint提取状态"""
        if not checkpoint:
            return {}
        
        try:
            # 从checkpoint获取channel_values
            if isinstance(checkpoint, dict):
                channel_values = checkpoint.get("channel_values", {})
            elif hasattr(checkpoint, 'checkpoint'):
                channel_values = checkpoint.checkpoint.get("channel_values", {})
            else:
                channel_values = {}
            
            # 尝试从特殊通道获取序列化状态
            serialized_state = channel_values.get("__root__")
            if serialized_state is not None:
                # 反序列化完整状态
                return self.universal_serializer.deserialize(serialized_state, "compact_json")
            
            # 尝试从其他可能的通道获取
            for key, value in channel_values.items():
                if key != "workflow_id" and isinstance(value, str):
                    try:
                        # 尝试反序列化这个值
                        return self.universal_serializer.deserialize(value, "compact_json")
                    except:
                        continue
            
            # 如果没有找到，返回空字典
            return {}
        except Exception as e:
            logger.error(f"提取状态失败: {e}")
            return {}