"""工作流执行服务

提供统一的工作流执行接口，避免Core层之间的循环依赖。
此服务作为Core层执行器和外部接口之间的适配层。
"""

from typing import Dict, Any, Optional, AsyncGenerator
from src.interfaces.dependency_injection import get_logger
from datetime import datetime

from src.interfaces.workflow.core import IWorkflow, IWorkflowState
from src.core.workflow.execution.executor import WorkflowExecutor
from src.core.state.implementations.workflow_state import WorkflowState
from src.interfaces.workflow.services import IWorkflowExecutor as ServiceIWorkflowExecutor
from src.interfaces.workflow.core import IWorkflowRegistry

logger = get_logger(__name__)


class WorkflowExecutionService(ServiceIWorkflowExecutor):
    """工作流执行服务
    
    提供统一的工作流执行接口，封装Core层的执行器，
    避免Core层之间的循环依赖。
    """
    
    def __init__(self,
                 workflow_registry: Optional[IWorkflowRegistry] = None,
                 enable_streaming: bool = True,
                 enable_async: bool = True):
        """初始化工作流执行服务
        
        Args:
            workflow_registry: 工作流注册表（通过依赖注入提供）
            enable_streaming: 是否启用流式执行
            enable_async: 是否启用异步执行
        """
        self.workflow_registry = workflow_registry
        self.enable_streaming = enable_streaming
        self.enable_async = enable_async
        
        # 初始化Core层执行器
        self._sync_executor = WorkflowExecutor()
        
        logger.debug("工作流执行服务初始化完成")
    
    def execute(self,
                workflow: IWorkflow,
                initial_state: Optional[IWorkflowState] = None,
                config: Optional[Dict[str, Any]] = None) -> IWorkflowState:
        """同步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            执行结果状态
        """
        start_time = datetime.now()
        
        try:
            # 准备初始状态
            prepared_state = self._prepare_initial_state(initial_state, config)
            
            logger.info(f"开始执行工作流: {workflow.name}")
            
            # 这里应该调用实际的执行逻辑
            # 由于execute()方法现在在services层，具体实现需要根据架构调整
            result_state = prepared_state
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"工作流执行完成: {workflow.name}, 耗时: {execution_time:.3f}s")
            
            return result_state
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"工作流执行失败: {workflow.name}, 错误: {e}, 耗时: {execution_time:.3f}s")
            raise
    
    async def execute_async(self,
                           workflow: IWorkflow,
                           initial_state: Optional[IWorkflowState] = None,
                           config: Optional[Dict[str, Any]] = None) -> IWorkflowState:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            执行结果状态
        """
        if not self.enable_async:
            raise RuntimeError("异步执行未启用")
        
        start_time = datetime.now()
        
        try:
            # 准备初始状态
            prepared_state = self._prepare_initial_state(initial_state, config)
            
            logger.info(f"开始异步执行工作流: {workflow.name}")
            
            # 这里应该调用实际的异步执行逻辑
            result_state = prepared_state
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"工作流异步执行完成: {workflow.name}, 耗时: {execution_time:.3f}s")
            
            return result_state
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"工作流异步执行失败: {workflow.name}, 错误: {e}, 耗时: {execution_time:.3f}s")
            raise
    
    async def execute_stream(self,
                            workflow: IWorkflow,
                            initial_state: Optional[IWorkflowState] = None,
                            config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            config: 执行配置
            
        Yields:
            执行事件字典
        """
        if not self.enable_streaming:
            raise RuntimeError("流式执行未启用")
        
        start_time = datetime.now()
        
        try:
            # 准备初始状态
            prepared_state = self._prepare_initial_state(initial_state, config)
            
            logger.info(f"开始流式执行工作流: {workflow.name}")
            
            # 这里应该调用实际的流式执行逻辑
            # 暂时不yield任何内容
            if False:
                yield
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"工作流流式执行完成: {workflow.name}, 耗时: {execution_time:.3f}s")
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"工作流流式执行失败: {workflow.name}, 错误: {e}, 耗时: {execution_time:.3f}s")
            raise
    
    def get_execution_count(self, workflow_id: str) -> int:
        """获取工作流的执行次数
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            执行次数
        """
        # 这里可以实现执行计数逻辑
        # 暂时返回0，实际实现中可以使用持久化存储
        return 0
    
    def _prepare_initial_state(self,
                              initial_state: Optional[IWorkflowState],
                              config: Optional[Dict[str, Any]]) -> IWorkflowState:
        """准备初始状态
        
        Args:
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            准备后的初始状态
        """
        if initial_state:
            return initial_state
        
        # 如果没有提供初始状态，创建默认状态
        if config and "initial_data" in config:
            return WorkflowState.from_dict(config["initial_data"])
        
        # 创建空的初始状态
        return WorkflowState(
            workflow_id="unknown"
        )


