"""
Checkpoint serializer implementation for the infrastructure layer.

This module provides the concrete implementation of ICheckpointSerializer interface,
using the generic Serializer for the actual serialization work.
"""

from typing import Any, Dict, cast

from ...domain.checkpoint.interfaces import ICheckpointSerializer
from ...infrastructure.common.serialization import Serializer
from ...infrastructure.graph.states import create_workflow_state, HumanMessage, AIMessage


class CheckpointSerializer(ICheckpointSerializer):
    """Concrete implementation of checkpoint serializer using the generic Serializer."""
    
    def __init__(self, serializer: Serializer):
        """
        Initialize the checkpoint serializer.
        
        Args:
            serializer: The generic serializer instance to use
        """
        self._serializer = serializer
    
    def serialize_workflow_state(self, state: Any) -> str:
        """
        Serialize a workflow state to string format.
        
        Args:
            state: The workflow state to serialize
            
        Returns:
            Serialized state as string
        """
        return cast(str, self._serializer.serialize(state, format_type="json"))
    
    def deserialize_workflow_state(self, data: str) -> Any:
        """
        Deserialize a workflow state from string format.
        
        Args:
            data: The serialized state data
            
        Returns:
            Deserialized workflow state
        """
        return self._serializer.deserialize(data, format_type="json")
    
    def serialize_messages(self, messages: list) -> str:
        """
        Serialize a list of messages to string format.
        
        Args:
            messages: List of messages to serialize
            
        Returns:
            Serialized messages as string
        """
        return cast(str, self._serializer.serialize(messages, format_type="json"))
    
    def deserialize_messages(self, data: str) -> list:
        """
        Deserialize messages from string format.
        
        Args:
            data: The serialized messages data
            
        Returns:
            List of deserialized messages
        """
        result = self._serializer.deserialize(data, format_type="json")
        return cast(list, result)
    
    def serialize_tool_results(self, tool_results: Dict[str, Any]) -> str:
        """
        Serialize tool results to string format.
        
        Args:
            tool_results: Dictionary of tool results to serialize
            
        Returns:
            Serialized tool results as string
        """
        return cast(str, self._serializer.serialize(tool_results, format_type="json"))
    
    def deserialize_tool_results(self, data: str) -> Dict[str, Any]:
        """
        Deserialize tool results from string format.
        
        Args:
            data: The serialized tool results data
            
        Returns:
            Dictionary of deserialized tool results
        """
        result = self._serializer.deserialize(data, format_type="json")
        return cast(Dict[str, Any], result)
    
    def serialize(self, state: Any) -> Dict[str, Any]:
        """
        Serialize workflow state (backward compatibility).
        
        Args:
            state: Workflow state object
            
        Returns:
            Dict[str, Any]: Serialized state data
        """
        # 为了向后兼容，将字符串包装成字典格式
        serialized_str = self.serialize_workflow_state(state)
        return {"serialized_state": serialized_str}
    
    def deserialize(self, state_data: Dict[str, Any]) -> Any:
        """
        Deserialize workflow state (backward compatibility).
        
        Args:
            state_data: Serialized state data
            
        Returns:
            Any: Deserialized workflow state object
        """
        # 从字典中提取序列化字符串
        if "serialized_state" in state_data:
            return self.deserialize_workflow_state(state_data["serialized_state"])
        else:
            # 处理旧的格式
            return self._create_workflow_state_from_legacy_format(state_data)
    
    def _create_workflow_state_from_legacy_format(self, state_data: Dict[str, Any]) -> Any:
        """
        Create workflow state from legacy format.
        
        Args:
            state_data: Legacy format state data
            
        Returns:
            Workflow state object
        """
        # 处理消息
        messages = []
        if "messages" in state_data:
            messages = self.deserialize_messages(state_data["messages"])
        
        # 处理工具结果
        tool_results = {}
        if "tool_results" in state_data:
            tool_results = self.deserialize_tool_results(state_data["tool_results"])
        
        # 创建状态对象
        return create_workflow_state(
            workflow_id="default",
            workflow_name="legacy",
            input_text="",
            messages=messages,
            max_iterations=10
        )