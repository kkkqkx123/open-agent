"""Checkpoint序列化服务

实现ICheckpointSerializer接口，负责工作流状态的序列化和反序列化。
"""

import json
import logging
from typing import Dict, Any, Optional, List

from src.interfaces.checkpoint import ICheckpointSerializer
from src.core.common.serialization import Serializer


logger = logging.getLogger(__name__)


class CheckpointSerializer(ICheckpointSerializer):
    """Checkpoint序列化器实现
    
    提供工作流状态、消息和工具结果的序列化功能。
    """
    
    def __init__(self, enable_compression: bool = False, cache_size: int = 1000):
        """初始化序列化器
        
        Args:
            enable_compression: 是否启用压缩
            cache_size: 缓存大小
        """
        self._serializer = Serializer(
            enable_cache=True,
            cache_size=cache_size
        )
        self._enable_compression = enable_compression
    
    def _ensure_str(self, data: Any) -> str:
        """确保数据是字符串类型"""
        if isinstance(data, str):
            return data
        elif isinstance(data, bytes):
            return data.decode('utf-8')
        elif isinstance(data, (bytearray, memoryview)):
            return bytes(data).decode('utf-8')
        else:
            return str(data)
    
    def serialize_workflow_state(self, state: Any) -> str:
        """序列化工作流状态到字符串格式
        
        Args:
            state: 工作流状态对象
            
        Returns:
            str: 序列化后的状态字符串
        """
        try:
            # 使用通用序列化器进行序列化
            serialized_data = self._serializer.serialize(
                state,
                format=self._serializer.FORMAT_JSON
            )
            
            # 确保返回字符串类型
            result = self._ensure_str(serialized_data)
            
            logger.debug(f"Serialized workflow state of type: {type(state)}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to serialize workflow state: {e}")
            raise
    
    def deserialize_workflow_state(self, data: str) -> Any:
        """从字符串格式反序列化工作流状态
        
        Args:
            data: 序列化的状态字符串
            
        Returns:
            Any: 反序列化后的工作流状态对象
        """
        try:
            # 使用通用序列化器进行反序列化
            deserialized_data = self._serializer.deserialize(
                data, 
                format=self._serializer.FORMAT_JSON
            )
            
            logger.debug(f"Deserialized workflow state")
            return deserialized_data
            
        except Exception as e:
            logger.error(f"Failed to deserialize workflow state: {e}")
            raise
    
    def serialize_messages(self, messages: list) -> str:
        """序列化消息列表到字符串格式
        
        Args:
            messages: 要序列化的消息列表
            
        Returns:
            str: 序列化后的消息字符串
        """
        try:
            # 序列化消息列表
            serialized_data = self._serializer.serialize(
                messages,
                format=self._serializer.FORMAT_JSON
            )
            
            # 确保返回字符串类型
            result = self._ensure_str(serialized_data)
            
            logger.debug(f"Serialized {len(messages)} messages")
            return result
            
        except Exception as e:
            logger.error(f"Failed to serialize messages: {e}")
            raise
    
    def deserialize_messages(self, data: str) -> list:
        """从字符串格式反序列化消息
        
        Args:
            data: 序列化的消息字符串
            
        Returns:
            list: 反序列化后的消息列表
        """
        try:
            # 反序列化消息数据
            deserialized_data = self._serializer.deserialize(
                data, 
                format=self._serializer.FORMAT_JSON
            )
            
            if not isinstance(deserialized_data, list):
                raise ValueError(f"Expected list, got {type(deserialized_data)}")
            
            logger.debug(f"Deserialized {len(deserialized_data)} messages")
            return deserialized_data
            
        except Exception as e:
            logger.error(f"Failed to deserialize messages: {e}")
            raise
    
    def serialize_tool_results(self, tool_results: Dict[str, Any]) -> str:
        """序列化工具结果到字符串格式
        
        Args:
            tool_results: 要序列化的工具结果字典
            
        Returns:
            str: 序列化后的工具结果字符串
        """
        try:
            # 序列化工具结果
            serialized_data = self._serializer.serialize(
                tool_results,
                format=self._serializer.FORMAT_JSON
            )
            
            # 确保返回字符串类型
            result = self._ensure_str(serialized_data)
            
            logger.debug(f"Serialized tool results with {len(tool_results)} entries")
            return result
            
        except Exception as e:
            logger.error(f"Failed to serialize tool results: {e}")
            raise
    
    def deserialize_tool_results(self, data: str) -> Dict[str, Any]:
        """从字符串格式反序列化工具结果
        
        Args:
            data: 序列化的工具结果字符串
            
        Returns:
            Dict[str, Any]: 反序列化后的工具结果字典
        """
        try:
            # 反序列化工具结果
            deserialized_data = self._serializer.deserialize(
                data, 
                format=self._serializer.FORMAT_JSON
            )
            
            if not isinstance(deserialized_data, dict):
                raise ValueError(f"Expected dict, got {type(deserialized_data)}")
            
            logger.debug(f"Deserialized tool results with {len(deserialized_data)} entries")
            return deserialized_data
            
        except Exception as e:
            logger.error(f"Failed to deserialize tool results: {e}")
            raise
    
    def serialize(self, state: Any) -> Dict[str, Any]:
        """序列化工作流状态（向后兼容）
        
        Args:
            state: 工作流状态对象
            
        Returns:
            Dict[str, Any]: 序列化后的状态数据
        """
        try:
            # 将状态序列化为字符串，然后包装到字典中
            serialized_state = self.serialize_workflow_state(state)
            
            result = {
                'state_data': serialized_state,
                'format': 'json',
                'serialized_at': self._serializer.serialize(
                    {'timestamp': 'now'}, 
                    format=self._serializer.FORMAT_JSON
                )
            }
            
            logger.debug(f"Serialized state with backward compatibility")
            return result
            
        except Exception as e:
            logger.error(f"Failed to serialize state with backward compatibility: {e}")
            raise
    
    def deserialize(self, state_data: Dict[str, Any]) -> Any:
        """反序列化工作流状态（向后兼容）
        
        Args:
            state_data: 序列化的状态数据
            
        Returns:
            Any: 反序列化后的工作流状态对象
        """
        try:
            # 从字典中提取序列化状态并反序列化
            if 'state_data' in state_data:
                serialized_state = state_data['state_data']
                deserialized_state = self.deserialize_workflow_state(serialized_state)
                
                logger.debug(f"Deserialized state with backward compatibility")
                return deserialized_state
            else:
                raise ValueError("state_data key not found in state_data dict")
                
        except Exception as e:
            logger.error(f"Failed to deserialize state with backward compatibility: {e}")
            raise