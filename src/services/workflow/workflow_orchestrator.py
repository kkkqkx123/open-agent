"""工作流编排器

在 services 层负责业务逻辑协调，与 workflow 层的执行逻辑分离。
"""

from typing import Dict, Any, Optional, List

from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state.workflow import IWorkflowState
from src.interfaces.logger import ILogger
from src.core.workflow.graph_entities import GraphConfig
from src.core.workflow.workflow import Workflow


class WorkflowOrchestrator:
    """工作流编排器 - 顶层业务协调
    
    负责业务逻辑处理，与 workflow 层的执行逻辑分离。
    """
    
    def __init__(self, workflow_coordinator: IWorkflowCoordinator, logger: Optional[ILogger] = None):
        """初始化工作流编排器
        
        Args:
            workflow_coordinator: 工作流协调器
            logger: 日志记录器
        """
        self._workflow_coordinator = workflow_coordinator
        self._logger = logger
    
    def orchestrate_workflow_execution(self, 
                                     workflow_config: Dict[str, Any],
                                     business_context: Dict[str, Any]) -> Dict[str, Any]:
        """编排工作流执行 - 包含业务逻辑
        
        Args:
            workflow_config: 工作流配置
            business_context: 业务上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 业务逻辑处理
            processed_config = self._process_business_rules(workflow_config, business_context)
            
            # 创建工作流配置
            config = GraphConfig.from_dict(processed_config)
            
            # 创建工作流
            workflow = self._workflow_coordinator.create_workflow(config)
            
            # 创建初始状态
            initial_state = self._create_initial_state(business_context)
            
            # 执行工作流
            result_state = self._workflow_coordinator.execute_workflow(workflow, initial_state)
            
            # 业务结果处理
            return self._process_business_result(result_state, business_context)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"编排工作流执行失败: {e}")
            raise
    
    def create_workflow_with_business_logic(self, 
                                          workflow_config: Dict[str, Any],
                                          business_context: Dict[str, Any]) -> IWorkflow:
        """创建工作流 - 包含业务逻辑
        
        Args:
            workflow_config: 工作流配置
            business_context: 业务上下文
            
        Returns:
            IWorkflow: 工作流实例
        """
        try:
            # 业务逻辑处理
            processed_config = self._process_business_rules(workflow_config, business_context)
            
            # 创建工作流配置
            config = GraphConfig.from_dict(processed_config)
            
            # 创建工作流
            workflow = self._workflow_coordinator.create_workflow(config)
            
            if self._logger:
                self._logger.info(f"成功创建工作流: {workflow.name}")
            return workflow

        except Exception as e:
            if self._logger:
                self._logger.error(f"创建工作流失败: {e}")
            raise
    
    def execute_workflow_with_business_logic(self,
                                           workflow: IWorkflow,
                                           business_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流 - 包含业务逻辑
        
        Args:
            workflow: 工作流实例
            business_context: 业务上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 创建初始状态
            initial_state = self._create_initial_state(business_context)
            
            # 执行工作流
            result_state = self._workflow_coordinator.execute_workflow(workflow, initial_state)
            
            # 业务结果处理
            return self._process_business_result(result_state, business_context)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"执行工作流失败: {e}")
            raise
    
    def validate_workflow_with_business_rules(self,
                                             workflow_config: Dict[str, Any],
                                             business_context: Dict[str, Any]) -> List[str]:
        """验证工作流配置 - 包含业务规则
        
        Args:
            workflow_config: 工作流配置
            business_context: 业务上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        try:
            # 业务规则验证
            business_errors = self._validate_business_rules(workflow_config, business_context)
            errors.extend(business_errors)
            
            # 基础配置验证
            processed_config = self._process_business_rules(workflow_config, business_context)
            config = GraphConfig.from_dict(processed_config)
            
            # 使用协调器验证配置
            validation_errors = self._workflow_coordinator.validate_workflow_config(config)
            errors.extend(validation_errors)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"验证工作流配置失败: {e}")
            errors.append(f"配置验证失败: {str(e)}")
        
        return errors
    
    def _process_business_rules(self, 
                               workflow_config: Dict[str, Any], 
                               business_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理业务规则
        
        Args:
            workflow_config: 原始工作流配置
            business_context: 业务上下文
            
        Returns:
            Dict[str, Any]: 处理后的配置
        """
        processed_config = workflow_config.copy()
        
        # 应用业务规则
        if business_context.get("environment") == "production":
            # 生产环境的业务规则
            processed_config.setdefault("max_iterations", 100)
            processed_config.setdefault("timeout", 3600)
        elif business_context.get("environment") == "development":
            # 开发环境的业务规则
            processed_config.setdefault("max_iterations", 10)
            processed_config.setdefault("timeout", 300)
        
        # 应用用户权限
        if business_context.get("user_role") == "guest":
            # 访客用户的限制
            processed_config.setdefault("restricted_mode", True)
        
        # 应用业务上下文变量
        context_vars = business_context.get("variables", {})
        if context_vars:
            processed_config.setdefault("context_variables", context_vars)
        
            if self._logger:
                self._logger.debug(f"业务规则处理完成，环境: {business_context.get('environment')}")
        return processed_config
    
    def _validate_business_rules(self,
                                workflow_config: Dict[str, Any],
                                business_context: Dict[str, Any]) -> List[str]:
        """验证业务规则
        
        Args:
            workflow_config: 工作流配置
            business_context: 业务上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证必需的业务上下文
        required_context_keys = ["environment", "user_id"]
        for key in required_context_keys:
            if key not in business_context:
                errors.append(f"缺少必需的业务上下文: {key}")
        
        # 验证工作流配置的业务规则
        if business_context.get("user_role") == "guest":
            # 访客用户不能执行某些类型的工作流
            restricted_types = ["admin_workflow", "system_workflow"]
            workflow_type = workflow_config.get("type")
            if workflow_type in restricted_types:
                errors.append(f"访客用户不能执行 {workflow_type} 类型的工作流")
        
        # 验证资源限制
        if business_context.get("resource_limits"):
            limits = business_context["resource_limits"]
            max_nodes = limits.get("max_nodes", 50)
            node_count = len(workflow_config.get("nodes", {}))
            if node_count > max_nodes:
                errors.append(f"节点数量 {node_count} 超过限制 {max_nodes}")
        
        return errors
    
    def _create_initial_state(self, business_context: Dict[str, Any]) -> IWorkflowState:
        """创建初始状态
        
        Args:
            business_context: 业务上下文
            
        Returns:
            IWorkflowState: 初始状态
        """
        from src.core.state.implementations.workflow_state import WorkflowState
        
        # 创建基础状态
        state = WorkflowState(key="workflow_state")
        
        # 设置业务上下文
        state.set_data("business_context", business_context)
        state.set_data("user_id", business_context.get("user_id"))
        state.set_data("environment", business_context.get("environment"))
        state.set_data("user_role", business_context.get("user_role"))
        
        # 设置初始变量
        variables = business_context.get("variables", {})
        for key, value in variables.items():
            state.set_data(key, value)
        
            if self._logger:
                self._logger.debug(f"创建初始状态完成，用户: {business_context.get('user_id')}")
        return state
    
    def _process_business_result(self, 
                                result_state: IWorkflowState, 
                                business_context: Dict[str, Any]) -> Dict[str, Any]:
        """处理业务结果
        
        Args:
            result_state: 结果状态
            business_context: 业务上下文
            
        Returns:
            Dict[str, Any]: 处理后的结果
        """
        # 提取基础结果
        metadata_dict: Dict[str, Any] = {}
        if hasattr(result_state, '_metadata'):
            metadata_dict = getattr(result_state, '_metadata', {})
        
        result = {
            "success": True,
            "state_data": result_state.values,
            "execution_metadata": metadata_dict,
        }
        
        # 添加业务上下文信息
        result["business_context"] = {
            "user_id": business_context.get("user_id"),
            "environment": business_context.get("environment"),
            "execution_time": result_state.get_data("execution_time"),
        }
        
        # 根据业务规则处理结果
        if business_context.get("environment") == "production":
            # 生产环境的额外处理
            result["audit_info"] = {
                "timestamp": result_state.get_data("timestamp"),
                "user_id": business_context.get("user_id"),
                "workflow_id": result_state.get_data("workflow_id"),
            }
        
            if self._logger:
                self._logger.debug(f"业务结果处理完成，用户: {business_context.get('user_id')}")
        return result


# 便捷函数
def create_workflow_orchestrator(workflow_coordinator: IWorkflowCoordinator) -> WorkflowOrchestrator:
    """创建工作流编排器实例
    
    Args:
        workflow_coordinator: 工作流协调器
        
    Returns:
        WorkflowOrchestrator: 工作流编排器实例
    """
    return WorkflowOrchestrator(workflow_coordinator)


# 导出实现
__all__ = [
    "WorkflowOrchestrator",
    "create_workflow_orchestrator",
]