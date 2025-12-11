"""工作流管理器和验证模块

基于新架构原则，提供统一的工作流管理和验证功能。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.core.workflow.graph_entities import GraphConfig
from src.core.workflow.workflow import Workflow
from src.interfaces.workflow.core import (
    IWorkflow, IWorkflowManager, IWorkflowValidator, ValidationResult
)
from src.interfaces.state import IWorkflowState
from src.core.workflow.execution.executor import WorkflowExecutor
from src.core.workflow.core.builder import WorkflowBuilder

logger = get_logger(__name__)


class WorkflowValidator(IWorkflowValidator):
    """工作流验证器实现"""
    
    def __init__(self):
        """初始化工作流验证器"""
        self.logger = get_logger(f"{__name__}.WorkflowValidator")
    
    def validate(self, workflow: IWorkflow) -> ValidationResult:
        """验证工作流
        
        Args:
            workflow: 工作流实例
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], metadata={})
        
        try:
            # 基础验证
            self._validate_basic_properties(workflow, result)
            
            # 配置验证
            self._validate_config(workflow.config, result)
            
            # 结构验证
            self._validate_structure(workflow, result)
            
            # 记录验证结果
            self._log_validation_result(workflow.workflow_id, result)
            
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"验证过程中发生异常: {str(e)}")
            self.logger.error(f"工作流验证异常: {workflow.workflow_id}, 错误: {e}")
        
        return result
    
    def validate_config(self, config: GraphConfig) -> ValidationResult:
        """验证工作流配置
        
        Args:
            config: 工作流配置
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], metadata={})
        
        try:
            # 基础配置验证
            self._validate_config_basic(config, result)
            
            # 节点验证
            self._validate_config_nodes(config, result)
            
            # 边验证
            self._validate_config_edges(config, result)
            
            # 入口点验证
            self._validate_config_entry_point(config, result)
            
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"配置验证过程中发生异常: {str(e)}")
            self.logger.error(f"配置验证异常: {config.name}, 错误: {e}")
        
        return result
    
    def _validate_basic_properties(self, workflow: IWorkflow, result: ValidationResult) -> None:
        """验证基础属性"""
        if not workflow.workflow_id:
            result.is_valid = False
            result.errors.append("工作流ID不能为空")
        
        if not workflow.name:
            result.is_valid = False
            result.errors.append("工作流名称不能为空")
        
        if not workflow.version:
            result.warnings.append("工作流版本未设置，使用默认版本")
    
    def _validate_config(self, config: GraphConfig, result: ValidationResult) -> None:
        """验证配置"""
        if not config:
            result.is_valid = False
            result.errors.append("工作流配置不能为空")
            return
        
        # 验证配置名称
        if not hasattr(config, 'name') or not config.name:
            result.is_valid = False
            result.errors.append("配置名称不能为空")
    
    def _validate_structure(self, workflow: IWorkflow, result: ValidationResult) -> None:
        """验证工作流结构"""
        nodes = workflow.get_nodes()
        edges = workflow.get_edges()
        
        if not nodes:
            result.is_valid = False
            result.errors.append("工作流必须包含至少一个节点")
        
        if not edges:
            result.warnings.append("工作流没有定义边，可能无法正常执行")
        
        # 验证入口点
        if workflow.entry_point and workflow.entry_point not in nodes:
            result.is_valid = False
            result.errors.append(f"入口点节点 '{workflow.entry_point}' 不存在")
    
    def _validate_config_basic(self, config: GraphConfig, result: ValidationResult) -> None:
        """验证基础配置"""
        if not hasattr(config, 'name') or not config.name:
            result.is_valid = False
            result.errors.append("配置名称不能为空")
    
    def _validate_config_nodes(self, config: GraphConfig, result: ValidationResult) -> None:
        """验证节点配置"""
        if not hasattr(config, 'nodes') or not config.nodes:
            result.is_valid = False
            result.errors.append("配置必须包含节点定义")
            return
        
        for node_name, node_config in config.nodes.items():
            if not node_config:
                result.is_valid = False
                result.errors.append(f"节点 '{node_name}' 配置不能为空")
            
            # 验证节点必需字段
            if hasattr(node_config, 'function_name') and not node_config.function_name:
                result.errors.append(f"节点 '{node_name}' 缺少函数定义")
    
    def _validate_config_edges(self, config: GraphConfig, result: ValidationResult) -> None:
        """验证边配置"""
        if not hasattr(config, 'edges') or not config.edges:
            result.warnings.append("配置没有定义边")
            return
        
        node_names = set(config.nodes.keys()) if hasattr(config, 'nodes') else set()
        
        for i, edge in enumerate(config.edges):
            if not edge:
                result.errors.append(f"边 {i} 配置不能为空")
                continue
            
            # 验证边的节点引用
            from_node = getattr(edge, 'from_node', None)
            to_node = getattr(edge, 'to_node', None)
            
            if from_node and from_node not in node_names:
                result.errors.append(f"边 {i} 的源节点 '{from_node}' 不存在")
            
            if to_node and to_node not in node_names:
                result.errors.append(f"边 {i} 的目标节点 '{to_node}' 不存在")
    
    def _validate_config_entry_point(self, config: GraphConfig, result: ValidationResult) -> None:
        """验证入口点配置"""
        if not hasattr(config, 'entry_point') or not config.entry_point:
            result.warnings.append("配置未指定入口点")
            return
        
        node_names = set(config.nodes.keys()) if hasattr(config, 'nodes') else set()
        
        if config.entry_point not in node_names:
            result.is_valid = False
            result.errors.append(f"入口点节点 '{config.entry_point}' 不存在")
    
    def _log_validation_result(self, workflow_id: str, result: ValidationResult) -> None:
        """记录验证结果"""
        if result.is_valid:
            self.logger.debug(f"工作流验证通过: {workflow_id}")
        else:
            self.logger.error(f"工作流验证失败: {workflow_id}")
            for error in result.errors:
                self.logger.error(f"  错误: {error}")
        
        for warning in result.warnings:
            self.logger.warning(f"  警告: {warning}")


class WorkflowManager(IWorkflowManager):
    """工作流管理器实现 - 统一管理工作流生命周期"""
    
    def __init__(
        self,
        executor: Optional[WorkflowExecutor] = None,
        builder: Optional[WorkflowBuilder] = None,
        validator: Optional[WorkflowValidator] = None
    ):
        """初始化工作流管理器
        
        Args:
            executor: 工作流执行器
            builder: 工作流构建器
            validator: 工作流验证器
        """
        self.executor = executor or WorkflowExecutor()
        self.builder = builder or WorkflowBuilder()
        self.validator = validator or WorkflowValidator()
        self.logger = get_logger(f"{__name__}.WorkflowManager")
        
        # 工作流状态跟踪
        self._workflow_status: Dict[str, Dict[str, Any]] = {}
        
        self.logger.debug("工作流管理器初始化完成")
    
    def create_workflow(self, config: GraphConfig) -> IWorkflow:
        """创建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            IWorkflow: 工作流实例
        """
        try:
            self.logger.debug(f"创建工作流: {config.name}")
            
            # 创建工作流实例
            workflow = Workflow(config)
            
            # 验证工作流
            validation_result = self.validate_workflow(workflow)
            if not validation_result.is_valid:
                error_msg = f"工作流验证失败: {'; '.join(validation_result.errors)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 记录工作流状态
            self._workflow_status[workflow.workflow_id] = {
                "status": "created",
                "created_at": datetime.now(),
                "last_updated": datetime.now(),
                "validation_result": validation_result.metadata
            }
            
            self.logger.info(f"工作流创建成功: {workflow.workflow_id}")
            return workflow
            
        except Exception as e:
            self.logger.error(f"创建工作流失败: {config.name}, 错误: {e}")
            raise
    
    def execute_workflow(
        self, 
        workflow: IWorkflow, 
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        try:
            self.logger.debug(f"开始执行工作流: {workflow.workflow_id}")
            
            # 更新工作流状态
            self._update_workflow_status(workflow.workflow_id, "executing")
            
            # 验证工作流
            validation_result = self.validate_workflow(workflow)
            if not validation_result.is_valid:
                error_msg = f"工作流验证失败: {'; '.join(validation_result.errors)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 编译工作流
            self.compile_workflow(workflow)
            
            # 执行工作流
            result_state = self.executor.execute(workflow, initial_state, context)
            
            # 更新工作流状态
            self._update_workflow_status(workflow.workflow_id, "completed")
            
            self.logger.info(f"工作流执行完成: {workflow.workflow_id}")
            return result_state
            
        except Exception as e:
            self._update_workflow_status(workflow.workflow_id, "failed")
            self.logger.error(f"工作流执行失败: {workflow.workflow_id}, 错误: {e}")
            raise
    
    async def execute_workflow_async(
        self, 
        workflow: IWorkflow, 
        initial_state: IWorkflowState,
        context: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        try:
            self.logger.debug(f"开始异步执行工作流: {workflow.workflow_id}")
            
            # 更新工作流状态
            self._update_workflow_status(workflow.workflow_id, "executing")
            
            # 验证工作流
            validation_result = self.validate_workflow(workflow)
            if not validation_result.is_valid:
                error_msg = f"工作流验证失败: {'; '.join(validation_result.errors)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 编译工作流
            self.compile_workflow(workflow)
            
            # 异步执行工作流
            result_state = await self.executor.execute_async(workflow, initial_state, context)
            
            # 更新工作流状态
            self._update_workflow_status(workflow.workflow_id, "completed")
            
            self.logger.info(f"工作流异步执行完成: {workflow.workflow_id}")
            return result_state
            
        except Exception as e:
            self._update_workflow_status(workflow.workflow_id, "failed")
            self.logger.error(f"工作流异步执行失败: {workflow.workflow_id}, 错误: {e}")
            raise
    
    def validate_workflow(self, workflow: IWorkflow) -> ValidationResult:
        """验证工作流
        
        Args:
            workflow: 工作流实例
            
        Returns:
            ValidationResult: 验证结果
        """
        return self.validator.validate(workflow)
    
    def compile_workflow(self, workflow: IWorkflow) -> None:
        """编译工作流
        
        Args:
            workflow: 工作流实例
        """
        try:
            if not workflow.compiled_graph:
                self.logger.debug(f"编译工作流图: {workflow.workflow_id}")
                self.builder.build_and_set_graph(workflow)
                self.logger.debug(f"工作流图编译完成: {workflow.workflow_id}")
        except Exception as e:
            self.logger.error(f"工作流图编译失败: {workflow.workflow_id}, 错误: {e}")
            raise
    
    def get_workflow_status(self, workflow: IWorkflow) -> Dict[str, Any]:
        """获取工作流状态
        
        Args:
            workflow: 工作流实例
            
        Returns:
            Dict[str, Any]: 工作流状态信息
        """
        status_info = self._workflow_status.get(workflow.workflow_id, {
            "status": "unknown",
            "created_at": None,
            "last_updated": None
        })
        
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "version": workflow.version,
            "status": status_info["status"],
            "created_at": status_info["created_at"],
            "last_updated": status_info["last_updated"],
            "has_compiled_graph": workflow.compiled_graph is not None,
            "node_count": len(workflow.get_nodes()),
            "edge_count": len(workflow.get_edges()),
            "entry_point": workflow.entry_point
        }
    
    def _update_workflow_status(self, workflow_id: str, status: str) -> None:
        """更新工作流状态
        
        Args:
            workflow_id: 工作流ID
            status: 新状态
        """
        if workflow_id in self._workflow_status:
            self._workflow_status[workflow_id]["status"] = status
            self._workflow_status[workflow_id]["last_updated"] = datetime.now()


# 创建默认实例
default_workflow_manager = WorkflowManager()
default_validator = WorkflowValidator()


def get_workflow_manager() -> WorkflowManager:
    """获取默认工作流管理器实例
    
    Returns:
        WorkflowManager: 工作流管理器实例
    """
    return default_workflow_manager


def get_workflow_validator() -> WorkflowValidator:
    """获取默认工作流验证器实例
    
    Returns:
        WorkflowValidator: 工作流验证器实例
    """
    return default_validator