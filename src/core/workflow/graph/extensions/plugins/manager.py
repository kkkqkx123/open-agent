"""插件管理器

负责插件的加载、配置和执行管理。
已重构：移除Hook相关职责，专注于插件管理。
"""

import importlib
from src.interfaces.dependency_injection import get_logger
import time
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Sequence
from collections import defaultdict

from src.interfaces.workflow.plugins import (
    IPlugin, IStartPlugin, IEndPlugin, PluginType, PluginStatus,
    PluginContext, PluginError, PluginInitializationError, PluginExecutionError
)
from src.core.workflow.registry import PluginRegistry


logger = get_logger(__name__)


class PluginManager:
    """插件管理器
    
    负责插件的完整生命周期管理。
    已重构：移除Hook相关职责，专注于插件管理。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化插件管理器
        
        Args:
            config_path: 插件配置文件路径
        """
        self.config_path = config_path
        self.registry = PluginRegistry()
        self.plugin_configs: Dict[str, Any] = {}
        self.loaded_plugins: Dict[str, IPlugin] = {}
        self._initialized = False
    
    def initialize(self) -> bool:
        """初始化插件管理器
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            # 加载配置
            if not self.load_config():
                logger.error("加载插件配置失败")
                return False
            
            # 注册内置插件
            self.register_builtin_plugins()
            
            # 加载外部插件
            self.load_external_plugins()
            
            self._initialized = True
            logger.info("插件管理器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"插件管理器初始化失败: {e}")
            return False
    
    def load_config(self) -> bool:
        """加载插件配置
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if self.config_path and Path(self.config_path).exists():
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.plugin_configs = yaml.safe_load(f)
                logger.info(f"成功加载插件配置: {self.config_path}")
                return True
            else:
                logger.warning("插件配置文件不存在，使用默认配置")
                self.plugin_configs = self._get_default_config()
                return True
        except Exception as e:
            logger.error(f"加载插件配置失败: {e}")
            return False
    
    def register_builtin_plugins(self) -> None:
        """注册内置插件"""
        try:
            # 注册START插件
            from .builtin.start import (
                ContextSummaryPlugin, EnvironmentCheckPlugin, MetadataCollectorPlugin
            )
            self.registry.register_plugin(ContextSummaryPlugin())
            self.registry.register_plugin(EnvironmentCheckPlugin())
            self.registry.register_plugin(MetadataCollectorPlugin())
            
            # 注册END插件
            from .builtin.end import (
                ResultSummaryPlugin, ExecutionStatsPlugin, 
                FileTrackerPlugin, CleanupManagerPlugin
            )
            self.registry.register_plugin(ResultSummaryPlugin())
            self.registry.register_plugin(ExecutionStatsPlugin())
            self.registry.register_plugin(FileTrackerPlugin())
            self.registry.register_plugin(CleanupManagerPlugin())
            
            logger.info("内置插件注册完成")
            
        except ImportError as e:
            logger.warning(f"无法导入内置插件: {e}")
        except Exception as e:
            logger.error(f"注册内置插件失败: {e}")
    
    def load_external_plugins(self) -> None:
        """加载外部插件"""
        try:
            external_configs = []
            
            # 收集所有外部插件配置
            start_external = self.plugin_configs.get('start_plugins', {}).get('external', [])
            end_external = self.plugin_configs.get('end_plugins', {}).get('external', [])
            external_configs.extend(start_external)
            external_configs.extend(end_external)
            
            for plugin_config in external_configs:
                if not plugin_config.get('enabled', False):
                    continue
                
                try:
                    plugin = self._load_external_plugin(plugin_config)
                    if plugin:
                        self.registry.register_plugin(plugin)
                        logger.info(f"成功加载外部插件: {plugin_config['name']}")
                except Exception as e:
                    logger.error(f"加载外部插件失败 {plugin_config['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"加载外部插件过程中发生错误: {e}")
    
    def _load_external_plugin(self, config: Dict[str, Any]) -> Optional[IPlugin]:
        """加载单个外部插件
        
        Args:
            config: 插件配置
            
        Returns:
            Optional[IPlugin]: 插件实例，加载失败则返回None
        """
        module_name = config.get('module')
        class_name = config.get('class')
        
        if not module_name or not class_name:
            logger.error(f"插件配置缺少module或class: {config}")
            return None
        
        try:
            # 动态导入模块
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            
            # 实例化插件
            plugin = plugin_class()
            
            # 验证插件接口
            if not isinstance(plugin, IPlugin):
                logger.error(f"插件 {class_name} 未实现正确的接口")
                return None
            
            return plugin
            
        except ImportError as e:
            logger.error(f"无法导入插件模块 {module_name}: {e}")
            return None
        except AttributeError as e:
            logger.error(f"插件类 {class_name} 在模块 {module_name} 中不存在: {e}")
            return None
        except Exception as e:
            logger.error(f"实例化插件失败 {class_name}: {e}")
            return None
    
    def get_enabled_plugins(self, plugin_type: PluginType) -> List[IPlugin]:
        """获取启用的插件列表
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            List[IPlugin]: 启用的插件列表，按优先级排序
        """
        if not self._initialized:
            if not self.initialize():
                return []
        
        plugins = []
        
        # 获取配置
        type_key = f"{plugin_type.value}_plugins"
        plugin_configs = self.plugin_configs.get(type_key, {})
        
        # 处理内置插件
        builtin_configs = {c['name']: c for c in plugin_configs.get('builtin', [])}
        for config in builtin_configs.values():
            if config.get('enabled', False):
                plugin = self.registry.get_plugin(config['name'])
                if plugin:
                    # 初始化插件
                    if self._initialize_plugin(plugin, config.get('config', {})):
                        plugins.append((plugin, config.get('priority', 50)))
        
        # 处理外部插件
        external_configs = {c['name']: c for c in plugin_configs.get('external', [])}
        for config in external_configs.values():
            if config.get('enabled', False):
                plugin = self.registry.get_plugin(config['name'])
                if plugin:
                    # 初始化插件
                    if self._initialize_plugin(plugin, config.get('config', {})):
                        plugins.append((plugin, config.get('priority', 50)))
        
        # 按优先级排序
        plugins.sort(key=lambda x: x[1])
        return [plugin for plugin, _ in plugins]
    
    def _initialize_plugin(self, plugin: IPlugin, config: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            plugin: 插件实例
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 验证配置
            errors = plugin.validate_config(config)
            if errors:
                logger.error(f"插件 {plugin.metadata.name} 配置验证失败: {errors}")
                self.registry.set_plugin_status(plugin.metadata.name, PluginStatus.ERROR)
                return False
            
            # 初始化插件
            if plugin.initialize(config):
                self.loaded_plugins[plugin.metadata.name] = plugin
                logger.debug(f"插件 {plugin.metadata.name} 初始化成功")
                return True
            else:
                logger.error(f"插件 {plugin.metadata.name} 初始化失败")
                self.registry.set_plugin_status(plugin.metadata.name, PluginStatus.ERROR)
                return False
                
        except Exception as e:
            logger.error(f"初始化插件失败 {plugin.metadata.name}: {e}")
            self.registry.set_plugin_status(plugin.metadata.name, PluginStatus.ERROR)
            return False
    
    def execute_plugins(self, plugin_type: PluginType, state: Dict[str, Any], 
                       context: PluginContext) -> Dict[str, Any]:
        """执行指定类型的所有插件
        
        Args:
            plugin_type: 插件类型
            state: 当前状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        if not self._initialized:
            if not self.initialize():
                return state
        
        plugins = self.get_enabled_plugins(plugin_type)
        
        if not plugins:
            logger.debug(f"没有启用的 {plugin_type.value} 插件")
            return state
        
        execution_config = self.plugin_configs.get('execution', {})
        parallel_execution = execution_config.get('parallel_execution', False)
        continue_on_error = execution_config.get('error_handling', {}).get('continue_on_error', True)
        
        logger.info(f"开始执行 {len(plugins)} 个 {plugin_type.value} 插件 (并行: {parallel_execution})")
        
        if parallel_execution:
            return self._execute_plugins_parallel(plugins, state, context, continue_on_error)
        else:
            return self._execute_plugins_sequential(plugins, state, context, continue_on_error)
    
    def _execute_plugins_sequential(self, plugins: Sequence[IPlugin], state: Dict[str, Any],
                                  context: PluginContext, continue_on_error: bool) -> Dict[str, Any]:
        """顺序执行插件
        
        Args:
            plugins: 插件列表
            state: 当前状态
            context: 执行上下文
            continue_on_error: 是否在错误时继续执行
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        current_state = state
        execution_config = self.plugin_configs.get('execution', {})
        default_timeout = execution_config.get('timeout', {}).get('default_timeout', 30)
        
        for plugin in plugins:
            plugin_name = plugin.metadata.name
            start_time = time.time()
            
            try:
                logger.debug(f"开始执行插件: {plugin_name}")
                
                # 执行插件（带超时）
                plugin_timeout = execution_config.get('timeout', {}).get('per_plugin_timeout', default_timeout)
                updated_state = self._execute_plugin_with_timeout(plugin, current_state, context, plugin_timeout)
                
                current_state = updated_state
                execution_time = time.time() - start_time
                
                logger.debug(f"插件 {plugin_name} 执行成功，耗时 {execution_time:.2f}s")
                
                # 记录执行信息
                if 'plugin_executions' not in current_state:
                    current_state['plugin_executions'] = []
                
                current_state['plugin_executions'].append({
                    'plugin_name': plugin_name,
                    'plugin_type': plugin.metadata.plugin_type.value,
                    'execution_time': execution_time,
                    'status': 'success',
                    'timestamp': time.time()
                })
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"插件 {plugin_name} 执行失败: {e}")
                
                # 记录错误信息
                if 'plugin_executions' not in current_state:
                    current_state['plugin_executions'] = []
                
                current_state['plugin_executions'].append({
                    'plugin_name': plugin_name,
                    'plugin_type': plugin.metadata.plugin_type.value,
                    'execution_time': execution_time,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                })
                
                if not continue_on_error:
                    raise PluginExecutionError(f"插件 {plugin_name} 执行失败: {e}")
        
        return current_state
    
    def _execute_plugins_parallel(self, plugins: List[IPlugin], state: Dict[str, Any], 
                                 context: PluginContext, continue_on_error: bool) -> Dict[str, Any]:
        """并行执行插件
        
        Args:
            plugins: 插件列表
            state: 当前状态
            context: 执行上下文
            continue_on_error: 是否在错误时继续执行
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        execution_config = self.plugin_configs.get('execution', {})
        max_workers = execution_config.get('max_parallel_plugins', 3)
        default_timeout = execution_config.get('timeout', {}).get('default_timeout', 30)
        
        results = {}
        errors = {}
        
        def execute_plugin(plugin: IPlugin) -> tuple[str, Dict[str, Any] | Exception]:
            """执行单个插件"""
            plugin_name = plugin.metadata.name
            start_time = time.time()
            
            try:
                plugin_timeout = execution_config.get('timeout', {}).get('per_plugin_timeout', default_timeout)
                result = self._execute_plugin_with_timeout(plugin, state, context, plugin_timeout)
                execution_time = time.time() - start_time
                
                # 添加执行信息到结果
                if 'plugin_executions' not in result:
                    result['plugin_executions'] = []
                
                result['plugin_executions'].append({
                    'plugin_name': plugin_name,
                    'plugin_type': plugin.metadata.plugin_type.value,
                    'execution_time': execution_time,
                    'status': 'success',
                    'timestamp': time.time()
                })
                
                return plugin_name, result
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_info = {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin.metadata.plugin_type.value,
                    'execution_time': execution_time,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
                return plugin_name, PluginExecutionError(f"插件 {plugin_name} 执行失败: {e}")
        
        # 使用线程池并行执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有插件任务
            future_to_plugin = {
                executor.submit(execute_plugin, plugin): plugin 
                for plugin in plugins
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_plugin):
                plugin = future_to_plugin[future]
                try:
                    plugin_name, result = future.result()
                    if isinstance(result, Exception):
                        errors[plugin_name] = result
                        if not continue_on_error:
                            raise result
                    else:
                        results[plugin_name] = result
                        logger.debug(f"插件 {plugin_name} 执行成功")
                except Exception as e:
                    logger.error(f"插件 {plugin.metadata.name} 执行失败: {e}")
                    errors[plugin.metadata.name] = e
                if not continue_on_error:
                        raise
        
        # 合并结果
        merged_state = state.copy()
        
        # 合并成功的结果
        for plugin_name, plugin_state in results.items():
            if isinstance(plugin_state, dict):
                merged_state.update(plugin_state)
        
        # 添加错误信息
        if errors:
            merged_state['plugin_errors'] = {
                plugin_name: str(error) for plugin_name, error in errors.items()
            }
        
        return merged_state
    
    def _execute_plugin_with_timeout(self, plugin: IPlugin, state: Dict[str, Any], 
                                   context: PluginContext, timeout: int) -> Dict[str, Any]:
        """带超时的插件执行
        
        Args:
            plugin: 插件实例
            state: 当前状态
            context: 执行上下文
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 更新后的状态
            
        Raises:
            PluginExecutionError: 执行超时或失败
        """
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(plugin.execute, state, context)
                return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise PluginExecutionError(f"插件 {plugin.metadata.name} 执行超时 ({timeout}s)")
        except Exception as e:
            raise PluginExecutionError(f"插件 {plugin.metadata.name} 执行失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            "start_plugins": {
                "builtin": [
                    {"name": "context_summary", "enabled": True, "priority": 10, "config": {}},
                    {"name": "environment_check", "enabled": True, "priority": 20, "config": {}},
                    {"name": "metadata_collector", "enabled": True, "priority": 30, "config": {}}
                ],
                "external": []
            },
            "end_plugins": {
                "builtin": [
                    {"name": "result_summary", "enabled": True, "priority": 10, "config": {}},
                    {"name": "execution_stats", "enabled": True, "priority": 20, "config": {}},
                    {"name": "file_tracker", "enabled": True, "priority": 30, "config": {}},
                    {"name": "cleanup_manager", "enabled": True, "priority": 40, "config": {}}
                ],
                "external": []
            },
            "execution": {
                "parallel_execution": False,
                "max_parallel_plugins": 3,
                "error_handling": {
                    "continue_on_error": True,
                    "log_errors": True,
                    "fail_on_critical_error": False
                },
                "timeout": {
                    "default_timeout": 30,
                    "per_plugin_timeout": 60
                }
            }
        }
    
    def cleanup(self) -> None:
        """清理插件管理器资源"""
        try:
            # 清理所有已加载的插件
            for plugin in self.loaded_plugins.values():
                try:
                    plugin.cleanup()
                except Exception as e:
                    logger.error(f"清理插件资源失败 {plugin.metadata.name}: {e}")
            
            # 清空注册表
            self.registry.clear()
            self.loaded_plugins.clear()
            self._initialized = False
            
            logger.info("插件管理器清理完成")
            
        except Exception as e:
            logger.error(f"插件管理器清理失败: {e}")
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self.registry.get_registry_stats()
        stats.update({
            "initialized": self._initialized,
            "config_path": self.config_path,
            "loaded_plugins_count": len(self.loaded_plugins),
            "config_loaded": bool(self.plugin_configs)
        })
        return stats