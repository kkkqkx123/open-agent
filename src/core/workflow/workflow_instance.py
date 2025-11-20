"""工作流实例 - 重构后实现

封装已编译的图和配置，提供统一的执行接口。
使用Services层组件，避免循环依赖。
"""

from typing import Dict, Any, Optional, Generator, AsyncIterator, List
from datetime import datetime
import logging
import asyncio

from src.core.workflow.config.config import GraphConfig
from src.core.workflow.state_machine.state_templates import StateTemplateManager
from src.core.workflow.interfaces import IWorkflow, IWorkflowState
from src.core.workflow.entities import WorkflowState, ExecutionResult
from src.core.workflow.exceptions import WorkflowExecutionError, WorkflowStateError

logger = logging.getLogger(__name__)


class WorkflowInstance:
    """工作流实例 - 重构后实现
    
    封装已编译的图和配置，提供统一的执行接口。
    使用Services层组件，避免循环依赖。
    """
    
    def __init__(
        self,
        config: GraphConfig,
        compiled_graph: Optional[Any] = None,  # LangGraph 编译后的图
        state_template_manager: Optional[StateTemplateManager] = None,
        use_services_layer: bool = True
    ):
        """初始化工作流实例
        
        Args:
            config: 工作流配置
            compiled_graph: LangGraph 编译后的图（可选，如果不提供将通过Services层构建）
            state_template_manager: 状态模板管理器
            use_services_layer: 是否使用Services层（默认True）
        """
        self.config = config
        self.state_template_manager = state_template_manager or StateTemplateManager()
        self._created_at = datetime.now()
        self.use_services_layer = use_services_layer
        
        # 初始化Services层组件
        if use_services_layer:
            self._init_services_layer()
            # 通过Services层构建图
            self.compiled_graph = self._build_graph_via_services()
        else:
            # 直接使用提供的编译图
            if compiled_graph is None:
                raise WorkflowExecutionError("不使用Services层时必须提供compiled_graph")
            self.compiled_graph = compiled_graph
        
        # 验证图是否已编译
        if not hasattr(self.compiled_graph, 'invoke'):
            raise WorkflowExecutionError("提供的图未正确编译，缺少 invoke 方法")
        
        logger.debug(f"工作流实例初始化完成: {config.name}")
    
    def _init_services_layer(self):
        """初始化Services层组件"""
        try:
            # 延迟导入避免循环依赖
            from src.services.workflow.building.builder_service import WorkflowBuilderService
            from src.services.workflow.execution_service import WorkflowInstanceExecutor
            
            self._builder_service = WorkflowBuilderService()
            self._instance_executor = WorkflowInstanceExecutor()
            
            logger.debug("Services层组件初始化完成")
            
        except ImportError as e:
            logger.error(f"无法导入Services层组件: {e}")
            raise WorkflowExecutionError(f"Services层组件不可用: {e}")
    
    def _build_graph_via_services(self) -> Any:
        """通过Services层构建图
        
        Returns:
            编译后的图
        """
        try:
            # 使用Services层的构建服务
            workflow = self._builder_service.build_workflow(self.config.to_dict())
            return workflow.get_graph()
            
        except Exception as e:
            logger.error(f"通过Services层构建图失败: {e}")
            raise WorkflowExecutionError(f"图构建失败: {e}") from e
    
    def run(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """运行工作流 - 使用Services层执行器
        
        Args:
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        if self.use_services_layer and hasattr(self, '_instance_executor'):
            # 使用Services层的实例执行器
            return self._instance_executor.execute_workflow_instance(
                self.compiled_graph,
                self.config,
                initial_data,
                **kwargs
            )
        else:
            # 回退到直接执行
            return self._run_direct(initial_data, **kwargs)
    
    async def run_async(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """异步运行工作流 - 使用Services层执行器
        
        Args:
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        if self.use_services_layer and hasattr(self, '_instance_executor'):
            # 使用Services层的实例执行器
            return await self._instance_executor.execute_workflow_instance_async(
                self.compiled_graph,
                self.config,
                initial_data,
                **kwargs
            )
        else:
            # 回退到直接执行
            return await self._run_direct_async(initial_data, **kwargs)
    
    def _run_direct(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """直接运行工作流 - 回退实现
        
        Args:
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 创建初始状态
            initial_state = self._create_initial_state(initial_data)
            
            # 准备运行配置
            run_config = self._prepare_run_config(kwargs)
            
            # 执行工作流
            logger.info(f"开始执行工作流: {self.config.name}")
            result: Dict[str, Any] = self.compiled_graph.invoke(initial_state, config=run_config)
            logger.info(f"工作流执行完成: {self.config.name}")
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            result["_execution_time"] = execution_time
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"工作流执行失败: {self.config.name}, 错误: {e}")
            
            # 包装异常
            raise WorkflowExecutionError(
                f"工作流执行失败: {e}"
            ) from e
    
    async def _run_direct_async(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """直接异步运行工作流 - 回退实现
        
        Args:
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 创建初始状态
            initial_state = self._create_initial_state(initial_data)
            
            # 准备运行配置
            run_config = self._prepare_run_config(kwargs)
            
            # 异步执行工作流
            logger.info(f"开始异步执行工作流: {self.config.name}")
            
            if hasattr(self.compiled_graph, 'ainvoke'):
                result: Dict[str, Any] = await self.compiled_graph.ainvoke(initial_state, config=run_config)
            else:
                # 如果不支持异步，使用同步方式
                logger.warning("图不支持异步执行，使用同步方式")
                result = self.compiled_graph.invoke(initial_state, config=run_config)
            
            logger.info(f"工作流异步执行完成: {self.config.name}")
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            result["_execution_time"] = execution_time
            result["_execution_mode"] = "async"
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"工作流异步执行失败: {self.config.name}, 错误: {e}")
            
            # 包装异常
            raise WorkflowExecutionError(
                f"工作流异步执行失败: {e}"
            ) from e
    
    def stream(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Generator[Dict[str, Any], None, None]:
        """流式运行工作流 - 使用 compiled_graph.stream()
        
        Args:
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Yields:
            Dict[str, Any]: 中间状态
        """
        start_time = datetime.now()
        
        try:
            # 创建初始状态
            initial_state = self._create_initial_state(initial_data)
            
            # 准备运行配置
            run_config = self._prepare_run_config(kwargs)
            
            # 流式执行工作流
            logger.info(f"开始流式执行工作流: {self.config.name}")
            
            if hasattr(self.compiled_graph, 'stream'):
                for chunk in self.compiled_graph.stream(initial_state, config=run_config):
                    # 添加元数据
                    if isinstance(chunk, dict):
                        chunk["_timestamp"] = datetime.now().isoformat()
                        chunk["_workflow_name"] = self.config.name
                    yield chunk
            else:
                # 如果不支持流式，直接返回最终结果
                logger.warning("图不支持流式执行，返回最终结果")
                result = self.compiled_graph.invoke(initial_state, config=run_config)
                result["_timestamp"] = datetime.now().isoformat()
                result["_workflow_name"] = self.config.name
                yield result
            
            logger.info(f"工作流流式执行完成: {self.config.name}")
            
        except Exception as e:
            logger.error(f"工作流流式执行失败: {self.config.name}, 错误: {e}")
            
            # 包装异常
            raise WorkflowExecutionError(
                f"工作流流式执行失败: {e}"
            ) from e
    
    async def stream_async(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步流式运行工作流 - 使用 compiled_graph.astream()
        
        Args:
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Yields:
            Dict[str, Any]: 中间状态
        """
        start_time = datetime.now()
        
        try:
            # 创建初始状态
            initial_state = self._create_initial_state(initial_data)
            
            # 准备运行配置
            run_config = self._prepare_run_config(kwargs)
            
            # 异步流式执行工作流
            logger.info(f"开始异步流式执行工作流: {self.config.name}")
            
            if hasattr(self.compiled_graph, 'astream'):
                async for chunk in self.compiled_graph.astream(initial_state, config=run_config):
                    # 添加元数据
                    if isinstance(chunk, dict):
                        chunk["_timestamp"] = datetime.now().isoformat()
                        chunk["_workflow_name"] = self.config.name
                        chunk["_execution_mode"] = "async_stream"
                    yield chunk
            else:
                # 如果不支持异步流式，使用同步流式
                logger.warning("图不支持异步流式执行，使用同步流式")
                for chunk in self.stream(initial_data, **kwargs):
                    yield chunk
            
            logger.info(f"工作流异步流式执行完成: {self.config.name}")
            
        except Exception as e:
            logger.error(f"工作流异步流式执行失败: {self.config.name}, 错误: {e}")
            
            # 包装异常
            raise WorkflowExecutionError(
                f"工作流异步流式执行失败: {e}"
            ) from e
    
    def get_config(self) -> GraphConfig:
        """获取工作流配置
        
        Returns:
            GraphConfig: 工作流配置
        """
        return self.config
    
    def get_visualization(self) -> Dict[str, Any]:
        """获取工作流可视化数据
        
        Returns:
            Dict[str, Any]: 可视化数据
        """
        return {
            "name": self.config.name,
            "description": self.config.description,
            "version": getattr(self.config, 'version', '1.0.0'),
            "created_at": self._created_at.isoformat(),
            "nodes": [
                {
                    "id": node_id,
                    "type": node.function_name,
                    "config": node.config,
                    "description": node.description
                }
                for node_id, node in self.config.nodes.items()
            ],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "type": edge.type.value,
                    "condition": edge.condition,
                    "description": edge.description
                }
                for edge in self.config.edges
            ],
            "entry_point": self.config.entry_point,
            "state_schema": self._get_state_schema_info(),
            "metadata": {
                "graph_type": type(self.compiled_graph).__name__,
                "supports_async": hasattr(self.compiled_graph, 'ainvoke'),
                "supports_stream": hasattr(self.compiled_graph, 'stream'),
                "supports_async_stream": hasattr(self.compiled_graph, 'astream')
            }
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取工作流元数据
        
        Returns:
            Dict[str, Any]: 元数据
        """
        return {
            "name": self.config.name,
            "description": self.config.description,
            "version": getattr(self.config, 'version', '1.0.0'),
            "created_at": self._created_at.isoformat(),
            "config": {
                "node_count": len(self.config.nodes),
                "edge_count": len(self.config.edges),
                "entry_point": self.config.entry_point,
                "has_state_schema": hasattr(self.config, 'state_schema') and self.config.state_schema is not None
            },
            "capabilities": {
                "supports_async": hasattr(self.compiled_graph, 'ainvoke'),
                "supports_stream": hasattr(self.compiled_graph, 'stream'),
                "supports_async_stream": hasattr(self.compiled_graph, 'astream')
            }
        }
    
    def _create_initial_state(self, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建初始状态
        
        Args:
            initial_data: 初始数据
            
        Returns:
            Dict[str, Any]: 初始状态
        """
        try:
            # 直接使用初始数据，避免复杂的类型转换
            if initial_data:
                return initial_data.copy()
            else:
                return {}
        except Exception as e:
            logger.warning(f"创建初始状态失败: {e}，使用初始数据")
            return initial_data or {}
    
    def _prepare_run_config(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """准备运行配置
        
        Args:
            kwargs: 运行参数
            
        Returns:
            Dict[str, Any]: 运行配置
        """
        run_config = {}
        
        # 设置递归限制
        if "recursion_limit" not in kwargs:
            recursion_limit = getattr(self.config, 'recursion_limit', None)
            if recursion_limit is None and hasattr(self.config, 'additional_config'):
                recursion_limit = self.config.additional_config.get("recursion_limit", 10)
            run_config["recursion_limit"] = recursion_limit or 10
        
        # 添加其他配置
        for key, value in kwargs.items():
            if not key.startswith('_'):
                run_config[key] = value
        
        return run_config
    
    def _get_state_schema_info(self) -> Optional[Dict[str, Any]]:
        """获取状态模式信息
        
        Returns:
            Optional[Dict[str, Any]]: 状态模式信息
        """
        if not hasattr(self.config, 'state_schema') or not self.config.state_schema:
            return None
        
        state_schema = self.config.state_schema
        return {
            "fields": list(state_schema.fields.keys()) if hasattr(state_schema, 'fields') else [],
            "field_count": len(state_schema.fields) if hasattr(state_schema, 'fields') else 0,
            "template": getattr(self.config, 'state_template', None)
        }
    
    def validate(self) -> List[str]:
        """验证工作流实例
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查图是否已编译
        if not hasattr(self.compiled_graph, 'invoke'):
            errors.append("图未正确编译，缺少 invoke 方法")
        
        # 检查配置
        if not self.config.name:
            errors.append("工作流名称不能为空")
        
        if not self.config.nodes:
            errors.append("工作流必须至少包含一个节点")
        
        if not self.config.entry_point:
            errors.append("工作流必须指定入口点")
        
        # 检查入口点是否存在
        if self.config.entry_point and self.config.entry_point not in self.config.nodes:
            if self.config.entry_point not in ["__start__", "__end__"]:
                errors.append(f"入口节点不存在: {self.config.entry_point}")
        
        return errors
    
    def __repr__(self) -> str:
        """字符串表示
        
        Returns:
            str: 字符串表示
        """
        return f"WorkflowInstance(name={self.config.name}, nodes={len(self.config.nodes)}, edges={len(self.config.edges)})"