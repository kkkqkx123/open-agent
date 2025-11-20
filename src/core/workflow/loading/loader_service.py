"""统一工作流加载器服务 - 新架构实现

整合所有加载相关功能，作为工作流相关服务的统一入口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging
import yaml

from src.core.config.config_manager import ConfigManager
from src.core.workflow.config.config import GraphConfig
from src.core.workflow.management.workflow_validator import WorkflowValidator, ValidationIssue
from src.core.workflow.state_machine.state_templates import StateTemplateManager
from src.services.workflow.function_registry import FunctionRegistry, FunctionType
from src.core.workflow.graph.builder.base import UnifiedGraphBuilder
from ....core.workflow.workflow_instance import WorkflowInstance
from src.core.workflow.exceptions import WorkflowConfigError, WorkflowValidationError

logger = logging.getLogger(__name__)


class IUniversalLoaderService(ABC):
    """统一加载器服务接口"""
    
    @abstractmethod
    def load_from_file(self, config_path: str) -> WorkflowInstance:
        """从文件加载工作流"""
        pass
    
    @abstractmethod
    def load_from_dict(self, config_dict: Dict[str, Any]) -> WorkflowInstance:
        """从字典加载工作流"""
        pass
    
    @abstractmethod
    def get_workflow_info(self, config_path: str) -> Dict[str, Any]:
        """获取工作流信息"""
        pass
    
    @abstractmethod
    def list_available_workflows(self) -> List[str]:
        """列出可用工作流"""
        pass
    
    @abstractmethod
    def validate_workflow(self, config_path: str) -> List[ValidationIssue]:
        """验证工作流配置"""
        pass
    
    @abstractmethod
    def register_function(
        self, 
        name: str, 
        function: Any, 
        function_type: FunctionType
    ) -> None:
        """注册函数"""
        pass
    
    @abstractmethod
    def clear_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存"""
        pass


