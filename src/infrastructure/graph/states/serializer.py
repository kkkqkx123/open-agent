"""状态序列化器

提供高效的状态序列化和反序列化功能。
"""

import json
import pickle
from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime
from dataclasses import asdict

from .base import BaseGraphState, BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from .agent import AgentState
from .workflow import WorkflowState
from .react import ReActState
from .plan_execute import PlanExecuteState


class StateSerializer:
    """状态序列化器
    
    提供高效的状态序列化和反序列化功能，支持多种格式。
    """
    
    # 支持的序列化格式
    FORMAT_JSON = "json"
    FORMAT_PICKLE = "pickle"
    
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
        if isinstance(message, ToolMessage) and hasattr(message, 'tool_call_id'):
            message_data["tool_call_id"] = message.tool_call_id
        
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
    
    @staticmethod
    def serialize_state(
        state: Dict[str, Any],
        format: str = FORMAT_JSON,
        include_metadata: bool = True
    ) -> Union[str, bytes]:
        """序列化状态
        
        Args:
            state: 状态字典
            format: 序列化格式 ("json" 或 "pickle")
            include_metadata: 是否包含元数据
            
        Returns:
            序列化后的数据
            
        Raises:
            ValueError: 当格式不支持时
        """
        # 准备序列化数据
        serialized_data = StateSerializer._prepare_state_for_serialization(
            state, include_metadata
        )
        
        if format == StateSerializer.FORMAT_JSON:
            return json.dumps(serialized_data, ensure_ascii=False, indent=2, default=str)
        elif format == StateSerializer.FORMAT_PICKLE:
            return pickle.dumps(serialized_data)
        else:
            raise ValueError(f"不支持的序列化格式: {format}")
    
    @staticmethod
    def deserialize_state(
        serialized_data: Union[str, bytes],
        format: str = FORMAT_JSON,
        state_type: Optional[Type] = None
    ) -> Dict[str, Any]:
        """反序列化状态
        
        Args:
            serialized_data: 序列化的数据
            format: 序列化格式 ("json" 或 "pickle")
            state_type: 状态类型（用于验证）
            
        Returns:
            反序列化后的状态字典
            
        Raises:
            ValueError: 当格式不支持时
        """
        # 反序列化基础数据
        if format == StateSerializer.FORMAT_JSON:
            data = json.loads(serialized_data)
        elif format == StateSerializer.FORMAT_PICKLE:
            data = pickle.loads(serialized_data)
        else:
            raise ValueError(f"不支持的序列化格式: {format}")
        
        # 恢复状态对象
        restored_state = StateSerializer._restore_state_from_serialization(data)
        
        # 验证状态类型
        if state_type:
            from .factory import StateFactory
            errors = StateFactory.validate_state(restored_state, state_type)
            if errors:
                raise ValueError(f"状态验证失败: {errors}")
        
        return restored_state
    
    @staticmethod
    def _prepare_state_for_serialization(
        state: Dict[str, Any],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """准备状态用于序列化
        
        Args:
            state: 原始状态
            include_metadata: 是否包含元数据
            
        Returns:
            准备好的序列化数据
        """
        serialized = state.copy()
        
        # 序列化消息列表
        if "messages" in serialized:
            serialized["messages"] = [
                StateSerializer.serialize_message(msg) 
                for msg in serialized["messages"]
            ]
        
        # 处理日期时间对象
        datetime_fields = ["start_time", "end_time"]
        for field in datetime_fields:
            if field in serialized and serialized[field] is not None:
                if isinstance(serialized[field], datetime):
                    serialized[field] = serialized[field].isoformat()
        
        # 处理图状态字典
        if "graph_states" in serialized:
            graph_states = {}
            for graph_id, graph_state in serialized["graph_states"].items():
                graph_states[graph_id] = StateSerializer._prepare_state_for_serialization(
                    graph_state, include_metadata
                )
            serialized["graph_states"] = graph_states
        
        # 添加序列化元数据
        if include_metadata:
            serialized["_serialization_metadata"] = {
                "serialized_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        
        return serialized
    
    @staticmethod
    def _restore_state_from_serialization(data: Dict[str, Any]) -> Dict[str, Any]:
        """从序列化数据恢复状态
        
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
                StateSerializer.deserialize_message(msg_data) 
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
                        # 如果解析失败，保持原样
                        pass
        
        # 恢复图状态字典
        if "graph_states" in state:
            graph_states = {}
            for graph_id, graph_state_data in state["graph_states"].items():
                graph_states[graph_id] = StateSerializer._restore_state_from_serialization(
                    graph_state_data
                )
            state["graph_states"] = graph_states
        
        return state
    
    @staticmethod
    def serialize_state_diff(
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        format: str = FORMAT_JSON
    ) -> Union[str, bytes]:
        """序列化状态差异
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            format: 序列化格式
            
        Returns:
            序列化后的差异数据
        """
        diff = StateSerializer._compute_state_diff(old_state, new_state)
        
        if format == StateSerializer.FORMAT_JSON:
            return json.dumps(diff, ensure_ascii=False, indent=2, default=str)
        elif format == StateSerializer.FORMAT_PICKLE:
            return pickle.dumps(diff)
        else:
            raise ValueError(f"不支持的序列化格式: {format}")
    
    @staticmethod
    def apply_state_diff(
        base_state: Dict[str, Any],
        diff_data: Union[str, bytes],
        format: str = FORMAT_JSON
    ) -> Dict[str, Any]:
        """应用状态差异
        
        Args:
            base_state: 基础状态
            diff_data: 差异数据
            format: 序列化格式
            
        Returns:
            应用差异后的状态
        """
        if format == StateSerializer.FORMAT_JSON:
            diff = json.loads(diff_data)
        elif format == StateSerializer.FORMAT_PICKLE:
            diff = pickle.loads(diff_data)
        else:
            raise ValueError(f"不支持的序列化格式: {format}")
        
        return StateSerializer._apply_state_diff(base_state, diff)
    
    @staticmethod
    def _compute_state_diff(
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算状态差异
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            
        Returns:
            状态差异
        """
        diff = {
            "added": {},
            "modified": {},
            "removed": {}
        }
        
        # 检查新增和修改的字段
        for key, new_value in new_state.items():
            if key not in old_state:
                diff["added"][key] = new_value
            elif old_state[key] != new_value:
                diff["modified"][key] = {
                    "old": old_state[key],
                    "new": new_value
                }
        
        # 检查删除的字段
        for key in old_state:
            if key not in new_state:
                diff["removed"][key] = old_state[key]
        
        return diff
    
    @staticmethod
    def _apply_state_diff(
        base_state: Dict[str, Any],
        diff: Dict[str, Any]
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
        for key, value in diff.get("added", {}).items():
            result[key] = value
        
        # 应用修改字段
        for key, change in diff.get("modified", {}).items():
            result[key] = change["new"]
        
        # 移除删除字段
        for key in diff.get("removed", {}):
            if key in result:
                del result[key]
        
        return result
    
    @staticmethod
    def get_state_size(state: Dict[str, Any]) -> int:
        """获取状态大小（字节）
        
        Args:
            state: 状态字典
            
        Returns:
            状态大小（字节）
        """
        serialized = StateSerializer.serialize_state(state, format=StateSerializer.FORMAT_PICKLE)
        return len(serialized)
    
    @staticmethod
    def optimize_state_for_storage(state: Dict[str, Any]) -> Dict[str, Any]:
        """优化状态用于存储
        
        Args:
            state: 原始状态
            
        Returns:
            优化后的状态
        """
        optimized = state.copy()
        
        # 移除空的可累加字段
        additive_fields = ["messages", "tool_calls", "tool_results", "errors", "steps", "step_results"]
        for field in additive_fields:
            if field in optimized and not optimized[field]:
                del optimized[field]
        
        # 移除None值
        none_fields = [key for key, value in optimized.items() if value is None]
        for field in none_fields:
            del optimized[field]
        
        return optimized