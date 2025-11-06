"""插件管理器

负责插件的加载、配置和执行管理。
"""

import importlib
import logging
import time
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Sequence
from collections import defaultdict

from .interfaces import (
    IPlugin, IStartPlugin, IEndPlugin, IHookPlugin, PluginType, PluginStatus,
    PluginContext, HookContext, HookPoint, HookExecutionResult,
    PluginError, PluginInitializationError, PluginExecutionError
)
from .registry import PluginRegistry
from ..states import WorkflowState
from ..registry import NodeExecutionResult


logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器
    
    负责插件的完整生命周期管理。
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
        
        # Hook相关
        self._hook_plugins: Dict[str, List[IHookPlugin]] = defaultdict(list)
        self._execution_counters: Dict[str, int] = defaultdict(int)
        self._performance_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
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
            
            # 注册Hook插件
            from .builtin.hooks import (
                DeadLoopDetectionPlugin, PerformanceMonitoringPlugin,
                ErrorRecoveryPlugin, LoggingPlugin, MetricsCollectionPlugin
            )
            self.registry.register_plugin(DeadLoopDetectionPlugin())
            self.registry.register_plugin(PerformanceMonitoringPlugin())
            self.registry.register_plugin(ErrorRecoveryPlugin())
            self.registry.register_plugin(LoggingPlugin())
            self.registry.register_plugin(MetricsCollectionPlugin())
            
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
            hook_external = self.plugin_configs.get('hook_plugins', {}).get('external', [])
            external_configs.extend(start_external)
            external_configs.extend(end_external)
            external_configs.extend(hook_external)
            
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
    
    def get_enabled_hook_plugins(self, node_type: str) -> List[IHookPlugin]:
        """获取指定节点的Hook插件列表
        
        Args:
            node_type: 节点类型
            
        Returns:
            List[IHookPlugin]: Hook插件列表
        """
        if not self._initialized:
            if not self.initialize():
                return []
        
        # 从缓存获取
        if node_type in self._hook_plugins:
            return self._hook_plugins[node_type]
        
        plugins = []
        
        # 获取Hook插件配置
        hook_configs = self.plugin_configs.get('hook_plugins', {})
        
        # 处理全局Hook插件
        global_configs = {c['name']: c for c in hook_configs.get('global', [])}
        for config in global_configs.values():
            if config.get('enabled', False):
                plugin = self.registry.get_plugin(config['name'])
                if plugin and isinstance(plugin, IHookPlugin):
                    # 初始化插件
                    if self._initialize_plugin(plugin, config.get('config', {})):
                        plugins.append((plugin, config.get('priority', 50)))
        
        # 处理节点特定Hook插件
        node_configs = hook_configs.get('node_specific', {}).get(node_type, [])
        for config in node_configs:
            if config.get('enabled', False):
                plugin = self.registry.get_plugin(config['name'])
                if plugin and isinstance(plugin, IHookPlugin):
                    # 初始化插件
                    if self._initialize_plugin(plugin, config.get('config', {})):
                        plugins.append((plugin, config.get('priority', 50)))
        
        # 按优先级排序
        plugins.sort(key=lambda x: x[1])
        hook_plugins = [plugin for plugin, _ in plugins]
        
        # 缓存结果
        self._hook_plugins[node_type] = hook_plugins
        
        return hook_plugins
    
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
                
                # 为Hook插件设置执行服务
                if isinstance(plugin, IHookPlugin):
                    plugin.set_execution_service(self)
                
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
    
    def execute_hooks(self, hook_point: HookPoint, context: HookContext) -> HookExecutionResult:
        """执行指定Hook点的所有Hook插件
        
        Args:
            hook_point: Hook执行点
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: 合并后的Hook执行结果
        """
        if not self._initialized:
            if not self.initialize():
                return HookExecutionResult(should_continue=True)
        
        hook_plugins = self.get_enabled_hook_plugins(context.node_type)
        
        # 过滤支持当前Hook点的插件
        applicable_plugins = [
            plugin for plugin in hook_plugins 
            if hook_point in plugin.get_supported_hook_points()
        ]
        
        if not applicable_plugins:
            return HookExecutionResult(should_continue=True)
        
        logger.debug(f"开始执行 {len(applicable_plugins)} 个 {hook_point.value} Hook插件")
        
        # 执行Hook插件
        modified_state = context.state
        modified_result = context.execution_result
        force_next_node = None
        should_continue = True
        metadata: Dict[str, Any] = {"executed_hooks": []}
        
        for plugin in applicable_plugins:
            try:
                hook_start_time = time.time()
                
                # 根据Hook点调用相应方法
                if hook_point == HookPoint.BEFORE_EXECUTE:
                    result = plugin.before_execute(context)
                elif hook_point == HookPoint.AFTER_EXECUTE:
                    result = plugin.after_execute(context)
                elif hook_point == HookPoint.ON_ERROR:
                    result = plugin.on_error(context)
                else:
                    continue
                
                hook_execution_time = time.time() - hook_start_time
                
                # 记录Hook执行信息
                metadata["executed_hooks"].append({
                    "plugin_name": plugin.metadata.name,
                    "execution_time": hook_execution_time,
                    "success": True
                })
                
                # 应用Hook结果
                if not result.should_continue:
                    should_continue = False
                
                if result.modified_state:
                    modified_state = result.modified_state
                
                if result.modified_result:
                    modified_result = result.modified_result
                
                if result.force_next_node:
                    force_next_node = result.force_next_node
                
                # 合并元数据
                if result.metadata:
                    metadata.update(result.metadata)
                
                # 如果Hook要求停止执行，则中断后续Hook
                if not should_continue:
                    logger.debug(f"Hook {plugin.metadata.name} 要求停止执行")
                    break
                    
            except Exception as e:
                logger.error(f"执行Hook {plugin.metadata.name} 时发生错误: {e}")
                metadata["executed_hooks"].append({
                    "plugin_name": plugin.metadata.name,
                    "success": False,
                    "error": str(e)
                })
                # 继续执行其他Hook，不中断整个流程
        
        return HookExecutionResult(
            should_continue=should_continue,
            modified_state=modified_state,
            modified_result=modified_result,
            force_next_node=force_next_node,
            metadata=metadata
        )
    
    def execute_with_hooks(
        self,
        node_type: str,
        state: 'WorkflowState',
        config: Dict[str, Any],
        node_executor_func: Callable[['WorkflowState', Dict[str, Any]], 'NodeExecutionResult']
    ) -> 'NodeExecutionResult':
        """统一的Hook执行接口
        
        Args:
            node_type: 节点类型
            state: 当前状态
            config: 节点配置
            node_executor_func: 节点执行函数
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        from ..registry import NodeExecutionResult
        
        # 创建前置Hook上下文
        before_context = HookContext(
            node_type=node_type,
            state=state,
            config=config,
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        # 执行前置Hook
        before_result = self.execute_hooks(HookPoint.BEFORE_EXECUTE, before_context)
        
        # 检查是否需要中断执行
        if not before_result.should_continue:
            return NodeExecutionResult(
                state=before_result.modified_state or state,
                next_node=before_result.force_next_node,
                metadata={
                    "interrupted_by_hooks": True,
                    "hook_metadata": before_result.metadata
                }
            )
        
        # 更新状态（如果Hook修改了状态）
        if before_result.modified_state:
            state = before_result.modified_state
        
        # 执行节点逻辑
        try:
            result = node_executor_func(state, config)
            
            # 创建后置Hook上下文
            after_context = HookContext(
                node_type=node_type,
                state=result.state,
                config=config,
                hook_point=HookPoint.AFTER_EXECUTE,
                execution_result=result
            )
            
            # 执行后置Hook
            after_result = self.execute_hooks(HookPoint.AFTER_EXECUTE, after_context)
            
            # 应用Hook结果
            if after_result.modified_state:
                result.state = after_result.modified_state
            
            if after_result.force_next_node:
                result.next_node = after_result.force_next_node
            
            if after_result.metadata:
                if result.metadata is None:
                    result.metadata = {}
                result.metadata.update(after_result.metadata)
            
            return result
            
        except Exception as e:
            # 创建错误Hook上下文
            error_context = HookContext(
                node_type=node_type,
                state=state,
                config=config,
                hook_point=HookPoint.ON_ERROR,
                error=e
            )
            
            # 执行错误Hook
            error_result = self.execute_hooks(HookPoint.ON_ERROR, error_context)
            
            # 检查Hook是否处理了错误
            if not error_result.should_continue:
                return NodeExecutionResult(
                    state=error_result.modified_state or state,
                    next_node=error_result.force_next_node or "error_handler",
                    metadata={
                        "error_handled_by_hooks": True,
                        "original_error": str(e),
                        "hook_metadata": error_result.metadata
                    }
                )
            
            # 如果Hook没有处理错误，重新抛出异常
            raise e
    
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
                }
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
    
    # Hook执行服务接口实现
    def get_execution_count(self, node_type: str) -> int:
        """获取节点执行次数
        
        Args:
            node_type: 节点类型
            
        Returns:
            int: 执行次数
        """
        return self._execution_counters[node_type]
    
    def increment_execution_count(self, node_type: str) -> int:
        """增加节点执行计数
        
        Args:
            node_type: 节点类型
            
        Returns:
            int: 增加后的执行次数
        """
        self._execution_counters[node_type] += 1
        return self._execution_counters[node_type]
    
    def update_performance_stats(
        self, 
        node_type: str, 
        execution_time: float, 
        success: bool = True
    ) -> None:
        """更新性能统计
        
        Args:
            node_type: 节点类型
            execution_time: 执行时间
            success: 是否成功
        """
        stats = self._performance_stats[node_type]
        
        if "total_executions" not in stats:
            stats["total_executions"] = 0
            stats["successful_executions"] = 0
            stats["failed_executions"] = 0
            stats["total_execution_time"] = 0.0
            stats["min_execution_time"] = float('inf')
            stats["max_execution_time"] = 0.0
        
        stats["total_executions"] += 1
        stats["total_execution_time"] += execution_time
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        stats["min_execution_time"] = min(stats["min_execution_time"], execution_time)
        stats["max_execution_time"] = max(stats["max_execution_time"], execution_time)
        stats["avg_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
    
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
            self._hook_plugins.clear()
            self._execution_counters.clear()
            self._performance_stats.clear()
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
            "config_loaded": bool(self.plugin_configs),
            "hook_plugins_count": sum(len(plugins) for plugins in self._hook_plugins.values()),
            "performance_stats": dict(self._performance_stats)
        })
        return stats