class UniversalLoaderService(IUniversalLoaderService):
    """统一工作流加载器服务 - 新架构实现
    
    整合所有加载相关功能，作为工作流相关服务的统一入口。
    """
    
    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        function_registry: Optional[FunctionRegistry] = None,
        builder: Optional[UnifiedGraphBuilder] = None,
        workflow_validator: Optional[WorkflowValidator] = None,
        state_template_manager: Optional[StateTemplateManager] = None,
        enable_caching: bool = True
    ):
        """初始化统一加载器服务
        
        Args:
            config_manager: 配置管理器
            function_registry: 函数注册表
            builder: 统一图构建器
            workflow_validator: 工作流验证器
            state_template_manager: 状态模板管理器
            enable_caching: 是否启用缓存
        """
        # 初始化核心组件
        self.config_manager = config_manager or ConfigManager()
        self.function_registry = function_registry or FunctionRegistry()
        self.builder = builder or UnifiedGraphBuilder(
            function_registry=self.function_registry
        )
        self.workflow_validator = workflow_validator or WorkflowValidator()
        self.state_template_manager = state_template_manager or StateTemplateManager()
        
        # 缓存
        self.enable_caching = enable_caching
        self._config_cache: Dict[str, GraphConfig] = {}
        self._graph_cache: Dict[str, Any] = {}
        self._instance_cache: Dict[str, WorkflowInstance] = {}
        
        logger.debug("统一工作流加载器服务初始化完成")
    
    def load_from_file(self, config_path: str) -> WorkflowInstance:
        """从文件加载工作流 - 整合多个步骤
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            WorkflowInstance: 工作流实例
            
        Raises:
            WorkflowConfigError: 配置错误
            WorkflowValidationError: 验证错误
        """
        try:
            # 1. 加载配置
            config = self._load_config_from_file(config_path)
            
            # 2. 验证配置
            self._validate_config(config)
            
            # 3. 构建图
            compiled_graph = self._build_graph(config)
            
            # 4. 创建工作流实例
            instance = self._create_workflow_instance(config, compiled_graph)
            
            logger.info(f"成功从文件加载工作流: {config.name}")
            return instance
            
        except Exception as e:
            logger.error(f"从文件加载工作流失败: {config_path}, 错误: {e}")
            raise
    
    def load_from_dict(self, config_dict: Dict[str, Any]) -> WorkflowInstance:
        """从字典加载工作流
        
        Args:
            config_dict: 配置字典
            
        Returns:
            WorkflowInstance: 工作流实例
            
        Raises:
            WorkflowConfigError: 配置错误
            WorkflowValidationError: 验证错误
        """
        try:
            # 1. 解析配置
            config = GraphConfig.from_dict(config_dict)
            
            # 2. 验证配置
            self._validate_config(config)
            
            # 3. 构建图
            compiled_graph = self._build_graph(config)
            
            # 4. 创建工作流实例
            instance = self._create_workflow_instance(config, compiled_graph)
            
            logger.info(f"成功从字典加载工作流: {config.name}")
            return instance
            
        except Exception as e:
            logger.error(f"从字典加载工作流失败: {e}")
            raise
    
    def get_workflow_info(self, config_path: str) -> Dict[str, Any]:
        """获取工作流信息
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 工作流信息
        """
        try:
            # 加载配置
            config = self._load_config_from_file(config_path)
            
            # 验证配置
            validation_result = self.workflow_validator.validate_config_object(config)
            
            # 构建基本信息
            info = {
                "name": config.name,
                "description": config.description,
                "version": getattr(config, 'version', '1.0.0'),
                "file_path": config_path,
                "validation": {
                    "is_valid": len([issue for issue in validation_result if issue.severity.value == "error"]) == 0,
                    "errors": [issue.message for issue in validation_result if issue.severity.value == "error"],
                    "warnings": [issue.message for issue in validation_result if issue.severity.value == "warning"],
                    "info_count": len([issue for issue in validation_result if issue.severity.value == "info"])
                },
                "structure": {
                    "node_count": len(config.nodes),
                    "edge_count": len(config.edges),
                    "entry_point": config.entry_point,
                    "nodes": list(config.nodes.keys()),
                    "has_state_schema": hasattr(config, 'state_schema') and config.state_schema is not None
                },
                "functions": self._get_function_info(),
                "metadata": {
                    "supports_caching": self.enable_caching,
                    "cache_status": {
                        "config_cached": config_path in self._config_cache,
                        "graph_cached": self._get_config_hash(config) in self._graph_cache,
                        "instance_cached": config_path in self._instance_cache
                    }
                }
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取工作流信息失败: {config_path}, 错误: {e}")
            return {
                "name": "unknown",
                "error": str(e),
                "file_path": config_path
            }
    
    def list_available_workflows(self) -> List[str]:
        """列出可用工作流
        
        Returns:
            List[str]: 可用工作流路径列表
        """
        try:
            # 手动扫描配置文件
            config_dir = Path("configs/workflows")
            if config_dir.exists():
                available_workflows = [
                    str(f) for f in config_dir.glob("*.yaml") 
                    if f.name != "_group.yaml"
                ]
                return available_workflows
            return []
            
        except Exception as e:
            logger.error(f"列出可用工作流失败: {e}")
            return []
    
    def validate_workflow(self, config_path: str) -> List[ValidationIssue]:
        """验证工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            List[ValidationIssue]: 验证问题列表
        """
        try:
            # 加载配置
            config = self._load_config_from_file(config_path)
            
            # 验证配置
            return self.workflow_validator.validate_config_object(config)
            
        except Exception as e:
            logger.error(f"验证工作流失败: {config_path}, 错误: {e}")
            return []
    
    def register_function(
        self, 
        name: str, 
        function: Any, 
        function_type: FunctionType
    ) -> None:
        """注册函数
        
        Args:
            name: 函数名称
            function: 函数对象
            function_type: 函数类型
        """
        try:
            self.function_registry.register(name, function, function_type)
            logger.debug(f"注册函数: {name} ({function_type.value})")
        except Exception as e:
            logger.error(f"注册函数失败: {name}, 错误: {e}")
            raise
    
    def register_functions_from_module(self, module_path: str) -> Dict[str, List[str]]:
        """从模块注册函数
        
        Args:
            module_path: 模块路径
            
        Returns:
            Dict[str, List[str]]: 注册的函数统计信息
        """
        try:
            return self.function_registry.discover_functions([module_path])
        except Exception as e:
            logger.error(f"从模块注册函数失败: {module_path}, 错误: {e}")
            raise
    
    def get_function_statistics(self) -> Dict[str, Any]:
        """获取函数统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 从函数注册表获取统计信息
            node_functions = self.function_registry.list_functions(FunctionType.NODE_FUNCTION)
            condition_functions = self.function_registry.list_functions(FunctionType.CONDITION_FUNCTION)
            
            return {
                "total_node_functions": len(node_functions.get("nodes", [])),
                "total_condition_functions": len(condition_functions.get("conditions", [])),
                "registered_functions": {
                    "nodes": node_functions.get("nodes", []),
                    "conditions": condition_functions.get("conditions", [])
                }
            }
        except Exception as e:
            logger.error(f"获取函数统计信息失败: {e}")
            return {
                "total_node_functions": 0,
                "total_condition_functions": 0,
                "registered_functions": {"nodes": [], "conditions": []}
            }
    
    def clear_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 特定配置路径，如果为None则清除所有缓存
        """
        if config_path:
            # 清除特定配置的缓存
            self._config_cache.pop(config_path, None)
            self._instance_cache.pop(config_path, None)
            
            # 尝试清除图缓存（需要计算哈希）
            try:
                config = self._load_config_from_file(config_path)
                config_hash = self._get_config_hash(config)
                self._graph_cache.pop(config_hash, None)
            except:
                pass
            
            logger.debug(f"清除配置缓存: {config_path}")
        else:
            # 清除所有缓存
            self._config_cache.clear()
            self._graph_cache.clear()
            self._instance_cache.clear()
            logger.debug("清除所有缓存")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        return {
            "caching_enabled": self.enable_caching,
            "config_cache_size": len(self._config_cache),
            "graph_cache_size": len(self._graph_cache),
            "instance_cache_size": len(self._instance_cache),
            "cached_configs": list(self._config_cache.keys()),
            "cached_instances": list(self._instance_cache.keys())
        }
    
    def _load_config_from_file(self, config_path: str) -> GraphConfig:
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            GraphConfig: 图配置
        """
        # 检查缓存
        if self.enable_caching and config_path in self._config_cache:
            logger.debug(f"从缓存加载配置: {config_path}")
            return self._config_cache[config_path]
        
        try:
            # 使用配置管理器加载配置
            config_data = self.config_manager.load_config(config_path)
            
            # 解析为 GraphConfig
            config = GraphConfig.from_dict(config_data)
            
            # 处理函数注册配置
            self._process_function_registrations(config_data)
            
            # 缓存配置
            if self.enable_caching:
                self._config_cache[config_path] = config
            
            return config
            
        except Exception as e:
            raise WorkflowConfigError(f"加载配置文件失败: {e}") from e
    
    def _validate_config(self, config: GraphConfig) -> None:
        """验证配置
        
        Args:
            config: 图配置
            
        Raises:
            WorkflowValidationError: 验证失败
        """
        validation_result = self.workflow_validator.validate_config_object(config)
        
        # 检查是否有错误
        errors = [issue for issue in validation_result if issue.severity.value == "error"]
        if errors:
            error_messages = [error.message for error in errors]
            raise WorkflowValidationError(f"配置验证失败: {'; '.join(error_messages)}")
    
    def _build_graph(self, config: GraphConfig) -> Any:
        """构建图
        
        Args:
            config: 图配置
            
        Returns:
            Any: 编译后的图
        """
        # 检查缓存
        config_hash = self._get_config_hash(config)
        if self.enable_caching and config_hash in self._graph_cache:
            logger.debug(f"从缓存获取图: {config.name}")
            return self._graph_cache[config_hash]
        
        try:
            # 构建图
            compiled_graph = self.builder.build_graph(config)
            
            # 缓存图
            if self.enable_caching:
                self._graph_cache[config_hash] = compiled_graph
            
            return compiled_graph
            
        except Exception as e:
            raise WorkflowConfigError(f"构建图失败: {e}") from e
    
    def _create_workflow_instance(
        self, 
        config: GraphConfig, 
        compiled_graph: Any
    ) -> WorkflowInstance:
        """创建工作流实例
        
        Args:
            config: 图配置
            compiled_graph: 编译后的图
            
        Returns:
            WorkflowInstance: 工作流实例
        """
        # 检查缓存
        if self.enable_caching and config.name in self._instance_cache:
            logger.debug(f"从缓存获取工作流实例: {config.name}")
            return self._instance_cache[config.name]
        
        try:
            # 创建工作流实例
            instance = WorkflowInstance(
                compiled_graph=compiled_graph,
                config=config,
                state_template_manager=self.state_template_manager
            )
            
            # 缓存实例
            if self.enable_caching:
                self._instance_cache[config.name] = instance
            
            return instance
            
        except Exception as e:
            raise WorkflowConfigError(f"创建工作流实例失败: {e}") from e
    
    def _process_function_registrations(self, config_data: Dict[str, Any]) -> None:
        """处理函数注册配置
        
        Args:
            config_data: 配置数据
        """
        function_registrations = config_data.get("function_registrations", {})
        
        if not function_registrations:
            return
        
        # 注册节点函数
        node_functions = function_registrations.get("nodes", {})
        for name, module_path in node_functions.items():
            try:
                self._register_function_from_module(name, module_path, FunctionType.NODE_FUNCTION)
            except Exception as e:
                logger.warning(f"注册节点函数失败: {name} -> {module_path}, 错误: {e}")
        
        # 注册条件函数
        condition_functions = function_registrations.get("conditions", {})
        for name, module_path in condition_functions.items():
            try:
                self._register_function_from_module(name, module_path, FunctionType.CONDITION_FUNCTION)
            except Exception as e:
                logger.warning(f"注册条件函数失败: {name} -> {module_path}, 错误: {e}")
        
        # 处理自动发现配置
        auto_discovery = function_registrations.get("auto_discovery", {})
        if auto_discovery.get("enabled", False):
            module_paths = auto_discovery.get("module_paths", [])
            if module_paths:
                try:
                    discovered = self.function_registry.discover_functions(module_paths)
                    logger.info(f"自动发现函数: 节点函数 {len(discovered['nodes'])} 个, 条件函数 {len(discovered['conditions'])} 个")
                except Exception as e:
                    logger.warning(f"自动发现函数失败: {e}")
    
    def _register_function_from_module(self, name: str, module_path: str, function_type: FunctionType) -> None:
        """从模块注册函数
        
        Args:
            name: 函数名称
            module_path: 模块路径
            function_type: 函数类型
        """
        try:
            import importlib
            module = importlib.import_module(module_path)
            function = getattr(module, name)
            self.register_function(name, function, function_type)
        except Exception as e:
            raise WorkflowConfigError(f"从模块注册函数失败: {e}") from e
    
    def _get_config_hash(self, config: GraphConfig) -> str:
        """获取配置哈希
        
        Args:
            config: 图配置
            
        Returns:
            str: 配置哈希
        """
        import hashlib
        config_str = str(config.to_dict())
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _get_function_info(self) -> Dict[str, Any]:
        """获取函数信息
        
        Returns:
            Dict[str, Any]: 函数信息
        """
        try:
            node_functions = self.function_registry.list_functions(FunctionType.NODE_FUNCTION)
            condition_functions = self.function_registry.list_functions(FunctionType.CONDITION_FUNCTION)
            
            return {
                "node_functions": {
                    "count": len(node_functions.get("nodes", [])),
                    "names": node_functions.get("nodes", [])
                },
                "condition_functions": {
                    "count": len(condition_functions.get("conditions", [])),
                    "names": condition_functions.get("conditions", [])
                }
            }
        except Exception as e:
            logger.error(f"获取函数信息失败: {e}")
            return {
                "node_functions": {"count": 0, "names": []},
                "condition_functions": {"count": 0, "names": []}
            }