class WorkflowInstanceExecutor:
    """工作流实例执行器
    
    专门用于WorkflowInstance的执行，避免与Core层的直接依赖。
    """
    
    def __init__(self, execution_service: Optional[WorkflowExecutionService] = None):
        """初始化实例执行器
        
        Args:
            execution_service: 执行服务实例
        """
        self.execution_service = execution_service or WorkflowExecutionService()
    
    def execute_workflow_instance(self,
                                 compiled_graph: Any,
                                 config: Any,
                                 initial_data: Optional[Dict[str, Any]] = None,
                                 **kwargs: Any) -> Dict[str, Any]:
        """执行工作流实例
        
        Args:
            compiled_graph: 编译后的图
            config: 工作流配置
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        start_time = datetime.now()
        
        try:
            # 创建初始状态
            initial_state = self._create_initial_state(initial_data)
            
            # 准备运行配置
            run_config = self._prepare_run_config(kwargs)
            
            logger.info(f"开始执行工作流实例: {config.name}")
            
            # 直接使用编译后的图执行
            if hasattr(compiled_graph, 'invoke'):
                result: Dict[str, Any] = compiled_graph.invoke(initial_state, config=run_config)
            else:
                raise ValueError("编译后的图不支持invoke方法")
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            result["_execution_time"] = execution_time
            
            logger.info(f"工作流实例执行完成: {config.name}, 耗时: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"工作流实例执行失败: {config.name}, 错误: {e}, 耗时: {execution_time:.3f}s")
            raise
    
    async def execute_workflow_instance_async(self,
                                             compiled_graph: Any,
                                             config: Any,
                                             initial_data: Optional[Dict[str, Any]] = None,
                                             **kwargs: Any) -> Dict[str, Any]:
        """异步执行工作流实例
        
        Args:
            compiled_graph: 编译后的图
            config: 工作流配置
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        start_time = datetime.now()
        result: Dict[str, Any] = {}
        
        try:
            # 创建初始状态
            initial_state = self._create_initial_state(initial_data)
            
            # 准备运行配置
            run_config = self._prepare_run_config(kwargs)
            
            logger.info(f"开始异步执行工作流实例: {config.name}")
            
            # 直接使用编译后的图执行
            if hasattr(compiled_graph, 'ainvoke'):
                result = await compiled_graph.ainvoke(initial_state, config=run_config)
            else:
                # 如果不支持异步，使用同步方式
                logger.warning("图不支持异步执行，使用同步方式")
                result = compiled_graph.invoke(initial_state, config=run_config)
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            result["_execution_time"] = execution_time
            result["_execution_mode"] = "async"
            
            logger.info(f"工作流实例异步执行完成: {config.name}, 耗时: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"工作流实例异步执行失败: {config.name}, 错误: {e}, 耗时: {execution_time:.3f}s")
            raise
    
    def _create_initial_state(self, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建初始状态
        
        Args:
            initial_data: 初始数据
            
        Returns:
            初始状态字典
        """
        if initial_data:
            return initial_data.copy()
        else:
            return {}
    
    def _prepare_run_config(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """准备运行配置
        
        Args:
            kwargs: 运行参数
            
        Returns:
            运行配置
        """
        run_config = {}
        
        # 设置递归限制
        if "recursion_limit" not in kwargs:
            run_config["recursion_limit"] = kwargs.get("recursion_limit", 10)
        
        # 添加其他配置
        for key, value in kwargs.items():
            if not key.startswith('_'):
                run_config[key] = value
        
        return run_config
