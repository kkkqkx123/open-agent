"""重构后的工作流管理器

专注于工作流生命周期管理，使用WorkflowFactory处理创建逻辑。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncGenerator, Generator
from pathlib import Path
import uuid
from datetime import datetime
import logging

from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states import WorkflowState, StateFactory
from src.infrastructure.config_loader import IConfigLoader
from src.infrastructure.container import IDependencyContainer
from .factory import IWorkflowFactory, WorkflowFactory
from .interfaces import IWorkflowManager

logger = logging.getLogger(__name__)


class WorkflowManager(IWorkflowManager):
    """重构后的工作流管理器
    
    专注于工作流生命周期管理，包括：
    - 工作流加载和卸载
    - 工作流执行和监控
    - 工作流元数据管理
    """
    
    def __init__(
        self,
        container: Optional[IDependencyContainer] = None,
        config_loader: Optional[IConfigLoader] = None,
        workflow_factory: Optional[IWorkflowFactory] = None
    ) -> None:
        """初始化工作流管理器
        
        Args:
            container: 依赖注入容器
            config_loader: 配置加载器
            workflow_factory: 工作流工厂
        """
        self.container = container
        self.config_loader = config_loader
        self.workflow_factory = workflow_factory or WorkflowFactory(container)
        
        # 工作流存储
        self._workflows: Dict[str, Any] = {}
        self._workflow_configs: Dict[str, WorkflowConfig] = {}
        self._workflow_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 执行统计
        self._execution_stats: Dict[str, Dict[str, Any]] = {}

    def load_workflow(self, config_path: str) -> str:
        """加载工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            str: 工作流ID
        """
        logger.info(f"加载工作流配置: {config_path}")
        
        try:
            # 使用工厂创建工作流
            workflow = self.workflow_factory.create_workflow_from_config(config_path)
            
            # 获取配置
            config = self.workflow_factory.builder_adapter.load_workflow_config(config_path)
            
            # 生成工作流ID
            workflow_id = self._generate_workflow_id(config.name)
            
            # 存储工作流
            self._workflows[workflow_id] = workflow
            self._workflow_configs[workflow_id] = config
            self._workflow_metadata[workflow_id] = {
                "name": config.name,
                "description": config.description,
                "version": config.version,
                "config_path": config_path,
                "loaded_at": datetime.now().isoformat(),
                "last_used": None,
                "usage_count": 0
            }
            
            # 初始化执行统计
            self._execution_stats[workflow_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_execution_time": 0.0,
                "last_execution_time": None
            }
            
            logger.info(f"工作流加载成功: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"加载工作流失败: {e}")
            raise

    def create_workflow(self, workflow_id: str) -> Any:
        """创建工作流实例
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Any: 工作流实例
        """
        if workflow_id not in self._workflows:
            raise ValueError(f"工作流 '{workflow_id}' 不存在")
        
        # 更新使用统计
        self._update_usage_stats(workflow_id)
        
        # 克隆工作流实例以避免状态污染
        workflow = self._workflows[workflow_id]
        return self.workflow_factory.clone_workflow(workflow)

    def run_workflow(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> WorkflowState:
        """运行工作流
        
        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            event_collector: 可选的事件收集器
            **kwargs: 其他参数
            
        Returns:
            WorkflowState: 最终状态
        """
        execution_start_time = datetime.now()
        
        try:
            # 创建工作流实例
            workflow = self.create_workflow(workflow_id)
            config = self._workflow_configs[workflow_id]
            
            # 准备初始状态
            if initial_state is None:
                initial_state = self.workflow_factory.create_workflow_state(
                    workflow_id=workflow_id,
                    workflow_name=config.name,
                    input_text=kwargs.get('input_text', ''),
                    workflow_config=config.additional_config,
                    max_iterations=config.additional_config.get('max_iterations', 10)
                )
            
            # 收集工作流开始事件
            if event_collector:
                event_collector.collect_workflow_start(config.name, config.to_dict())
            
            # 运行工作流
            result = workflow.invoke(initial_state, **kwargs)
            
            # 更新执行统计
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            self._update_execution_stats(workflow_id, True, execution_time)
            
            # 收集工作流结束事件
            if event_collector:
                event_collector.collect_workflow_end(
                    config.name, 
                    {"status": "success", "execution_time": execution_time}
                )
            
            logger.info(f"工作流执行成功: {workflow_id}, 耗时: {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            # 更新执行统计
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            self._update_execution_stats(workflow_id, False, execution_time)
            
            # 记录错误
            self._log_workflow_error(workflow_id, e)
            
            # 收集错误事件
            if event_collector:
                config = self._workflow_configs.get(workflow_id)
                if config:
                    event_collector.collect_error(
                        e, 
                        {"workflow_id": workflow_id, "workflow_name": config.name}
                    )
            
            logger.error(f"工作流执行失败: {workflow_id}, 错误: {e}")
            raise

    async def run_workflow_async(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> WorkflowState:
        """异步运行工作流
        
        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            event_collector: 可选的事件收集器
            **kwargs: 其他参数
            
        Returns:
            WorkflowState: 最终状态
        """
        execution_start_time = datetime.now()
        
        try:
            # 创建工作流实例
            workflow = self.create_workflow(workflow_id)
            config = self._workflow_configs[workflow_id]
            
            # 准备初始状态
            if initial_state is None:
                initial_state = self.workflow_factory.create_workflow_state(
                    workflow_id=workflow_id,
                    workflow_name=config.name,
                    input_text=kwargs.get('input_text', ''),
                    workflow_config=config.additional_config,
                    max_iterations=config.additional_config.get('max_iterations', 10)
                )
            
            # 收集工作流开始事件
            if event_collector:
                event_collector.collect_workflow_start(config.name, config.to_dict())
            
            # 异步运行工作流
            if hasattr(workflow, 'ainvoke'):
                result = await workflow.ainvoke(initial_state, **kwargs)
            else:
                # 如果不支持异步，使用同步方式
                result = workflow.invoke(initial_state, **kwargs)
            
            # 更新执行统计
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            self._update_execution_stats(workflow_id, True, execution_time)
            
            # 收集工作流结束事件
            if event_collector:
                event_collector.collect_workflow_end(
                    config.name, 
                    {"status": "success", "execution_time": execution_time}
                )
            
            logger.info(f"工作流异步执行成功: {workflow_id}, 耗时: {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            # 更新执行统计
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            self._update_execution_stats(workflow_id, False, execution_time)
            
            # 记录错误
            self._log_workflow_error(workflow_id, e)
            
            # 收集错误事件
            if event_collector:
                config = self._workflow_configs.get(workflow_id)
                if config:
                    event_collector.collect_error(
                        e, 
                        {"workflow_id": workflow_id, "workflow_name": config.name}
                    )
            
            logger.error(f"工作流异步执行失败: {workflow_id}, 错误: {e}")
            raise

    def stream_workflow(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> Generator[WorkflowState, None, None]:
        """流式运行工作流
        
        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            event_collector: 可选的事件收集器
            **kwargs: 其他参数
            
        Yields:
            WorkflowState: 中间状态
        """
        execution_start_time = datetime.now()
        
        try:
            # 创建工作流实例
            workflow = self.create_workflow(workflow_id)
            config = self._workflow_configs[workflow_id]
            
            # 准备初始状态
            if initial_state is None:
                initial_state = self.workflow_factory.create_workflow_state(
                    workflow_id=workflow_id,
                    workflow_name=config.name,
                    input_text=kwargs.get('input_text', ''),
                    workflow_config=config.additional_config,
                    max_iterations=config.additional_config.get('max_iterations', 10)
                )
            
            # 收集工作流开始事件
            if event_collector:
                event_collector.collect_workflow_start(config.name, config.to_dict())
            
            # 流式运行工作流
            if hasattr(workflow, 'stream'):
                for chunk in workflow.stream(initial_state, **kwargs):
                    yield chunk
            else:
                # 如果不支持流式，直接返回最终结果
                result = workflow.invoke(initial_state, **kwargs)
                yield result
            
            # 更新执行统计
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            self._update_execution_stats(workflow_id, True, execution_time)
            
            # 收集工作流结束事件
            if event_collector:
                event_collector.collect_workflow_end(
                    config.name, 
                    {"status": "success", "execution_time": execution_time}
                )
            
            logger.info(f"工作流流式执行成功: {workflow_id}, 耗时: {execution_time:.2f}秒")
            
        except Exception as e:
            # 更新执行统计
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            self._update_execution_stats(workflow_id, False, execution_time)
            
            # 记录错误
            self._log_workflow_error(workflow_id, e)
            
            # 收集错误事件
            if event_collector:
                config = self._workflow_configs.get(workflow_id)
                if config:
                    event_collector.collect_error(
                        e, 
                        {"workflow_id": workflow_id, "workflow_name": config.name}
                    )
            
            logger.error(f"工作流流式执行失败: {workflow_id}, 错误: {e}")
            raise

    def list_workflows(self) -> List[str]:
        """列出所有已加载的工作流
        
        Returns:
            List[str]: 工作流ID列表
        """
        return list(self._workflows.keys())

    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[WorkflowConfig]: 工作流配置
        """
        return self._workflow_configs.get(workflow_id)

    def unload_workflow(self, workflow_id: str) -> bool:
        """卸载工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否成功卸载
        """
        if workflow_id not in self._workflows:
            return False
        
        # 移除工作流
        del self._workflows[workflow_id]
        del self._workflow_configs[workflow_id]
        del self._workflow_metadata[workflow_id]
        del self._execution_stats[workflow_id]
        
        logger.info(f"工作流卸载成功: {workflow_id}")
        return True

    def get_workflow_visualization(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流可视化数据
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Dict[str, Any]: 可视化数据
        """
        config = self.get_workflow_config(workflow_id)
        if not config:
            return {}
        
        # 转换配置为可视化数据
        return {
            "workflow_id": workflow_id,
            "name": config.name,
            "description": config.description,
            "version": config.version,
            "nodes": [
                {
                    "id": node_id,
                    "type": node.function_name,
                    "config": node.config,
                    "description": node.description
                }
                for node_id, node in config.nodes.items()
            ],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "type": edge.type.value,
                    "condition": edge.condition,
                    "description": edge.description
                }
                for edge in config.edges
            ],
            "entry_point": config.entry_point
        }

    def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流配置摘要（名称、版本、校验指纹等）
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Dict[str, Any]: 工作流摘要信息
        """
        config = self.get_workflow_config(workflow_id)
        if not config:
            return {}
        
        metadata = self._workflow_metadata.get(workflow_id, {})
        stats = self._execution_stats.get(workflow_id, {})
        config_path = metadata.get("config_path", "")
        
        # 计算配置文件校验和
        checksum = ""
        if config_path and Path(config_path).exists():
            try:
                import hashlib
                with open(config_path, 'rb') as f:
                    checksum = hashlib.md5(f.read()).hexdigest()
            except Exception:
                checksum = ""
        
        return {
            "workflow_id": workflow_id,
            "name": config.name,
            "version": config.version,
            "description": config.description,
            "config_path": config_path,
            "checksum": checksum,
            "loaded_at": metadata.get("loaded_at"),
            "last_used": metadata.get("last_used"),
            "usage_count": metadata.get("usage_count", 0),
            "execution_stats": stats
        }

    def get_workflow_execution_stats(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流执行统计
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Dict[str, Any]: 执行统计信息
        """
        return self._execution_stats.get(workflow_id, {})

    def _generate_workflow_id(self, workflow_name: str) -> str:
        """生成工作流ID
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            str: 工作流ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{workflow_name}_{timestamp}_{unique_id}"

    def _update_usage_stats(self, workflow_id: str) -> None:
        """更新使用统计
        
        Args:
            workflow_id: 工作流ID
        """
        if workflow_id in self._workflow_metadata:
            metadata = self._workflow_metadata[workflow_id]
            metadata["last_used"] = datetime.now().isoformat()
            metadata["usage_count"] += 1

    def _update_execution_stats(
        self, 
        workflow_id: str, 
        success: bool, 
        execution_time: float
    ) -> None:
        """更新执行统计
        
        Args:
            workflow_id: 工作流ID
            success: 是否成功
            execution_time: 执行时间
        """
        if workflow_id not in self._execution_stats:
            return
        
        stats = self._execution_stats[workflow_id]
        stats["total_executions"] += 1
        stats["last_execution_time"] = execution_time
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        # 更新平均执行时间
        total_time = stats.get("total_execution_time", 0.0) + execution_time
        stats["total_execution_time"] = total_time
        stats["average_execution_time"] = total_time / stats["total_executions"]

    def _log_workflow_error(self, workflow_id: str, error: Exception) -> None:
        """记录工作流错误
        
        Args:
            workflow_id: 工作流ID
            error: 错误信息
        """
        metadata = self._workflow_metadata.get(workflow_id, {})
        if "errors" not in metadata:
            metadata["errors"] = []
        
        metadata["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error)
        })