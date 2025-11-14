"""工作流工厂

提供工作流实例的创建和管理功能。
"""

from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod
import logging

from .interfaces import IWorkflowFactory, IWorkflowManager
from src.infrastructure.graph.states import WorkflowState
from src.infrastructure.graph.config import WorkflowConfig
from infrastructure.config.core.loader import IConfigLoader
from src.infrastructure.container import IDependencyContainer
from src.infrastructure.registry.module_registry_manager import ModuleRegistryManager
from src.infrastructure.registry.dynamic_importer import DynamicImporter
from src.infrastructure.registry.hot_reload_listener import HotReloadManager, HotReloadEvent

logger = logging.getLogger(__name__)


class WorkflowFactory(IWorkflowFactory):
    """工作流工厂实现"""
    
    def __init__(
        self,
        container: Optional[IDependencyContainer] = None,
        config_loader: Optional[IConfigLoader] = None,
        registry_manager: Optional[ModuleRegistryManager] = None
    ):
        """初始化工作流工厂
        
        Args:
            container: 依赖注入容器
            config_loader: 配置加载器
            registry_manager: 模块注册管理器
        """
        self.container = container
        self.config_loader = config_loader
        self.registry_manager = registry_manager
        self.dynamic_importer = DynamicImporter()
        
        # 工作流类型注册表
        self._workflow_types: Dict[str, Type] = {}
        
        # 热重载管理器
        self.hot_reload_manager: Optional[HotReloadManager] = None
        
        # 初始化注册管理器
        if self.registry_manager:
            self._initialize_from_registry()
            self._setup_hot_reload()
        else:
            # 注册内置工作流类型（向后兼容）
            self._register_builtin_workflows()
    
    def create_workflow(self, config: WorkflowConfig) -> Any:
        """创建工作流实例

        Args:
            config: 工作流配置

        Returns:
            工作流实例
        """
        # 从配置中推断工作流类型
        # 首先尝试从additional_config中获取类型
        workflow_type = config.additional_config.get('workflow_type')

        # 如果没有，则从名称中推断
        if not workflow_type:
            name = config.name.lower()
            if 'react' in name:
                workflow_type = 'react'
            elif 'plan_execute' in name or 'plan' in name:
                workflow_type = 'plan_execute'
            else:
                workflow_type = 'base'

        if workflow_type not in self._workflow_types:
            raise ValueError(f"未知的工作流类型: {workflow_type}")

        workflow_class = self._workflow_types[workflow_type]

        return workflow_class(config, self.config_loader, self.container)
    
    def register_workflow_type(self, workflow_type: str, workflow_class: Type) -> None:
        """注册工作流类型
        
        Args:
            workflow_type: 工作流类型名称
            workflow_class: 工作流类
        """
        self._workflow_types[workflow_type] = workflow_class
        logger.debug(f"注册工作流类型: {workflow_type}")
    
    def get_supported_types(self) -> list:
        """获取支持的工作流类型列表
        
        Returns:
            list: 工作流类型列表
        """
        return list(self._workflow_types.keys())
    
    def _register_builtin_workflows(self) -> None:
        """注册内置工作流类型"""
        try:
            # 注册基础工作流
            self.register_workflow_type("base", BaseWorkflow)
            
            logger.debug("内置工作流类型注册完成")
        except Exception as e:
            logger.warning(f"部分内置工作流类型不可用: {e}")
    
    def load_workflow_config(self, config_path: str) -> WorkflowConfig:
        """加载工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            WorkflowConfig: 工作流配置
        """
        if not self.config_loader:
            raise ValueError("配置加载器未初始化")
        
        # 使用配置加载器加载YAML配置文件
        import yaml
        from pathlib import Path
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 转换为WorkflowConfig对象
        return WorkflowConfig.from_dict(config_data)
    
    def _initialize_from_registry(self) -> None:
        """从注册管理器初始化工作流类型
        
        从模块注册管理器中加载工作流类型信息并注册。
        """
        if not self.registry_manager:
            logger.warning("注册管理器未初始化")
            return
        
        try:
            # 获取工作流类型信息
            workflow_types = self.registry_manager.get_workflow_types()
            
            for type_name, type_info in workflow_types.items():
                if not type_info.enabled:
                    logger.debug(f"跳过禁用的工作流类型: {type_name}")
                    continue
                
                try:
                    # 动态导入工作流类
                    workflow_class = self.dynamic_importer.import_class(type_info.class_path)
                    
                    # 注册工作流类型
                    self.register_workflow_type(type_name, workflow_class)
                    
                    logger.info(f"从注册表加载工作流类型: {type_name} -> {type_info.class_path}")
                    
                except Exception as e:
                    logger.error(f"加载工作流类型失败: {type_name}, 错误: {e}")
            
            logger.info(f"从注册表初始化完成，加载了 {len(self._workflow_types)} 个工作流类型")
            
        except Exception as e:
            logger.error(f"从注册表初始化失败: {e}")
            # 降级到内置工作流类型
            self._register_builtin_workflows()
    
    def create_workflow_from_registry(self, workflow_name: str) -> Any:
        """从注册表创建工作流实例
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            工作流实例
            
        Raises:
            ValueError: 工作流不存在或创建失败
        """
        if not self.registry_manager:
            raise ValueError("注册管理器未初始化")
        
        # 获取工作流配置
        workflow_config = self.registry_manager.get_workflow_config(workflow_name)
        if not workflow_config:
            raise ValueError(f"工作流配置不存在: {workflow_name}")
        
        # 转换为WorkflowConfig对象
        config = WorkflowConfig.from_dict(workflow_config)
        
        # 创建工作流实例
        return self.create_workflow(config)
    
    def reload_from_registry(self) -> None:
        """从注册表重新加载工作流类型
        
        清除当前注册的工作流类型并重新从注册表加载。
        """
        if not self.registry_manager:
            logger.warning("注册管理器未初始化")
            return
        
        logger.info("重新从注册表加载工作流类型")
        
        # 清除当前注册的工作流类型
        self._workflow_types.clear()
        
        # 重新初始化
        self._initialize_from_registry()
    
    def get_registry_info(self) -> Optional[Dict[str, Any]]:
        """获取注册表信息
        
        Returns:
            Optional[Dict[str, Any]]: 注册表信息，如果注册管理器未初始化则返回None
        """
        if not self.registry_manager:
            return None
        
        return self.registry_manager.get_registry_info()
    
    def _setup_hot_reload(self) -> None:
        """设置热重载功能"""
        try:
            # 创建热重载管理器
            self.hot_reload_manager = HotReloadManager()
            
            # 添加监听器
            self.hot_reload_manager.add_listener(
                watch_paths=["configs/workflows"],
                file_patterns=[r".*\.ya?ml$"],
                exclude_patterns=[r".*\.tmp$", r".*\.swp$", r".*~$"]
            )
            
            # 添加热重载回调
            self.hot_reload_manager.add_callback(self._handle_hot_reload_event)
            
            # 启动热重载
            self.hot_reload_manager.start()
            
            logger.info("工作流工厂热重载已启用")
            
        except Exception as e:
            logger.warning(f"设置工作流工厂热重载失败: {e}")
    
    def _handle_hot_reload_event(self, event: HotReloadEvent) -> None:
        """处理热重载事件
        
        Args:
            event: 热重载事件
        """
        try:
            logger.info(f"工作流工厂收到热重载事件: {event}")
            
            # 检查是否是注册表文件
            if "__registry__.yaml" in event.file_path:
                logger.info("检测到注册表文件变化，重新加载工作流类型")
                self.reload_from_registry()
                # 清除缓存
                if self.registry_manager:
                    self.registry_manager.clear_cache()
                return
            
            # 检查是否是工作流配置文件
            if event.file_path.startswith("configs/workflows/"):
                # 清除相关配置缓存
                if self.registry_manager:
                    self.registry_manager.clear_cache()
                
                logger.info(f"工作流配置文件已更新: {event.file_path}")
            
        except Exception as e:
            logger.error(f"处理热重载事件失败: {e}")
    
    def enable_hot_reload(self) -> None:
        """启用热重载"""
        if not self.hot_reload_manager and self.registry_manager:
            self._setup_hot_reload()
        elif self.hot_reload_manager and not self.hot_reload_manager.is_running:
            self.hot_reload_manager.start()
    
    def disable_hot_reload(self) -> None:
        """禁用热重载"""
        if self.hot_reload_manager:
            self.hot_reload_manager.stop()
    
    def is_hot_reload_enabled(self) -> bool:
        """检查热重载是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.hot_reload_manager is not None and self.hot_reload_manager.is_running


class BaseWorkflow:
    """基础工作流类"""
    
    def __init__(self, config: Dict[str, Any], config_loader: IConfigLoader, container: IDependencyContainer):
        """初始化基础工作流
        
        Args:
            config: 工作流配置
            config_loader: 配置加载器
            container: 依赖注入容器
        """
        self.config = config
        self.config_loader = config_loader
        self.container = container
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """执行工作流
        
        Args:
            state: 工作流状态
            
        Returns:
            WorkflowState: 更新后的状态
        """
        # 基础实现，子类应该重写此方法
        return state
    
    def validate_config(self) -> list:
        """验证配置
        
        Returns:
            list: 验证错误列表
        """
        # 基础实现，子类可以重写此方法
        return []


class ReActWorkflow(BaseWorkflow):
    """ReAct工作流"""
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """执行ReAct工作流
        
        Args:
            state: 工作流状态
            
        Returns:
            WorkflowState: 更新后的状态
        """
        # ReAct工作流的实现逻辑
        # 这里应该实现ReAct算法的具体步骤
        
        # 确保状态中有必要的字段
        if "iteration_count" not in state:
            state["iteration_count"] = 0
        if "max_iterations" not in state:
            state["max_iterations"] = self.config.get("max_iterations", 10)
        
        # 简化的ReAct实现
        state["iteration_count"] += 1
        
        return state


class PlanExecuteWorkflow(BaseWorkflow):
    """计划执行工作流"""
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """执行计划执行工作流
        
        Args:
            state: 工作流状态
            
        Returns:
            WorkflowState: 更新后的状态
        """
        # 计划执行工作流的实现逻辑
        # 这里应该实现计划执行算法的具体步骤
        
        # 确保状态中有必要的字段
        if "context" not in state:
            state["context"] = {}
        
        # 简化的计划执行实现
        context = state["context"]
        if "current_plan" not in context:
            # 生成初始计划
            context["current_plan"] = [
                "分析用户需求",
                "制定执行计划",
                "执行计划步骤",
                "总结结果"
            ]
            context["current_step_index"] = 0
        
        return state