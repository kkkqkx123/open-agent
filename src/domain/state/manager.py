"""状态管理器

提供统一的状态管理功能，支持不同类型的状态转换和持久化。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import asdict
import json
import logging

from .interfaces import IStateManager, IStateConverter, IStateValidator
from ..agent.state import AgentState
from ...application.workflow.state import WorkflowState

logger = logging.getLogger(__name__)


class StateManager(IStateManager):
    """状态管理器实现"""
    
    def __init__(self):
        """初始化状态管理器"""
        self._converters: Dict[Type, IStateConverter] = {}
        self._validators: Dict[Type, IStateValidator] = {}
        self._state_history: List[Dict[str, Any]] = []
        
        # 注册默认转换器
        self._register_default_converters()
        
        # 注册默认验证器
        self._register_default_validators()
    
    def register_converter(self, state_type: Type, converter: IStateConverter) -> None:
        """注册状态转换器
        
        Args:
            state_type: 状态类型
            converter: 转换器实例
        """
        self._converters[state_type] = converter
        logger.debug(f"注册状态转换器: {state_type.__name__}")
    
    def register_validator(self, state_type: Type, validator: IStateValidator) -> None:
        """注册状态验证器
        
        Args:
            state_type: 状态类型
            validator: 验证器实例
        """
        self._validators[state_type] = validator
        logger.debug(f"注册状态验证器: {state_type.__name__}")
    
    def convert_state(self, source_state: Any, target_type: Type) -> Any:
        """转换状态类型
        
        Args:
            source_state: 源状态
            target_type: 目标类型
            
        Returns:
            转换后的状态
            
        Raises:
            ValueError: 转换失败
        """
        source_type = type(source_state)
        
        if source_type == target_type:
            return source_state
        
        # 查找转换器
        converter = self._converters.get(source_type)
        if not converter:
            raise ValueError(f"未找到状态转换器: {source_type.__name__}")
        
        try:
            return converter.convert(source_state, target_type)
        except Exception as e:
            logger.error(f"状态转换失败: {e}")
            raise ValueError(f"状态转换失败: {e}")
    
    def validate_state(self, state: Any) -> bool:
        """验证状态
        
        Args:
            state: 要验证的状态
            
        Returns:
            bool: 验证是否通过
        """
        state_type = type(state)
        validator = self._validators.get(state_type)
        
        if not validator:
            # 如果没有专门的验证器，返回True
            return True
        
        try:
            return validator.validate(state)
        except Exception as e:
            logger.error(f"状态验证失败: {e}")
            return False
    
    def save_state_snapshot(self, state: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """保存状态快照
        
        Args:
            state: 状态对象
            metadata: 元数据
            
        Returns:
            str: 快照ID
        """
        import uuid
        snapshot_id = str(uuid.uuid4())
        
        snapshot = {
            "id": snapshot_id,
            "state_type": type(state).__name__,
            "state_data": self._serialize_state(state),
            "metadata": metadata or {},
            "timestamp": self._get_timestamp()
        }
        
        self._state_history.append(snapshot)
        logger.debug(f"保存状态快照: {snapshot_id}")
        
        return snapshot_id
    
    def load_state_snapshot(self, snapshot_id: str) -> Any:
        """加载状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            状态对象
            
        Raises:
            ValueError: 快照不存在
        """
        for snapshot in self._state_history:
            if snapshot["id"] == snapshot_id:
                state_type_name = snapshot["state_type"]
                state_data = snapshot["state_data"]
                
                # 根据类型名称创建状态对象
                if state_type_name == "AgentState":
                    return AgentState.from_dict(state_data)
                elif state_type_name == "WorkflowState":
                    # 这里需要实现WorkflowState.from_dict方法
                    # 暂时返回None
                    logger.warning("WorkflowState.from_dict方法尚未实现")
                    return None
                else:
                    raise ValueError(f"未知的状态类型: {state_type_name}")
        
        raise ValueError(f"快照不存在: {snapshot_id}")
    
    def get_state_history(self, state_type: Optional[Type] = None) -> List[Dict[str, Any]]:
        """获取状态历史
        
        Args:
            state_type: 状态类型过滤
            
        Returns:
            状态历史列表
        """
        if state_type is None:
            return self._state_history.copy()
        
        type_name = state_type.__name__
        return [
            snapshot for snapshot in self._state_history
            if snapshot["state_type"] == type_name
        ]
    
    def clear_history(self) -> None:
        """清除状态历史"""
        self._state_history.clear()
        logger.debug("清除状态历史")
    
    def _register_default_converters(self) -> None:
        """注册默认转换器"""
        # AgentState到WorkflowState的转换器
        self.register_converter(AgentState, AgentToWorkflowConverter())
        
        # WorkflowState到AgentState的转换器
        self.register_converter(WorkflowState, WorkflowToAgentConverter())
    
    def _register_default_validators(self) -> None:
        """注册默认验证器"""
        # AgentState验证器
        self.register_validator(AgentState, AgentStateValidator())
        
        # WorkflowState验证器
        self.register_validator(WorkflowState, WorkflowStateValidator())
    
    def _serialize_state(self, state: Any) -> Dict[str, Any]:
        """序列化状态
        
        Args:
            state: 状态对象
            
        Returns:
            序列化后的数据
        """
        if hasattr(state, 'to_dict'):
            return state.to_dict()
        elif hasattr(state, '__dict__'):
            return state.__dict__
        else:
            return {"value": str(state)}
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


class AgentToWorkflowConverter(IStateConverter):
    """AgentState到WorkflowState的转换器"""
    
    def convert(self, source_state: AgentState, target_type: Type) -> WorkflowState:
        """转换AgentState为WorkflowState"""
        if target_type != WorkflowState:
            raise ValueError(f"不支持的目标类型: {target_type.__name__}")
        
        # 创建WorkflowState
        workflow_state = WorkflowState()
        
        # 复制基本信息
        workflow_state.agent_id = source_state.agent_id
        workflow_state.workflow_name = f"agent_{source_state.agent_type}"
        
        # 转换消息
        for agent_msg in source_state.messages:
            from ...application.workflow.state import BaseMessage, MessageRole
            
            # 映射角色
            role_mapping = {
                "user": MessageRole.HUMAN,
                "assistant": MessageRole.AI,
                "system": MessageRole.SYSTEM,
                "tool": MessageRole.TOOL
            }
            
            role = role_mapping.get(agent_msg.role, MessageRole.HUMAN)
            
            # 创建消息
            if role == MessageRole.HUMAN:
                from ...application.workflow.state import HumanMessage
                msg = HumanMessage(content=agent_msg.content)
            elif role == MessageRole.AI:
                from ...application.workflow.state import AIMessage
                msg = AIMessage(content=agent_msg.content)
            elif role == MessageRole.SYSTEM:
                from ...application.workflow.state import SystemMessage
                msg = SystemMessage(content=agent_msg.content)
            else:
                msg = BaseMessage(content=agent_msg.content, type=role)
            
            workflow_state.add_message(msg)
        
        # 复制工具结果
        workflow_state.tool_results = source_state.tool_results
        
        # 复制控制信息
        workflow_state.current_step = source_state.current_step
        workflow_state.max_iterations = source_state.max_iterations
        workflow_state.iteration_count = source_state.iteration_count
        
        # 复制错误
        workflow_state.errors = source_state.errors
        
        # 复制自定义字段
        workflow_state.custom_fields = source_state.custom_fields
        
        return workflow_state


class WorkflowToAgentConverter(IStateConverter):
    """WorkflowState到AgentState的转换器"""
    
    def convert(self, source_state: WorkflowState, target_type: Type) -> AgentState:
        """转换WorkflowState为AgentState"""
        if target_type != AgentState:
            raise ValueError(f"不支持的目标类型: {target_type.__name__}")
        
        # 创建AgentState
        agent_state = AgentState()
        
        # 复制基本信息
        agent_state.agent_id = source_state.agent_id
        agent_state.agent_type = source_state.workflow_name.replace("agent_", "")
        
        # 转换消息
        for workflow_msg in source_state.messages:
            # 映射角色
            role_mapping = {
                "human": "user",
                "ai": "assistant",
                "system": "system",
                "tool": "tool"
            }
            
            role = role_mapping.get(workflow_msg.role.value, "user")
            
            # 创建消息
            from ..agent.state import AgentMessage
            agent_msg = AgentMessage(
                content=workflow_msg.content,
                role=role,
                timestamp=workflow_msg.timestamp,
                metadata=workflow_msg.metadata
            )
            
            agent_state.add_message(agent_msg)
        
        # 复制工具结果
        agent_state.tool_results = source_state.tool_results
        
        # 复制控制信息
        agent_state.current_step = source_state.current_step
        agent_state.max_iterations = source_state.max_iterations
        agent_state.iteration_count = source_state.iteration_count
        
        # 复制错误
        agent_state.errors = source_state.errors
        
        # 复制自定义字段
        agent_state.custom_fields = source_state.custom_fields
        
        return agent_state


class AgentStateValidator(IStateValidator):
    """AgentState验证器"""
    
    def validate(self, state: AgentState) -> bool:
        """验证AgentState"""
        # 基本验证
        if not state.agent_id:
            logger.warning("AgentState缺少agent_id")
            return False
        
        if not state.agent_type:
            logger.warning("AgentState缺少agent_type")
            return False
        
        # 验证迭代次数
        if state.iteration_count < 0:
            logger.warning("AgentState迭代次数不能为负数")
            return False
        
        if state.max_iterations <= 0:
            logger.warning("AgentState最大迭代次数必须大于0")
            return False
        
        return True


class WorkflowStateValidator(IStateValidator):
    """WorkflowState验证器"""
    
    def validate(self, state: WorkflowState) -> bool:
        """验证WorkflowState"""
        # 基本验证
        if not state.workflow_id:
            logger.warning("WorkflowState缺少workflow_id")
            return False
        
        # 验证迭代次数
        if state.iteration_count < 0:
            logger.warning("WorkflowState迭代次数不能为负数")
            return False
        
        if state.max_iterations <= 0:
            logger.warning("WorkflowState最大迭代次数必须大于0")
            return False
        
        return True