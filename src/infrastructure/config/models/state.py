"""状态管理配置数据模型

提供基础设施层的状态配置数据结构，不包含业务逻辑。
"""

from typing import Dict, Any, Optional
from .base import ConfigData


class StateConfigData(ConfigData):
    """状态配置数据
    
    纯数据容器，用于状态管理配置的基础数据结构。
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """初始化状态配置数据
        
        Args:
            data: 配置数据字典
        """
        super().__init__(data)
        
        # 设置默认数据结构
        if not self.data:
            self.data = self._get_default_data()
    
    def _get_default_data(self) -> Dict[str, Any]:
        """获取默认配置数据
        
        Returns:
            默认配置数据字典
        """
        return {
            'core': {
                'default_ttl': 3600,
                'max_states': 10000,
                'cleanup_interval': 300
            },
            'serializer': {
                'format': 'json',
                'compression': True,
                'compression_threshold': 1024
            },
            'cache': {
                'enabled': True,
                'max_size': 1000,
                'ttl': 300,
                'eviction_policy': 'lru',
                'enable_serialization': False,
                'serialization_format': 'json'
            },
            'storage': {
                'default_type': 'memory',
                'memory': {
                    'max_size': 10000
                },
                'sqlite': {
                    'database_path': 'data/states.db',
                    'connection_pool_size': 10,
                    'compression': True,
                    'compression_threshold': 1024
                },
                'file': {
                    'base_path': 'data/states',
                    'format': 'json',
                    'compression': False,
                    'create_subdirs': True
                }
            },
            'validation': {
                'enabled': True,
                'strict_mode': False,
                'custom_validators': []
            },
            'lifecycle': {
                'auto_cleanup': True,
                'cleanup_interval': 300,
                'event_handlers': []
            },
            'specialized': {
                'workflow': {
                    'max_iterations': 100,
                    'message_history_limit': 1000,
                    'auto_save': True
                },
                'tools': {
                    'context_isolation': True,
                    'auto_expiration': True,
                    'default_ttl': 1800
                },
                'sessions': {
                    'auto_cleanup': True,
                    'max_inactive_duration': 3600
                },
                'threads': {
                    'auto_cleanup': True,
                    'max_inactive_duration': 7200
                },
                'checkpoints': {
                    'auto_cleanup': True,
                    'max_checkpoints_per_thread': 50,
                    'cleanup_interval': 600
                }
            },
            'monitoring': {
                'enabled': True,
                'statistics_interval': 60,
                'performance_tracking': True,
                'memory_tracking': True
            },
            'error_handling': {
                'retry_attempts': 3,
                'retry_delay': 1.0,
                'fallback_to_memory': True,
                'log_errors': True
            },
            'development': {
                'debug_mode': False,
                'verbose_logging': False,
                'enable_profiling': False,
                'mock_storage': False
            }
        }
    
    def get_core_config(self) -> Dict[str, Any]:
        """获取核心配置
        
        Returns:
            核心配置字典
        """
        return self.get('core', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置
        
        Returns:
            存储配置字典
        """
        return self.get('storage', {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置
        
        Returns:
            缓存配置字典
        """
        return self.get('cache', {})
    
    def get_serializer_config(self) -> Dict[str, Any]:
        """获取序列化配置
        
        Returns:
            序列化配置字典
        """
        return self.get('serializer', {})
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流配置
        
        Returns:
            工作流配置字典
        """
        return self.get('specialized.workflow', {})
    
    def get_tools_config(self) -> Dict[str, Any]:
        """获取工具配置
        
        Returns:
            工具配置字典
        """
        return self.get('specialized.tools', {})
    
    def get_sessions_config(self) -> Dict[str, Any]:
        """获取会话配置
        
        Returns:
            会话配置字典
        """
        return self.get('specialized.sessions', {})
    
    def get_threads_config(self) -> Dict[str, Any]:
        """获取线程配置
        
        Returns:
            线程配置字典
        """
        return self.get('specialized.threads', {})
    
    def get_checkpoints_config(self) -> Dict[str, Any]:
        """获取检查点配置
        
        Returns:
            检查点配置字典
        """
        return self.get('specialized.checkpoints', {})


__all__ = [
    "StateConfigData"
]