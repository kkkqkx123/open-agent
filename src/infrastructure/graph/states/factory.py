"""状态工厂

提供统一的状态创建和初始化方法。
"""

from typing import Dict, Any, List, Optional, Type, Union, cast
from datetime import datetime
from typing_extensions import TypedDict

from .base import BaseGraphState, BaseMessage, create_base_state, create_message, LCBaseMessage
from .workflow import WorkflowState, create_workflow_state
from .react import ReActState, create_react_state
from .plan_execute import PlanExecuteState, create_plan_execute_state


# Agent状态类型已弃用，统一使用WorkflowState


class StateFactory:
    """状态工厂类
    
    提供统一的状态创建接口，支持各种状态类型的创建和初始化。
    """
    
    @staticmethod
    def create_base_state(
        messages: Optional[List] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None,
        current_step: str = "start"
    ) -> BaseGraphState:
        """创建基础状态
        
        Args:
            messages: 初始消息列表
            metadata: 元数据
            execution_context: 执行上下文
            current_step: 当前步骤
            
        Returns:
            BaseGraphState实例
        """
        return create_base_state(
            messages=messages,
            metadata=metadata,
            execution_context=execution_context,
            current_step=current_step
        )
    
    @staticmethod
    def create_agent_state(
        input_text: str,
        agent_id: str,
        agent_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
        messages: Optional[List] = None
    ) -> WorkflowState:
        """创建Agent状态（已弃用，使用create_workflow_state替代）
        
        Args:
            input_text: 输入文本
            agent_id: Agent ID
            agent_config: Agent配置
            max_iterations: 最大迭代次数
            messages: 初始消息列表
            
        Returns:
            WorkflowState实例
        """
        # 使用工作流状态创建函数来创建状态
        return create_workflow_state(
            workflow_id=agent_id,
            workflow_name=f"agent_{agent_id}",
            input_text=input_text,
            workflow_config=agent_config,
            max_iterations=max_iterations,
            messages=messages
        )
    
    @staticmethod
    def create_workflow_state(
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        workflow_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10
    ) -> WorkflowState:
        """创建工作流状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            workflow_config: 工作流配置
            max_iterations: 最大迭代次数
            
        Returns:
            WorkflowState实例
        """
        return create_workflow_state(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_text=input_text,
            workflow_config=workflow_config,
            max_iterations=max_iterations
        )
    
    @staticmethod
    def create_react_state(
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        max_iterations: int = 10,
        max_steps: int = 10
    ) -> ReActState:
        """创建ReAct状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            max_iterations: 最大迭代次数
            max_steps: 最大步骤数
            
        Returns:
            ReActState实例
        """
        return create_react_state(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_text=input_text,
            max_iterations=max_iterations,
            max_steps=max_steps
        )
    
    @staticmethod
    def create_plan_execute_state(
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        max_iterations: int = 10,
        max_steps: int = 10
    ) -> PlanExecuteState:
        """创建计划执行状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            max_iterations: 最大迭代次数
            max_steps: 最大步骤数
            
        Returns:
            PlanExecuteState实例
        """
        return create_plan_execute_state(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_text=input_text,
            max_iterations=max_iterations,
            max_steps=max_steps
        )
    
    @staticmethod
    def create_state_by_type(
        state_type: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """根据类型创建状态
        
        Args:
            state_type: 状态类型 ("base", "agent", "workflow", "react", "plan_execute")
            **kwargs: 状态创建参数
            
        Returns:
            对应类型的状态实例
            
        Raises:
            ValueError: 当状态类型不支持时
        """
        state_creators = {
            "base": StateFactory.create_base_state,
            "agent": StateFactory.create_agent_state,
            "workflow": StateFactory.create_workflow_state,
            "react": StateFactory.create_react_state,
            "plan_execute": StateFactory.create_plan_execute_state
        }
        
        creator = state_creators.get(state_type)
        if not creator:
            raise ValueError(f"不支持的状态类型: {state_type}")
        
        return creator(**kwargs)  # type: ignore
    
    @staticmethod
    def create_message(content: str, role: str, **kwargs: Any) -> LCBaseMessage:
        """创建消息
        
        Args:
            content: 消息内容
            role: 消息角色
            **kwargs: 其他参数
            
        Returns:
            消息实例
        """
        return create_message(content=content, role=role, **kwargs)  # 返回LangChain消息类型
    
    @staticmethod
    def create_initial_messages(input_text: str, system_prompt: Optional[str] = None) -> List:
        """创建初始消息列表
        
        Args:
            input_text: 输入文本
            system_prompt: 系统提示
            
        Returns:
            初始消息列表
        """
        messages = []
        
        if system_prompt:
            messages.append(create_message(system_prompt, "system"))
        
        messages.append(create_message(input_text, "human"))
        
        return messages
    
    @staticmethod
    def clone_state(state: Dict[str, Any]) -> Dict[str, Any]:
        """克隆状态
        
        Args:
            state: 要克隆的状态
            
        Returns:
            克隆的状态
        """
        # 浅拷贝状态字典
        cloned = state.copy()
        
        # 深拷贝特定字段
        if "messages" in cloned:
            cloned["messages"] = cloned["messages"].copy()
        
        if "tool_calls" in cloned:
            cloned["tool_calls"] = cloned["tool_calls"].copy()
        
        if "tool_results" in cloned:
            cloned["tool_results"] = cloned["tool_results"].copy()
        
        if "errors" in cloned:
            cloned["errors"] = cloned["errors"].copy()
        
        if "steps" in cloned:
            cloned["steps"] = cloned["steps"].copy()
        
        if "step_results" in cloned:
            cloned["step_results"] = cloned["step_results"].copy()
        
        if "graph_states" in cloned:
            cloned["graph_states"] = cloned["graph_states"].copy()
        
        return cloned
    
    @staticmethod
    def merge_states(base_state: Dict[str, Any], update_state: Dict[str, Any]) -> Dict[str, Any]:
        """合并状态
        
        Args:
            base_state: 基础状态
            update_state: 更新状态
            
        Returns:
            合并后的状态
        """
        merged = StateFactory.clone_state(base_state)
        
        # 合并特殊字段（使用累加操作）
        additive_fields = [
            "messages", "tool_calls", "tool_results", 
            "errors", "steps", "step_results"
        ]
        
        for field in additive_fields:
            if field in update_state:
                base_values = merged.get(field, [])
                update_values = update_state.get(field, [])
                merged[field] = base_values + update_values
        
        # 合并普通字段
        for key, value in update_state.items():
            if key not in additive_fields:
                merged[key] = value
        
        return merged
    
    @staticmethod
    def validate_state(state: Dict[str, Any], state_type: Type) -> List[str]:
        """验证状态
        
        Args:
            state: 要验证的状态
            state_type: 状态类型
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 基础验证
        if "messages" not in state:
            errors.append("缺少messages字段")
        
        # 类型特定验证
        # 由于 ReActState 和 PlanExecuteState 都是 Dict[str, Any] 的类型别名，
        # 我们需要使用不同的方式来区分它们
        # AgentState类型已弃用，统一使用WorkflowState
        
        elif state_type == WorkflowState:
            required_fields = ["workflow_id", "workflow_name", "input", "max_iterations"]
            for field in required_fields:
                if field not in state:
                    errors.append(f"缺少必需字段: {field}")
        
        elif state_type.__name__ == "ReActState" or "max_steps" in state or "thought" in state:
            # ReActState 类型或包含 ReAct 特定字段
            required_fields = ["workflow_id", "workflow_name", "input", "max_iterations", "max_steps"]
            for field in required_fields:
                if field not in state:
                    errors.append(f"缺少必需字段: {field}")
        
        elif state_type.__name__ == "PlanExecuteState" or "plan" in state or "step_results" in state:
            # PlanExecuteState 类型或包含 PlanExecute 特定字段
            required_fields = ["workflow_id", "workflow_name", "input", "max_iterations", "max_steps"]
            for field in required_fields:
                if field not in state:
                    errors.append(f"缺少必需字段: {field}")
        
        return errors