"""工作流管理器

负责工作流的加载、创建、执行和管理。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncGenerator, Generator
from pathlib import Path
import uuid
from datetime import datetime

from src.application.workflow.config import WorkflowConfig
from .builder import WorkflowBuilder
from .registry import NodeRegistry, get_global_registry
from src.application.workflow.state import WorkflowState
from src.infrastructure.config_loader import IConfigLoader


class IWorkflowManager(ABC):
    """工作流管理器接口"""

    @abstractmethod
    def load_workflow(self, config_path: str) -> str:
        """加载工作流配置

        Args:
            config_path: 配置文件路径

        Returns:
            str: 工作流ID
        """
        pass

    @abstractmethod
    def create_workflow(self, workflow_id: str) -> Any:
        """创建工作流实例

        Args:
            workflow_id: 工作流ID

        Returns:
            Any: 工作流实例
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def list_workflows(self) -> List[str]:
        """列出所有已加载的工作流

        Returns:
            List[str]: 工作流ID列表
        """
        pass

    @abstractmethod
    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置

        Args:
            workflow_id: 工作流ID

        Returns:
            Optional[WorkflowConfig]: 工作流配置
        """
        pass

    @abstractmethod
    def unload_workflow(self, workflow_id: str) -> bool:
        """卸载工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            bool: 是否成功卸载
        """
        pass

    @abstractmethod
    def get_workflow_visualization(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流可视化数据

        Args:
            workflow_id: 工作流ID

        Returns:
            Dict[str, Any]: 可视化数据
        """
        pass

    @abstractmethod
    def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流配置摘要（名称、版本、校验指纹等）

        Args:
            workflow_id: 工作流ID

        Returns:
            Dict[str, Any]: 工作流摘要信息
        """
        pass


class WorkflowManager(IWorkflowManager):
    """工作流管理器实现"""

    def __init__(
        self,
        config_loader: Optional[IConfigLoader] = None,
        node_registry: Optional[NodeRegistry] = None,
        workflow_builder: Optional[WorkflowBuilder] = None
    ) -> None:
        """初始化工作流管理器

        Args:
            config_loader: 配置加载器
            node_registry: 节点注册表
            workflow_builder: 工作流构建器
        """
        self.config_loader = config_loader
        self.node_registry = node_registry or get_global_registry()
        self.workflow_builder = workflow_builder or WorkflowBuilder(self.node_registry)
        
        # 工作流存储
        self._workflows: Dict[str, Any] = {}
        self._workflow_configs: Dict[str, WorkflowConfig] = {}
        self._workflow_metadata: Dict[str, Dict[str, Any]] = {}

    def load_workflow(self, config_path: str) -> str:
        """加载工作流配置

        Args:
            config_path: 配置文件路径

        Returns:
            str: 工作流ID
        """
        # 加载配置
        workflow_config = self.workflow_builder.load_workflow_config(config_path)
        
        # 生成工作流ID
        workflow_id = self._generate_workflow_id(workflow_config.name)
        
        # 创建工作流实例
        workflow = self.workflow_builder.build_workflow(workflow_config)
        
        # 存储工作流
        self._workflows[workflow_id] = workflow
        self._workflow_configs[workflow_id] = workflow_config
        self._workflow_metadata[workflow_id] = {
            "name": workflow_config.name,
            "description": workflow_config.description,
            "version": workflow_config.version,
            "config_path": config_path,
            "loaded_at": datetime.now().isoformat(),
            "last_used": None,
            "usage_count": 0
        }
        
        return workflow_id

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
        self._workflow_metadata[workflow_id]["last_used"] = datetime.now().isoformat()
        self._workflow_metadata[workflow_id]["usage_count"] += 1
        
        return self._workflows[workflow_id]

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
        workflow = self.create_workflow(workflow_id)
        config = self._workflow_configs[workflow_id]
        
        # 准备初始状态
        if initial_state is None:
            initial_state = WorkflowState()
        
        # 设置初始参数
        if hasattr(initial_state, 'max_iterations'):
            initial_state.max_iterations = config.additional_config.get('max_iterations', 10)
        
        # 收集工作流开始事件
        if event_collector:
            event_collector.collect_workflow_start(config.name, config.to_dict())
        
        # 运行工作流
        try:
            result = workflow.invoke(initial_state, **kwargs)
            
            # 收集工作流结束事件
            if event_collector:
                event_collector.collect_workflow_end(config.name, {"status": "success", "result": result.to_dict() if hasattr(result, 'to_dict') else str(result)})
            
            return result  # type: ignore
        except Exception as e:
            # 记录错误并重新抛出
            self._log_workflow_error(workflow_id, e)
            
            # 收集错误事件
            if event_collector:
                event_collector.collect_error(e, {"workflow_id": workflow_id, "workflow_name": config.name})
            
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
        workflow = self.create_workflow(workflow_id)
        config = self._workflow_configs[workflow_id]
        
        # 准备初始状态
        if initial_state is None:
            initial_state = WorkflowState()
        
        # 设置初始参数
        if hasattr(initial_state, 'max_iterations'):
            initial_state.max_iterations = config.additional_config.get('max_iterations', 10)
        
        # 收集工作流开始事件
        if event_collector:
            event_collector.collect_workflow_start(config.name, config.to_dict())
        
        # 异步运行工作流
        try:
            if hasattr(workflow, 'ainvoke'):
                result = await workflow.ainvoke(initial_state, **kwargs)
            else:
                # 如果不支持异步，使用同步方式
                result = workflow.invoke(initial_state, **kwargs)
            
            # 收集工作流结束事件
            if event_collector:
                event_collector.collect_workflow_end(config.name, {"status": "success", "result": result.to_dict() if hasattr(result, 'to_dict') else str(result)})
            
            return result  # type: ignore
        except Exception as e:
            # 记录错误并重新抛出
            self._log_workflow_error(workflow_id, e)
            
            # 收集错误事件
            if event_collector:
                event_collector.collect_error(e, {"workflow_id": workflow_id, "workflow_name": config.name})
            
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
        workflow = self.create_workflow(workflow_id)
        config = self._workflow_configs[workflow_id]
        
        # 准备初始状态
        if initial_state is None:
            initial_state = WorkflowState()
        
        # 设置初始参数
        if hasattr(initial_state, 'max_iterations'):
            initial_state.max_iterations = config.additional_config.get('max_iterations', 10)
        
        # 收集工作流开始事件
        if event_collector:
            event_collector.collect_workflow_start(config.name, config.to_dict())
        
        # 流式运行工作流
        try:
            if hasattr(workflow, 'stream'):
                for chunk in workflow.stream(initial_state, **kwargs):
                    yield chunk
            else:
                # 如果不支持流式，直接返回最终结果
                result = workflow.invoke(initial_state, **kwargs)
                yield result
            
            # 收集工作流结束事件
            if event_collector:
                event_collector.collect_workflow_end(config.name, {"status": "success"})
                
        except Exception as e:
            # 记录错误并重新抛出
            self._log_workflow_error(workflow_id, e)
            
            # 收集错误事件
            if event_collector:
                event_collector.collect_error(e, {"workflow_id": workflow_id, "workflow_name": config.name})
            
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
                    "type": node.type,
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
            "usage_count": metadata.get("usage_count", 0)
        }

    def get_workflow_metadata(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流元数据

        Args:
            workflow_id: 工作流ID

        Returns:
            Optional[Dict[str, Any]]: 工作流元数据
        """
        return self._workflow_metadata.get(workflow_id)

    def reload_workflow(self, workflow_id: str) -> bool:
        """重新加载工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            bool: 是否成功重新加载
        """
        if workflow_id not in self._workflow_configs:
            return False
        
        # 获取原始配置路径
        metadata = self._workflow_metadata[workflow_id]
        config_path = metadata.get("config_path")
        
        if not config_path or not Path(config_path).exists():
            return False
        
        try:
            # 重新加载配置
            workflow_config = self.workflow_builder.load_workflow_config(config_path)
            workflow = self.workflow_builder.build_workflow(workflow_config)
            
            # 更新存储
            self._workflows[workflow_id] = workflow
            self._workflow_configs[workflow_id] = workflow_config
            
            # 更新元数据
            metadata["version"] = workflow_config.version
            metadata["loaded_at"] = datetime.now().isoformat()
            
            return True
        except Exception:
            return False

    def _generate_workflow_id(self, workflow_name: str) -> str:
        """生成工作流ID

        Args:
            workflow_name: 工作流名称

        Returns:
            str: 工作流ID
        """
        # 使用名称和时间戳生成唯一ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{workflow_name}_{timestamp}_{unique_id}"

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