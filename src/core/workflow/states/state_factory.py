"""工作流状态工厂
专门用于创建工作流状态的工厂模块，消除功能重叠。
"""

from typing import Any, Dict, List, Optional, Union

from .workflow_state import WorkflowState, BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage, MessageRole
from .state_builder import WorkflowStateBuilder


class WorkflowStateFactory:
    """工作流状态工厂类
    提供创建各种工作流状态的统一接口
    """
    
    @staticmethod
    def create_empty_state() -> WorkflowState:
        """创建空的工作流状态
        
        Returns:
            WorkflowState: 空的工作流状态
        """
        return WorkflowState()
    
    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> WorkflowState:
        """从字典创建工作流状态
        
        Args:
            data: 状态数据字典
            
        Returns:
            WorkflowState: 工作流状态
        """
        return WorkflowState.from_dict(data)
    
    @staticmethod
    def create_with_messages(messages: List[Union[BaseMessage, str, Dict[str, Any]]]) -> WorkflowState:
        """创建包含消息的工作流状态
        
        Args:
            messages: 消息列表
            
        Returns:
            WorkflowState: 工作流状态
        """
        return (WorkflowStateBuilder()
                .with_messages(messages)
                .build())
    
    @staticmethod
    def create_with_conversation(human_message: str, ai_message: Optional[str] = None) -> WorkflowState:
        """创建包含对话的工作流状态
        
        Args:
            human_message: 人类消息
            ai_message: AI消息（可选）
            
        Returns:
            WorkflowState: 工作流状态
        """
        builder = WorkflowStateBuilder().with_human_message(human_message)
        
        if ai_message:
            builder.with_ai_message(ai_message)
        
        return builder.build()
    
    @staticmethod
    def create_from_config(workflow_id: str, workflow_name: str, input_text: str,
                          workflow_config: Dict[str, Any] | None = None,
                          max_iterations: int = 10) -> WorkflowState:
        """从配置创建工作流状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            workflow_config: 工作流配置
            max_iterations: 最大迭代次数
            
        Returns:
            WorkflowState: 工作流状态实例
        """
        from .state_builder import WorkflowStateBuilder
        
        return (WorkflowStateBuilder()
                .with_id(workflow_id)
                .with_human_message(input_text)
                .with_max_iterations(max_iterations)
                .with_field("workflow_id", workflow_id)
                .with_field("workflow_name", workflow_name)
                .with_field("workflow_config", workflow_config or {})
                .build())
    
    @staticmethod
    def create_state_class_from_config(state_schema: Any) -> type[dict]:
        """从配置创建状态类
        
        Args:
            state_schema: 状态模式配置
            
        Returns:
            type[dict]: 状态类类型
        """
        # 创建基于配置的动态状态类
        fields: Dict[str, Any] = {}
        
        if hasattr(state_schema, 'fields'):
            for field_name, field_config in state_schema.fields.items():
                fields[field_name] = field_config
        
        # 返回可用作状态的动态类
        class DynamicState(dict):
            """从配置创建的动态状态类"""
            pass
        
        return DynamicState


# 便捷函数
def create_empty() -> WorkflowState:
    """创建空状态的便捷函数"""
    return WorkflowStateFactory.create_empty_state()


def from_dict(data: Dict[str, Any]) -> WorkflowState:
    """从字典创建状态的便捷函数"""
    return WorkflowStateFactory.create_from_dict(data)


def with_messages(messages: List[Union[BaseMessage, str, Dict[str, Any]]]) -> WorkflowState:
    """创建包含消息的状态的便捷函数"""
    return WorkflowStateFactory.create_with_messages(messages)


def conversation(human_message: str, ai_message: Optional[str] = None) -> WorkflowState:
    """创建对话状态的便捷函数"""
    return WorkflowStateFactory.create_with_conversation(human_message, ai_message)


def from_config(workflow_id: str, workflow_name: str, input_text: str, 
               workflow_config: Dict[str, Any] | None = None, 
               max_iterations: int = 10) -> WorkflowState:
    """从配置创建状态的便捷函数"""
    return WorkflowStateFactory.create_from_config(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        input_text=input_text,
        workflow_config=workflow_config,
        max_iterations=max_iterations
    )