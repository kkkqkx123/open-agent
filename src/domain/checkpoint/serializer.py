"""Checkpoint序列化器实现

提供工作流状态的序列化和反序列化功能。
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .interfaces import ICheckpointSerializer

logger = logging.getLogger(__name__)


class DefaultCheckpointSerializer(ICheckpointSerializer):
    """默认checkpoint序列化器
    
    处理基本的工作流状态序列化和反序列化。
    """
    
    def serialize(self, state: Any) -> Dict[str, Any]:
        """序列化工作流状态
        
        Args:
            state: 工作流状态对象
            
        Returns:
            Dict[str, Any]: 序列化后的状态数据
        """
        try:
            if hasattr(state, 'to_dict'):
                # 如果状态对象有to_dict方法，使用它
                return state.to_dict()
            elif hasattr(state, '__dict__'):
                # 如果是普通对象，序列化其属性
                result = {}
                for key, value in state.__dict__.items():
                    if not key.startswith('_'):  # 跳过私有属性
                        result[key] = self._serialize_value(value)
                return result
            elif isinstance(state, dict):
                # 如果是字典，递归序列化所有值
                return {k: self._serialize_value(v) for k, v in state.items()}
            elif isinstance(state, (list, tuple)):
                # 如果是列表或元组，递归序列化所有元素
                return {'type': 'list', 'items': [self._serialize_value(item) for item in state]}
            else:
                # 其他类型，直接转换为字符串
                return {'value': str(state), 'type': type(state).__name__}
        except Exception as e:
            logger.error(f"序列化状态失败: {e}")
            return {'error': str(e), 'original_type': type(state).__name__}
    
    def deserialize(self, state_data: Dict[str, Any]) -> Any:
        """反序列化工作流状态
        
        Args:
            state_data: 序列化的状态数据
            
        Returns:
            Any: 反序列化后的工作流状态对象
        """
        try:
            if not isinstance(state_data, dict):
                return state_data
            
            # 检查是否有错误信息
            if 'error' in state_data:
                logger.warning(f"状态数据包含错误: {state_data['error']}")
                return None
            
            # 检查是否是简单值
            if 'value' in state_data and 'type' in state_data:
                return state_data['value']
            
            # 尝试创建WorkflowState对象
            try:
                from ...application.workflow.state import WorkflowState
                workflow_state = WorkflowState()
                
                # 恢复基本属性
                if 'messages' in state_data:
                    workflow_state.messages = self._deserialize_messages(state_data['messages'])
                
                if 'tool_results' in state_data:
                    workflow_state.tool_results = self._deserialize_tool_results(state_data['tool_results'])
                
                if 'current_step' in state_data:
                    workflow_state.current_step = state_data['current_step']
                
                if 'max_iterations' in state_data:
                    workflow_state.max_iterations = state_data['max_iterations']
                
                if 'iteration_count' in state_data:
                    workflow_state.iteration_count = state_data['iteration_count']
                
                if 'workflow_name' in state_data:
                    workflow_state.workflow_name = state_data['workflow_name']
                
                if 'start_time' in state_data and state_data['start_time']:
                    try:
                        workflow_state.start_time = datetime.fromisoformat(state_data['start_time'])
                    except (ValueError, TypeError):
                        workflow_state.start_time = None
                
                if 'errors' in state_data:
                    workflow_state.errors = state_data['errors']
                
                if 'custom_fields' in state_data:
                    workflow_state.custom_fields = state_data['custom_fields']
                
                return workflow_state
            except ImportError:
                logger.warning("无法导入WorkflowState，返回原始数据")
                return state_data
            except Exception as e:
                logger.error(f"创建WorkflowState失败: {e}")
                return state_data
                
        except Exception as e:
            logger.error(f"反序列化状态失败: {e}")
            return None
    
    def _serialize_value(self, value: Any) -> Any:
        """序列化单个值
        
        Args:
            value: 要序列化的值
            
        Returns:
            Any: 序列化后的值
        """
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, 'to_dict'):
            return value.to_dict()
        elif hasattr(value, '__dict__'):
            return {k: self._serialize_value(v) for k, v in value.__dict__.items() if not k.startswith('_')}
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        else:
            return str(value)
    
    def _deserialize_messages(self, messages_data: Any) -> list:
        """反序列化消息列表
        
        Args:
            messages_data: 消息数据
            
        Returns:
            list: 反序列化后的消息列表
        """
        if not isinstance(messages_data, list):
            return []
        
        messages = []
        for msg_data in messages_data:
            try:
                # 尝试创建适当的消息类型
                if isinstance(msg_data, dict):
                    msg_type = msg_data.get('type', 'BaseMessage')
                    content = msg_data.get('content', '')
                    role = msg_data.get('role', 'human')
                    
                    # 导入消息类型
                    try:
                        from ...domain.prompts.agent_state import (
                            BaseMessage, HumanMessage, AIMessage, 
                            SystemMessage, ToolMessage, MessageRole
                        )
                        
                        if msg_type == 'HumanMessage':
                            msg = HumanMessage(content=content)
                        elif msg_type == 'SystemMessage':
                            msg = SystemMessage(content=content)
                        elif msg_type == 'AIMessage':
                            msg = AIMessage(content=content)
                        elif msg_type == 'ToolMessage':
                            msg = ToolMessage(content=content)
                        else:
                            # 尝试解析角色
                            try:
                                role_enum = MessageRole(role)
                                msg = BaseMessage(content=content, role=role_enum)
                            except ValueError:
                                msg = BaseMessage(content=content, role=MessageRole.HUMAN)
                        
                        messages.append(msg)
                    except ImportError:
                        # 如果无法导入消息类型，创建基本字典
                        messages.append(msg_data)
                else:
                    messages.append(msg_data)
            except Exception as e:
                logger.error(f"反序列化消息失败: {e}")
                continue
        
        return messages
    
    def _deserialize_tool_results(self, tool_results_data: Any) -> list:
        """反序列化工具结果列表
        
        Args:
            tool_results_data: 工具结果数据
            
        Returns:
            list: 反序列化后的工具结果列表
        """
        if not isinstance(tool_results_data, list):
            return []
        
        tool_results = []
        for result_data in tool_results_data:
            try:
                if isinstance(result_data, dict):
                    # 导入ToolResult
                    try:
                        from ...domain.prompts.agent_state import ToolResult
                        result = ToolResult(
                            tool_name=result_data.get('tool_name', ''),
                            success=result_data.get('success', False),
                            output=result_data.get('result'),
                            error=result_data.get('error')
                        )
                        tool_results.append(result)
                    except ImportError:
                        tool_results.append(result_data)
                else:
                    tool_results.append(result_data)
            except Exception as e:
                logger.error(f"反序列化工具结果失败: {e}")
                continue
        
        return tool_results


class JSONCheckpointSerializer(ICheckpointSerializer):
    """JSON checkpoint序列化器
    
    使用JSON进行序列化和反序列化。
    """
    
    def serialize(self, state: Any) -> Dict[str, Any]:
        """序列化工作流状态为JSON
        
        Args:
            state: 工作流状态对象
            
        Returns:
            Dict[str, Any]: 序列化后的状态数据
        """
        try:
            # 使用默认序列化器进行基本序列化
            default_serializer = DefaultCheckpointSerializer()
            serialized = default_serializer.serialize(state)
            
            # 确保所有数据都可以JSON序列化
            return json.loads(json.dumps(serialized, default=str, ensure_ascii=False))
        except Exception as e:
            logger.error(f"JSON序列化失败: {e}")
            return {'error': str(e), 'original_type': type(state).__name__}
    
    def deserialize(self, state_data: Dict[str, Any]) -> Any:
        """从JSON反序列化工作流状态
        
        Args:
            state_data: 序列化的状态数据
            
        Returns:
            Any: 反序列化后的工作流状态对象
        """
        try:
            # 使用默认序列化器进行反序列化
            default_serializer = DefaultCheckpointSerializer()
            return default_serializer.deserialize(state_data)
        except Exception as e:
            logger.error(f"JSON反序列化失败: {e}")
            return None