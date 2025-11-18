"""START节点实现

支持插件化扩展的START节点。
"""

import time
import logging
from typing import Dict, Any, Optional

from .base import BaseNode
from ..interfaces import NodeExecutionResult
from ..decorators import node
from ...states import WorkflowState
from ..plugins.manager import PluginManager
from ..plugins.interfaces import PluginType, PluginContext


logger = logging.getLogger(__name__)


@node("start_node")
class StartNode(BaseNode):
    """START节点 - 支持插件化扩展
    
    在工作流开始时执行各种初始化和准备操作。
    """
    
    def __init__(self, plugin_config_path: Optional[str] = None):
        """初始化START节点
        
        Args:
            plugin_config_path: 插件配置文件路径
        """
        self.plugin_config_path = plugin_config_path
        self.plugin_manager = PluginManager(plugin_config_path)
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
            self._initialized = True
    
    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
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
            workflow_id=state.get('workflow_id', 'unknown'),
            thread_id=state.get('thread_id'),
            session_id=state.get('session_id'),
            execution_start_time=start_time,
            metadata=config.get('context_metadata', {})
        )
        
        # 执行START插件
        try:
            updated_state = self.plugin_manager.execute_plugins(
                PluginType.START, 
                state, 
                context
            )
            
            # 添加执行元数据
            execution_time = time.time() - start_time
            updated_state['start_metadata'] = updated_state.get('start_metadata', {})
            updated_state['start_metadata'].update({
                'execution_time': execution_time,
                'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.START)),
                'timestamp': start_time,
                'node_type': self.node_type,
                'success': True
            })
            
            logger.info(f"START节点执行完成，耗时 {execution_time:.2f}s")
            
            return NodeExecutionResult(
                state=updated_state,
                next_node=config.get('next_node'),
                metadata=updated_state.get('start_metadata', {})
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"START节点执行失败: {e}")
            
            # 添加错误信息到状态
            state['start_metadata'] = state.get('start_metadata', {})
            state['start_metadata'].update({
                'execution_time': execution_time,
                'plugins_executed': len(self.plugin_manager.get_enabled_plugins(PluginType.START)),
                'timestamp': start_time,
                'node_type': self.node_type,
                'success': False,
                'error': str(e)
            })
            
            return NodeExecutionResult(
                state=state,
                next_node=config.get('error_next_node', 'error_handler'),
                metadata={
                    'error': str(e),
                    'execution_time': execution_time,
                    'node_type': self.node_type
                }
            )
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置Schema
        
        Returns:
            Dict[str, Any]: 配置Schema
        """
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
            return self.plugin_manager.get_manager_stats()
        else:
            return {"initialized": False}
    
    def cleanup(self) -> None:
        """清理节点资源"""
        try:
            if self._initialized:
                self.plugin_manager.cleanup()
                self._initialized = False
        except Exception as e:
            logger.error(f"清理START节点资源失败: {e}")