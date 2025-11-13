"""工作流管理器 - 重构版本

专注于工作流元数据管理和协调，不直接处理配置和执行
"""

from typing import Dict, Any, Optional, List, Generator
from pathlib import Path
import logging
from datetime import datetime
import uuid

from .interfaces import IWorkflowManager
from src.domain.workflow.interfaces import IWorkflowConfigManager, IWorkflowVisualizer, IWorkflowRegistry
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states import WorkflowState

logger = logging.getLogger(__name__)


class WorkflowManager(IWorkflowManager):
    """工作流管理器实现 - 重构版本
    
    专注于：
    - 工作流元数据管理
    - 组件协调
    - 向后兼容性
    """

    def __init__(
        self,
        config_loader: Optional[Any] = None,  # 保持向后兼容
        node_registry: Optional[Any] = None,  # 保持向后兼容
        workflow_builder: Optional[Any] = None,  # 保持向后兼容
        config_manager: Optional[IWorkflowConfigManager] = None,
        visualizer: Optional[IWorkflowVisualizer] = None,
        registry: Optional[IWorkflowRegistry] = None
    ):
        """初始化工作流管理器
        
        Args:
            config_loader: 配置加载器（向后兼容）
            node_registry: 节点注册表（向后兼容）
            workflow_builder: 工作流构建器（向后兼容）
            config_manager: 配置管理器
            visualizer: 可视化器
            registry: 工作流注册表
        """
        # 优先使用新的参数，如果未提供则尝试使用旧的参数（向后兼容）
        self.config_manager = config_manager
        self.visualizer = visualizer
        self.registry = registry
        
        # 向后兼容：设置旧的属性名
        self.config_loader = config_loader
        self.node_registry = node_registry
        self.workflow_builder = workflow_builder
        
        # 向后兼容：如果node_registry未提供，创建默认的
        if self.node_registry is None:
            try:
                from ...infrastructure.graph.registry import get_global_registry
                self.node_registry = get_global_registry()
            except ImportError:
                pass
        
        # 向后兼容：如果workflow_builder未提供，创建默认的
        if self.workflow_builder is None:
            try:
                from ...infrastructure.graph.builder import GraphBuilder
                if self.node_registry is not None:
                    self.workflow_builder = GraphBuilder(node_registry=self.node_registry)
            except ImportError:
                pass
        
        # 向后兼容：保持原有的工作流存储
        self._workflows: Dict[str, Any] = {}
        self._workflow_configs: Dict[str, WorkflowConfig] = {}
        self._workflow_metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.info("WorkflowManager初始化完成（重构版本）")
    
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
        # 由于重构后的工作流执行逻辑已移至ThreadManager，这里返回一个错误或简化实现
        raise NotImplementedError("工作流执行已移至ThreadManager，请使用ThreadManager.execute_workflow()")
    
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
        # 由于重构后的工作流执行逻辑已移至ThreadManager，这里返回一个错误或简化实现
        raise NotImplementedError("工作流执行已移至ThreadManager，请使用ThreadManager.execute_workflow()")
    
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
        # 由于重构后的工作流执行逻辑已移至ThreadManager，这里返回一个错误或简化实现
        raise NotImplementedError("工作流执行已移至ThreadManager，请使用ThreadManager.stream_workflow()")
    
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


    def load_workflow(self, config_path: str) -> str:
        """加载工作流（向后兼容方法）
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            str: 工作流ID
        """
        # 优先使用新的配置管理器，如果不可用则使用旧的实现
        if self.config_manager:
            # 使用新的配置管理器
            config_id = self.config_manager.load_config(config_path)
            config = self.config_manager.get_config(config_id)
            
            if not config:
                raise RuntimeError("配置加载失败")
            
            # 向后兼容：存储到原有结构
            workflow_id = config_id
            self._workflows[workflow_id] = config  # 简化存储
            self._workflow_configs[workflow_id] = config
            metadata = self.config_manager.get_config_metadata(config_id) or {}
            # 确保config_path在元数据中
            metadata["config_path"] = config_path
            metadata["loaded_at"] = datetime.now().isoformat()
            metadata["usage_count"] = 0
            self._workflow_metadata[workflow_id] = metadata
            
            # 注册到注册表
            if self.registry:
                self.registry.register_workflow({
                    "workflow_id": workflow_id,
                    "config_id": config_id,
                    "name": config.name,
                    "description": config.description,
                    "version": config.version,
                    "config_path": config_path
                })
            
            return workflow_id
        else:
            # 旧的实现已移除，现在必须使用新的配置管理器
            raise RuntimeError("配置管理器未初始化，无法加载工作流。请使用新的配置管理器。")

    def list_workflows(self) -> List[str]:
        """列出所有工作流（向后兼容方法）
        
        Returns:
            List[str]: 工作流ID列表
        """
        # 优先从配置管理器获取
        if self.config_manager:
            return self.config_manager.list_configs()
        
        # 向后兼容：从原有存储获取
        return list(self._workflows.keys())

    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置（向后兼容方法）
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[WorkflowConfig]: 工作流配置
        """
        # 优先从配置管理器获取
        if self.config_manager:
            config = self.config_manager.get_config(workflow_id)
            if config:
                return config
        
        # 向后兼容：从原有存储获取
        return self._workflow_configs.get(workflow_id)

    def unload_workflow(self, workflow_id: str) -> bool:
        """卸载工作流（向后兼容方法）
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否成功卸载
        """
        success = True
        
        # 从配置管理器移除（如果支持）
        # 注意：当前IWorkflowConfigManager接口没有unload方法，需要扩展
        
        # 向后兼容：从原有存储移除
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            success = True
        
        if workflow_id in self._workflow_configs:
            del self._workflow_configs[workflow_id]
            success = True
        
        if workflow_id in self._workflow_metadata:
            del self._workflow_metadata[workflow_id]
            success = True
        
        return success

    def reload_workflow(self, workflow_id: str) -> bool:
        """重新加载工作流（向后兼容方法）
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否成功重新加载
        """
        # 获取工作流的配置路径
        metadata = self._workflow_metadata.get(workflow_id)
        if not metadata or "config_path" not in metadata:
            logger.warning(f"无法找到工作流 '{workflow_id}' 的配置路径")
            return False
        
        config_path = metadata["config_path"]
        
        try:
            # 重新加载配置文件
            if self.config_manager:
                # 使用新的配置管理器重新加载
                new_config = self.config_manager.get_config(workflow_id)
                if new_config:
                    # 更新缓存
                    self._workflow_configs[workflow_id] = new_config
                    # 更新元数据中的last_reloaded时间
                    metadata["last_reloaded"] = datetime.now().isoformat()
                    return True
            
            # 向后兼容：使用config_loader重新加载
            if self.config_loader:
                # 从文件重新加载配置
                from ...infrastructure.graph.config import WorkflowConfig
                import yaml
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                new_config = WorkflowConfig.from_dict(config_data)
                self._workflow_configs[workflow_id] = new_config
                
                # 更新元数据
                metadata["last_reloaded"] = datetime.now().isoformat()
                
                logger.info(f"工作流 '{workflow_id}' 已成功重新加载")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"重新加载工作流 '{workflow_id}' 失败: {e}")
            return False

    def get_workflow_visualization(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流可视化数据（向后兼容方法）
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Dict[str, Any]: 可视化数据
        """
        config = self.get_workflow_config(workflow_id)
        if not config:
            return {}
        
        if self.visualizer:
            return self.visualizer.generate_visualization(config)
        
        # 向后兼容：简化实现
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


    def get_workflow_metadata(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流元数据（向后兼容方法）
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[Dict[str, Any]]: 工作流元数据
        """
        # 优先从配置管理器获取
        if self.config_manager:
            metadata = self.config_manager.get_config_metadata(workflow_id)
            if metadata:
                return metadata
        
        # 向后兼容：从原有存储获取
        return self._workflow_metadata.get(workflow_id)


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