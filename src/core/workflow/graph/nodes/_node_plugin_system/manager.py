"""Node Hook管理器

专门管理Node生命周期Hook的管理器，替代原来PluginManager中的Hook相关职责。
"""

import logging
from typing import Dict, Any, Optional

from ...plugins.hooks.executor import HookExecutor
from ...plugins.registry import PluginRegistry
from ...plugins.interfaces_new import IHookPlugin
from ...states import WorkflowState
from ...registry import NodeExecutionResult


logger = logging.getLogger(__name__)


class NodeHookManager:
    """Node Hook管理器
    
    专门管理Node生命周期Hook的管理器，职责包括：
    - 管理Node相关的Hook插件
    - 提供统一的Hook执行接口
    - 管理Hook配置和生命周期
    """
    
    def __init__(self, plugin_config_path: Optional[str] = None):
        """初始化Node Hook管理器
        
        Args:
            plugin_config_path: 插件配置文件路径
        """
        self.plugin_config_path = plugin_config_path
        self.registry = PluginRegistry()
        self.hook_executor = HookExecutor(self.registry)
        self.plugin_configs: Dict[str, Any] = {}
        self._initialized = False
    
    def initialize(self) -> bool:
        """初始化Node Hook管理器
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            # 加载配置
            if not self.load_config():
                logger.error("加载Hook插件配置失败")
                return False
            
            # 注册内置Hook插件
            self.register_builtin_hook_plugins()
            
            # 加载外部Hook插件
            self.load_external_hook_plugins()
            
            # 设置Hook配置到执行器
            self.hook_executor.set_hook_configs(self.plugin_configs)
            
            self._initialized = True
            logger.info("Node Hook管理器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"Node Hook管理器初始化失败: {e}")
            return False
    
    def load_config(self) -> bool:
        """加载Hook插件配置
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if self.plugin_config_path:
                import yaml
                from pathlib import Path
                
                if Path(self.plugin_config_path).exists():
                    with open(self.plugin_config_path, 'r', encoding='utf-8') as f:
                        self.plugin_configs = yaml.safe_load(f)
                    logger.info(f"成功加载Hook插件配置: {self.plugin_config_path}")
                    return True
                else:
                    logger.warning("Hook插件配置文件不存在，使用默认配置")
                    self.plugin_configs = self._get_default_config()
                    return True
            else:
                logger.warning("未指定Hook插件配置文件，使用默认配置")
                self.plugin_configs = self._get_default_config()
                return True
        except Exception as e:
            logger.error(f"加载Hook插件配置失败: {e}")
            return False
    
    def register_builtin_hook_plugins(self) -> None:
        """注册内置Hook插件"""
        try:
            # 注册Hook插件
            from ...plugins.builtin.hooks import (
                DeadLoopDetectionPlugin, PerformanceMonitoringPlugin,
                ErrorRecoveryPlugin, LoggingPlugin, MetricsCollectionPlugin
            )
            self.registry.register_plugin(DeadLoopDetectionPlugin())
            self.registry.register_plugin(PerformanceMonitoringPlugin())
            self.registry.register_plugin(ErrorRecoveryPlugin())
            self.registry.register_plugin(LoggingPlugin())
            self.registry.register_plugin(MetricsCollectionPlugin())
            
            logger.info("内置Hook插件注册完成")
            
        except ImportError as e:
            logger.warning(f"无法导入内置Hook插件: {e}")
        except Exception as e:
            logger.error(f"注册内置Hook插件失败: {e}")
    
    def load_external_hook_plugins(self) -> None:
        """加载外部Hook插件"""
        try:
            hook_configs = self.plugin_configs.get('hook_plugins', {})
            external_configs = hook_configs.get('external', [])
            
            for plugin_config in external_configs:
                if not plugin_config.get('enabled', False):
                    continue
                
                try:
                    plugin = self._load_external_hook_plugin(plugin_config)
                    if plugin:
                        self.registry.register_plugin(plugin)
                        logger.info(f"成功加载外部Hook插件: {plugin_config['name']}")
                except Exception as e:
                    logger.error(f"加载外部Hook插件失败 {plugin_config['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"加载外部Hook插件过程中发生错误: {e}")
    
    def _load_external_hook_plugin(self, config: Dict[str, Any]) -> Optional[IHookPlugin]:
        """加载单个外部Hook插件
        
        Args:
            config: 插件配置
            
        Returns:
            Optional[IHookPlugin]: Hook插件实例，加载失败则返回None
        """
        import importlib
        
        module_name = config.get('module')
        class_name = config.get('class')
        
        if not module_name or not class_name:
            logger.error(f"Hook插件配置缺少module或class: {config}")
            return None
        
        try:
            # 动态导入模块
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            
            # 实例化插件
            plugin = plugin_class()
            
            # 验证插件接口
            if not isinstance(plugin, IHookPlugin):
                logger.error(f"Hook插件 {class_name} 未实现正确的接口")
                return None
            
            return plugin
            
        except ImportError as e:
            logger.error(f"无法导入Hook插件模块 {module_name}: {e}")
            return None
        except AttributeError as e:
            logger.error(f"Hook插件类 {class_name} 在模块 {module_name} 中不存在: {e}")
            return None
        except Exception as e:
            logger.error(f"实例化Hook插件失败 {class_name}: {e}")
            return None
    
    def execute_with_hooks(
        self,
        node_type: str,
        state: WorkflowState,
        config: Dict[str, Any],
        node_executor_func: callable
    ) -> NodeExecutionResult:
        """统一的Hook执行接口
        
        Args:
            node_type: 节点类型
            state: 当前状态
            config: 节点配置
            node_executor_func: 节点执行函数
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        if not self._initialized:
            if not self.initialize():
                # 如果初始化失败，直接执行节点逻辑
                return node_executor_func(state, config)
        
        return self.hook_executor.execute_with_hooks(
            node_type=node_type,
            state=state,
            config=config,
            node_executor_func=node_executor_func
        )
    
    def get_hook_plugins(self, node_type: str) -> list:
        """获取指定节点的Hook插件列表
        
        Args:
            node_type: 节点类型
            
        Returns:
            list: Hook插件列表
        """
        if not self._initialized:
            if not self.initialize():
                return []
        
        return self.hook_executor.get_enabled_hook_plugins(node_type)
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 性能统计信息
        """
        return self.hook_executor.get_performance_stats()
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self.registry.get_registry_stats()
        stats.update({
            "initialized": self._initialized,
            "config_path": self.plugin_config_path,
            "config_loaded": bool(self.plugin_configs),
            "performance_stats": self.get_performance_stats()
        })
        return stats
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            "hook_plugins": {
                "global": [
                    {"name": "performance_monitoring", "enabled": True, "priority": 10, "config": {}},
                    {"name": "logging", "enabled": True, "priority": 20, "config": {}},
                    {"name": "metrics_collection", "enabled": False, "priority": 30, "config": {}}
                ],
                "node_specific": {
                    "llm_node": [
                        {"name": "dead_loop_detection", "enabled": True, "priority": 10, "config": {}},
                        {"name": "error_recovery", "enabled": True, "priority": 20, "config": {}}
                    ],
                    "tool_node": [
                        {"name": "error_recovery", "enabled": True, "priority": 10, "config": {}}
                    ]
                },
                "external": []
            }
        }
    
    def cleanup(self) -> None:
        """清理Node Hook管理器资源"""
        try:
            # 清理Hook执行器
            self.hook_executor.cleanup()
            
            # 清理注册表
            self.registry.clear()
            
            # 清空配置
            self.plugin_configs.clear()
            self._initialized = False
            
            logger.info("Node Hook管理器清理完成")
            
        except Exception as e:
            logger.error(f"Node Hook管理器清理失败: {e}")