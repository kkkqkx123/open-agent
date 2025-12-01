"""END节点实现 - 使用新的Hook系统

支持插件化扩展的END节点，使用新的Node Hook管理器。
"""

import time
from src.services.logger import get_logger
from typing import Dict, Any, Optional

from .registry import node
from .sync_node import SyncNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.interfaces import IState
from src.interfaces.state.workflow import IWorkflowState
from src.core.workflow.plugins.manager import PluginManager
from src.core.workflow.plugins.hooks.executor import HookExecutor
from src.interfaces.workflow.plugins import PluginType, PluginContext

logger = get_logger(__name__)


@node("end_node")
class EndNode(SyncNode):
    """END节点 - 支持插件化扩展
    
    在工作流结束时执行各种清理、统计和报告操作。
    使用新的Node Hook管理器来处理Hook插件。
    
    这是一个纯同步节点，用于工作流清理。
    """
    
    def __init__(self, plugin_config_path: Optional[str] = None):
        """初始化END节点
        
        Args:
            plugin_config_path: 插件配置文件路径
        """
        self.plugin_config_path = plugin_config_path
        # 保留原有的PluginManager用于END插件
        self.plugin_manager = PluginManager(plugin_config_path)
        # 新增HookExecutor用于Hook插件
        self.node_hook_manager = HookExecutor()
        self._initialized = False
    
    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "end_node"
    
    def _ensure_initialized(self) -> None:
        """确保插件管理器已初始化"""
        if not self._initialized:
            if not self.plugin_manager.initialize():
                raise RuntimeError("插件管理器初始化失败")
            # HookExecutor不需要初始化，直接使用
            logger.debug("HookExecutor已准备就绪")
            self._initialized = True
    
    def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行END节点逻辑
        
        Args:
            state: 当前工作流状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        self._ensure_initialized()
        
        # 记录开始时间
        start_time = time.time()
        
        logger.info("END节点开始执行")
        
        # 创建执行上下文
        context = PluginContext(
            workflow_id=state.get_data('workflow_id', 'unknown'),
            thread_id=state.get_data('thread_id'),
            session_id=state.get_data('session_id'),
            execution_start_time=state.get_data('start_metadata', {}).get('timestamp'),
            metadata=config.get('context_metadata', {})
        )
        
        # 定义节点执行函数
        def _execute_end_logic(state: IWorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
            """实际的END节点执行逻辑"""
            # 执行END插件
            try:
                # 将WorkflowState转换为字典，因为插件管理器期望字典类型
                state_dict = state.to_dict() if hasattr(state, 'to_dict') else state
                # 确保传递字典类型
                if not isinstance(state_dict, dict):
                    state_dict = state_dict.to_dict() if hasattr(state_dict, 'to_dict') else {}
                
                updated_state_dict = self.plugin_manager.execute_plugins(
                    PluginType.END, 
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
                    updated_state['end_metadata'] = updated_state.get_data('end_metadata', {})
                    updated_state['end_metadata'].update({
                        'execution_time': execution_time,
                        'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.END)),
                        'timestamp': time.time(),
                        'node_type': self.node_type,
                        'success': True
                    })
                else:
                    # WorkflowState对象
                    end_metadata = updated_state.get_metadata('end_metadata', {})
                    end_metadata.update({
                        'execution_time': execution_time,
                        'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.END)),
                        'timestamp': time.time(),
                        'node_type': self.node_type,
                        'success': True
                    })
                    updated_state.set_metadata('end_metadata', end_metadata)
                
                # 计算总执行时间
                if context.execution_start_time:
                    total_execution_time = time.time() - context.execution_start_time
                    if isinstance(updated_state, dict):
                        updated_state['end_metadata']['total_execution_time'] = total_execution_time
                        updated_state['end_metadata']['total_execution_time_formatted'] = self._format_duration(total_execution_time)
                    else:
                        end_metadata = updated_state.get_metadata('end_metadata', {})
                        end_metadata['total_execution_time'] = total_execution_time
                        end_metadata['total_execution_time_formatted'] = self._format_duration(total_execution_time)
                        updated_state.set_metadata('end_metadata', end_metadata)
                
                logger.info(f"END节点执行完成，耗时 {execution_time:.2f}s")
                
                # 标记工作流完成
                if isinstance(updated_state, dict):
                    updated_state['workflow_completed'] = True
                    updated_state['completion_timestamp'] = time.time()
                else:
                    updated_state.set_data('workflow_completed', True)
                    updated_state.set_data('completion_timestamp', time.time())
                
                # 确保 updated_state 是 IState 类型
                if isinstance(updated_state, dict):
                    # 如果是字典，需要转换回 IState 对象
                    if hasattr(state, 'from_dict'):
                        updated_state = state.__class__.from_dict(updated_state)
                
                return NodeExecutionResult(
                    state=updated_state,
                    next_node=None,  # END节点没有下一个节点
                    metadata=updated_state.get_data('end_metadata', {}) if hasattr(updated_state, 'get') else updated_state.get_data('end_metadata', {})
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"END节点执行失败: {e}")
                
                # 添加错误信息到状态
                if isinstance(state, dict):
                    state['end_metadata'] = state.get_data('end_metadata', {})
                    state['end_metadata'].update({
                        'execution_time': execution_time,
                        'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.END)),
                        'timestamp': time.time(),
                        'node_type': self.node_type,
                        'success': False,
                        'error': str(e)
                    })
                    
                    # 即使出错也标记工作流完成
                    state['workflow_completed'] = True
                    state['completion_timestamp'] = time.time()
                    state['workflow_failed'] = True
                else:
                    # WorkflowState对象
                    end_metadata = state.get_metadata('end_metadata', {})
                    end_metadata.update({
                        'execution_time': execution_time,
                        'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.END)),
                        'timestamp': time.time(),
                        'node_type': self.node_type,
                        'success': False,
                        'error': str(e)
                    })
                    state.set_metadata('end_metadata', end_metadata)
                    
                    # 即使出错也标记工作流完成
                    state.set_data('workflow_completed', True)
                    state.set_data('completion_timestamp', time.time())
                    state.set_data('workflow_failed', True)
                
                return NodeExecutionResult(
                    state=state,  # 确保传递WorkflowState类型
                    next_node=None,  # END节点没有下一个节点
                    metadata={
                        'error': str(e),
                        'execution_time': execution_time,
                        'node_type': self.node_type,
                        'workflow_failed': True
                    }
                )
        
        # 使用Node Hook管理器执行（带Hook）
        try:
            return self.node_hook_manager.execute_with_hooks(
                node_type=self.node_type,
                state=state,
                config=config,
                node_executor_func=_execute_end_logic
            )
        except Exception as e:
            logger.error(f"Node Hook执行失败，回退到直接执行: {e}")
            # 如果Hook执行失败，回退到直接执行
            return _execute_end_logic(state, config)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置Schema
        
        Returns:
            Dict[str, Any]: 配置Schema
        """
        try:
            from ...config.schema_generator import generate_node_schema
            return generate_node_schema("end_node")
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
                "error_next_node": {
                    "type": "string",
                    "description": "错误时跳转的节点名称（END节点通常不使用）"
                },
                "context_metadata": {
                    "type": "object",
                    "description": "上下文元数据"
                },
                "output_directory": {
                    "type": "string",
                    "description": "输出目录"
                },
                "generate_reports": {
                    "type": "boolean",
                    "description": "是否生成报告",
                    "default": True
                },
                "save_results": {
                    "type": "boolean",
                    "description": "是否保存结果",
                    "default": True
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
        
        # 验证错误下一个节点
        error_next_node = config.get('error_next_node')
        if error_next_node and not isinstance(error_next_node, str):
            errors.append("error_next_node 必须是字符串类型")
        
        # 验证上下文元数据
        context_metadata = config.get('context_metadata')
        if context_metadata and not isinstance(context_metadata, dict):
            errors.append("context_metadata 必须是对象类型")
        
        # 验证输出目录
        output_directory = config.get('output_directory')
        if output_directory and not isinstance(output_directory, str):
            errors.append("output_directory 必须是字符串类型")
        
        # 验证生成报告
        generate_reports = config.get('generate_reports')
        if generate_reports is not None and not isinstance(generate_reports, bool):
            errors.append("generate_reports 必须是布尔类型")
        
        # 验证保存结果
        save_results = config.get('save_results')
        if save_results is not None and not isinstance(save_results, bool):
            errors.append("save_results 必须是布尔类型")
        
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
    
    def get_workflow_summary(self, state: IWorkflowState) -> Dict[str, Any]:
        """获取工作流摘要
        
        Args:
            state: 当前工作流状态
            
        Returns:
            Dict[str, Any]: 工作流摘要
        """
        summary = {
            "workflow_id": state.get_data('workflow_id'),
            "completed": state.get_data('workflow_completed', False),
            "failed": state.get_data('workflow_failed', False),
            "completion_timestamp": state.get_data('completion_timestamp')
        }
        
        # 添加开始元数据
        start_metadata = state.get_data('start_metadata', {})
        if start_metadata:
            summary["start"] = {
                "timestamp": start_metadata.get('timestamp'),
                "execution_time": start_metadata.get('execution_time'),
                "plugins_executed": start_metadata.get('plugins_executed'),
                "success": start_metadata.get('success', False)
            }
        
        # 添加结束元数据
        end_metadata = state.get_data('end_metadata', {})
        if end_metadata:
            summary["end"] = {
                "timestamp": end_metadata.get('timestamp'),
                "execution_time": end_metadata.get('execution_time'),
                "plugins_executed": end_metadata.get('plugins_executed'),
                "success": end_metadata.get('success', False),
                "total_execution_time": end_metadata.get('total_execution_time')
            }
        
        # 添加插件执行信息
        if state.get_data("plugin_executions"):
            plugin_executions = state.get_data("plugin_executions")
            summary["plugin_executions"] = {
                "total": len(plugin_executions),
                "successful": len([p for p in plugin_executions if p.get("status") == "success"]),
                "failed": len([p for p in plugin_executions if p.get("status") == "error"]),
                "total_time": sum(p.get("execution_time", 0) for p in plugin_executions)
            }
        
        # 添加错误信息
        if state.get_data("errors"):
            summary["errors"] = {
                "count": len(state.get_data("errors")),
                "details": state.get_data("errors")
            }
        
        # 添加输出信息
        if state.get_data("output"):
            summary["output"] = state.get_data("output")
        
        return summary
    
    def _format_duration(self, seconds: float) -> str:
        """格式化持续时间
        
        Args:
            seconds: 秒数
            
        Returns:
            str: 格式化的时间字符串
        """
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.0f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            return f"{hours}h {remaining_minutes}m"
    
    def cleanup(self) -> None:
        """清理节点资源"""
        try:
            if self._initialized:
                self.plugin_manager.cleanup()
                self.node_hook_manager.cleanup()
                self._initialized = False
        except Exception as e:
            logger.error(f"清理END节点资源失败: {e}")