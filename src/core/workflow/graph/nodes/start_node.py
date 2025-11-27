"""START节点实现 - 使用新的Hook系统

支持插件化扩展的START节点，使用新的Node Hook管理器。
"""

import time
import logging
from typing import Dict, Any, Optional, Union

from .registry import node
from .sync_node import SyncNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.interfaces import IState
from src.interfaces.state.workflow import IWorkflowState
from src.core.workflow.plugins.manager import PluginManager
from src.core.workflow.plugins.hooks.executor import HookExecutor
from src.interfaces.workflow.plugins import PluginType, PluginContext


logger = logging.getLogger(__name__)


@node("start_node")
class StartNode(SyncNode):
    """START节点 - 支持插件化扩展
    
    在工作流开始时执行各种初始化和准备操作。
    使用新的Node Hook管理器来处理Hook插件。
    
    这是一个纯同步节点，用于工作流初始化。
    """
    
    def __init__(self, plugin_config_path: Optional[str] = None):
        """初始化START节点
        
        Args:
            plugin_config_path: 插件配置文件路径
        """
        self.plugin_config_path = plugin_config_path
        # 保留原有的PluginManager用于START插件
        self.plugin_manager = PluginManager(plugin_config_path)
        # 新增NodeHookManager用于Hook插件
        self.node_hook_manager = HookExecutor()
        self._initialized = False
    
    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "start_node"
    
    def _ensure_initialized(self) -> None:
        """确保插件管理器已初始化"""
        if not self._initialized:
            if not self.plugin_manager.initialize():
                raise RuntimeError("插件管理器初始化失败")
            # HookExecutor不需要初始化，直接使用
            logger.debug("HookExecutor已准备就绪")
            self._initialized = True
    
    def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行START节点逻辑
        
        Args:
            state: 当前工作流状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        self._ensure_initialized()
        
        # 记录开始时间
        start_time = time.time()
        
        logger.info("START节点开始执行")
        
        # 创建执行上下文
        context = PluginContext(
            workflow_id=state.get_data('workflow_id', 'unknown'),
            thread_id=state.get_data('thread_id'),
            session_id=state.get_data('session_id'),
            execution_start_time=start_time,
            metadata=config.get('context_metadata', {})
        )
        
        # 定义节点执行函数
        def _execute_start_logic(state: IWorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
            """实际的START节点执行逻辑"""
            # 执行START插件
            try:
                # 将WorkflowState转换为字典，因为插件管理器期望字典类型
                state_dict = state.to_dict() if hasattr(state, 'to_dict') else state
                # 确保传递字典类型
                if not isinstance(state_dict, dict):
                    state_dict = state_dict.to_dict() if hasattr(state_dict, 'to_dict') else {}
                
                updated_state_dict = self.plugin_manager.execute_plugins(
                    PluginType.START, 
                    state_dict,  # 确保传递字典类型
                    context
                )
                
                # 将字典转换回原始状态对象
                if hasattr(state, 'from_dict'):
                    updated_state = state.__class__.from_dict(updated_state_dict)
                else:
                    # 如果没有from_dict方法，直接使用字典
                    updated_state = state  # 保持原始状态类型
                
                # 添加执行元数据
                execution_time = time.time() - start_time
                if isinstance(updated_state, dict):
                    updated_state['start_metadata'] = updated_state.get_data('start_metadata', {})
                    updated_state['start_metadata'].update({
                        'execution_time': execution_time,
                        'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.START)),
                        'timestamp': start_time,
                        'node_type': self.node_type,
                        'success': True
                    })
                else:
                    # WorkflowState对象
                    start_metadata = updated_state.get_metadata('start_metadata', {})
                    start_metadata.update({
                        'execution_time': execution_time,
                        'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.START)),
                        'timestamp': start_time,
                        'node_type': self.node_type,
                        'success': True
                    })
                    updated_state.set_metadata('start_metadata', start_metadata)
                
                logger.info(f"START节点执行完成，耗时 {execution_time:.2f}s")
                
                return NodeExecutionResult(
                    state=updated_state,  # 确保传递WorkflowState类型
                    next_node=config.get('next_node'),
                    metadata=updated_state.get_data('start_metadata', {}) if not isinstance(updated_state, dict) else updated_state.get_data('start_metadata', {})
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"START节点执行失败: {e}")
                
                # 添加错误信息到状态
                if isinstance(state, dict):
                    state['start_metadata'] = state.get_data('start_metadata', {})
                    state['start_metadata'].update({
                        'execution_time': execution_time,
                        'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.START)),
                        'timestamp': start_time,
                        'node_type': self.node_type,
                        'success': False,
                        'error': str(e)
                    })
                else:
                    # WorkflowState对象
                    start_metadata = state.get_metadata('start_metadata', {})
                    start_metadata.update({
                        'execution_time': execution_time,
                        'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.START)),
                        'timestamp': start_time,
                        'node_type': self.node_type,
                        'success': False,
                        'error': str(e)
                    })
                    state.set_metadata('start_metadata', start_metadata)
                
                return NodeExecutionResult(
                    state=state,  # 确保传递WorkflowState类型
                    next_node=config.get('error_next_node', 'error_handler'),
                    metadata={
                        'error': str(e),
                        'execution_time': execution_time,
                        'node_type': self.node_type
                    }
                )
        
        # 使用Node Hook管理器执行（带Hook）
        try:
            return self.node_hook_manager.execute_with_hooks(
                node_type=self.node_type,
                state=state,
                config=config,
                node_executor_func=_execute_start_logic
            )
        except Exception as e:
            logger.error(f"Node Hook执行失败，回退到直接执行: {e}")
            # 如果Hook执行失败，回退到直接执行
            return _execute_start_logic(state, config)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置Schema
        
        Returns:
            Dict[str, Any]: 配置Schema
        """
        try:
            from ...config.schema_generator import generate_node_schema
            return generate_node_schema("start_node")
        except Exception as e:
            logger.warning(f"无法从配置文件生成Schema，使用默认Schema: {e}")
            return self._get_fallback_schema()
    
    def _get_fallback_schema(self) -> Dict[str, Any]:
        """获取备用Schema（当配置文件不可用时）"""
        return {
            "type": "object",
            "properties": {
                "plugin_config_path": {
                    "type": "string",
                    "description": "插件配置文件路径"
                },
                "next_node": {
                    "type": "string",
                    "description": "下一个节点名称"
                },
                "error_next_node": {
                    "type": "string",
                    "description": "错误时跳转的节点名称"
                },
                "context_metadata": {
                    "type": "object",
                    "description": "上下文元数据"
                }
            },
            "required": []
        }
    
    def validate_config(self, config: Dict[str, Any]) -> list:
        """验证配置
        
        Args:
            config: 节点配置
            
        Returns:
            list: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证插件配置路径
        plugin_config_path = config.get('plugin_config_path')
        if plugin_config_path and not isinstance(plugin_config_path, str):
            errors.append("plugin_config_path 必须是字符串类型")
        
        # 验证下一个节点
        next_node = config.get('next_node')
        if next_node and not isinstance(next_node, str):
            errors.append("next_node 必须是字符串类型")
        
        # 验证错误下一个节点
        error_next_node = config.get('error_next_node')
        if error_next_node and not isinstance(error_next_node, str):
            errors.append("error_next_node 必须是字符串类型")
        
        # 验证上下文元数据
        context_metadata = config.get('context_metadata')
        if context_metadata and not isinstance(context_metadata, dict):
            errors.append("context_metadata 必须是对象类型")
        
        return errors
    
    def get_plugin_manager_stats(self) -> Dict[str, Any]:
        """获取插件管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if self._initialized:
            stats = {
                "plugin_manager": self.plugin_manager.get_manager_stats(),
                "hook_executor": self.node_hook_manager.get_performance_stats()
            }
            return stats
        else:
            return {"initialized": False}
    
    def cleanup(self) -> None:
        """清理节点资源"""
        try:
            if self._initialized:
                self.plugin_manager.cleanup()
                self.node_hook_manager.cleanup()
                self._initialized = False
        except Exception as e:
            logger.error(f"清理START节点资源失败: {e}")