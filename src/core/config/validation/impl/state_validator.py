"""状态配置验证器

提供核心层的状态配置验证功能，包含业务逻辑验证。
"""

from typing import Dict, Any

from src.infrastructure.config.validation.base_validator import BaseConfigValidator
from src.interfaces.common_domain import IValidationResult


class StateConfigValidator(BaseConfigValidator):
    """状态配置验证器
    
    提供状态管理配置的验证功能，基于基础设施层的基础验证器。
    """
    
    def __init__(self, **kwargs):
        """初始化状态配置验证器"""
        super().__init__("StateConfigValidator", **kwargs)
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        return module_type == "state"
    
    def _validate_custom(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """自定义验证逻辑
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 验证必需的配置节
        required_sections = ['core', 'serializer', 'cache', 'storage']
        self._validate_required_fields(config, required_sections, result)
        
        # 验证核心配置
        if 'core' in config:
            self._validate_core_config(config['core'], result)
        
        # 验证序列化配置
        if 'serializer' in config:
            self._validate_serializer_config(config['serializer'], result)
        
        # 验证缓存配置
        if 'cache' in config:
            self._validate_cache_config(config['cache'], result)
        
        # 验证存储配置
        if 'storage' in config:
            self._validate_storage_config(config['storage'], result)
        
        # 验证特化配置
        if 'specialized' in config:
            self._validate_specialized_config(config['specialized'], result)
        
        # 验证监控配置
        if 'monitoring' in config:
            self._validate_monitoring_config(config['monitoring'], result)
        
        # 验证错误处理配置
        if 'error_handling' in config:
            self._validate_error_handling_config(config['error_handling'], result)
    
    def _validate_core_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证核心配置
        
        Args:
            config: 核心配置字典
            result: 验证结果
        """
        # 验证字段类型
        type_rules = {
            'default_ttl': int,
            'max_states': int,
            'cleanup_interval': int
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证字段值
        value_rules = {
            'default_ttl': {'range': (1, 86400 * 7)},  # 1秒到7天
            'max_states': {'range': (1, 1000000)},
            'cleanup_interval': {'range': (1, 3600)}  # 1秒到1小时
        }
        self._validate_field_values(config, value_rules, result)
        
        # 业务逻辑验证
        if config.get('max_states', 0) > 100000:
            result.add_warning("最大状态数设置过高，可能影响性能")
        
        if config.get('default_ttl', 0) > 86400:  # 24小时
            result.add_warning("默认TTL设置过长，可能导致内存占用过高")
    
    def _validate_serializer_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证序列化配置
        
        Args:
            config: 序列化配置字典
            result: 验证结果
        """
        # 验证字段类型
        type_rules = {
            'format': str,
            'compression': bool,
            'compression_threshold': int
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证字段值
        value_rules = {
            'format': {'enum': ['json', 'pickle', 'msgpack']},
            'compression_threshold': {'range': (1, 1024 * 1024)}  # 1字节到1MB
        }
        self._validate_field_values(config, value_rules, result)
        
        # 业务逻辑验证
        if config.get('format') == 'pickle' and config.get('compression', False):
            result.add_warning("Pickle格式与压缩同时使用可能影响性能")
    
    def _validate_cache_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证缓存配置
        
        Args:
            config: 缓存配置字典
            result: 验证结果
        """
        # 验证字段类型
        type_rules = {
            'enabled': bool,
            'max_size': int,
            'ttl': int,
            'eviction_policy': str,
            'enable_serialization': bool,
            'serialization_format': str
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证字段值
        value_rules = {
            'max_size': {'range': (1, 1000000)},
            'ttl': {'range': (1, 86400)},  # 1秒到24小时
            'eviction_policy': {'enum': ['lru', 'lfu', 'fifo']},
            'serialization_format': {'enum': ['json', 'pickle', 'msgpack']}
        }
        self._validate_field_values(config, value_rules, result)
        
        # 业务逻辑验证
        if config.get('enabled', False):
            if config.get('max_size', 0) > 100000:
                result.add_warning("缓存大小设置过高，可能影响性能")
            
            if config.get('ttl', 0) > 3600:  # 1小时
                result.add_warning("缓存TTL设置过长，可能导致数据过期不及时")
    
    def _validate_storage_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证存储配置
        
        Args:
            config: 存储配置字典
            result: 验证结果
        """
        # 验证存储类型
        if 'default_type' in config:
            value_rules = {
                'default_type': {'enum': ['memory', 'sqlite', 'file']}
            }
            self._validate_field_values(config, value_rules, result)
        
        # 验证内存存储配置
        if 'memory' in config:
            self._validate_memory_storage_config(config['memory'], result)
        
        # 验证SQLite存储配置
        if 'sqlite' in config:
            self._validate_sqlite_storage_config(config['sqlite'], result)
        
        # 验证文件存储配置
        if 'file' in config:
            self._validate_file_storage_config(config['file'], result)
    
    def _validate_memory_storage_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证内存存储配置
        
        Args:
            config: 内存存储配置字典
            result: 验证结果
        """
        type_rules = {
            'max_size': int,
            'database_path': str,
            'connection_pool_size': int,
            'compression': bool,
            'compression_threshold': int
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'max_size': {'range': (1, 10000000)},
            'connection_pool_size': {'range': (1, 100)},
            'compression_threshold': {'range': (1, 1024 * 1024)}
        }
        self._validate_field_values(config, value_rules, result)
    
    def _validate_sqlite_storage_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证SQLite存储配置
        
        Args:
            config: SQLite存储配置字典
            result: 验证结果
        """
        type_rules = {
            'database_path': str,
            'connection_pool_size': int,
            'compression': bool,
            'compression_threshold': int
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'connection_pool_size': {'range': (1, 100)},
            'compression_threshold': {'range': (1, 1024 * 1024)}
        }
        self._validate_field_values(config, value_rules, result)
    
    def _validate_file_storage_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证文件存储配置
        
        Args:
            config: 文件存储配置字典
            result: 验证结果
        """
        type_rules = {
            'base_path': str,
            'format': str,
            'compression': bool,
            'compression_threshold': int,
            'create_subdirs': bool
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'format': {'enum': ['json', 'yaml', 'pickle']},
            'compression_threshold': {'range': (1, 1024 * 1024)}
        }
        self._validate_field_values(config, value_rules, result)
        
        # 验证文件路径
        if 'base_path' in config:
            self._validate_file_path(config['base_path'], result)
    
    def _validate_specialized_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证特化配置
        
        Args:
            config: 特化配置字典
            result: 验证结果
        """
        # 验证工作流配置
        if 'workflow' in config:
            self._validate_workflow_config(config['workflow'], result)
        
        # 验证工具配置
        if 'tools' in config:
            self._validate_tools_config(config['tools'], result)
        
        # 验证会话配置
        if 'sessions' in config:
            self._validate_sessions_config(config['sessions'], result)
        
        # 验证线程配置
        if 'threads' in config:
            self._validate_threads_config(config['threads'], result)
        
        # 验证检查点配置
        if 'checkpoints' in config:
            self._validate_checkpoints_config(config['checkpoints'], result)
    
    def _validate_workflow_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证工作流配置
        
        Args:
            config: 工作流配置字典
            result: 验证结果
        """
        type_rules = {
            'max_iterations': int,
            'message_history_limit': int,
            'auto_save': bool
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'max_iterations': {'range': (1, 10000)},
            'message_history_limit': {'range': (1, 100000)}
        }
        self._validate_field_values(config, value_rules, result)
        
        # 业务逻辑验证
        if config.get('max_iterations', 0) > 1000:
            result.add_warning("工作流最大迭代次数设置过高，可能导致无限循环")
        
        if config.get('message_history_limit', 0) > 10000:
            result.add_warning("消息历史限制设置过高，可能占用大量内存")
    
    def _validate_tools_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证工具配置
        
        Args:
            config: 工具配置字典
            result: 验证结果
        """
        type_rules = {
            'context_isolation': bool,
            'auto_expiration': bool,
            'default_ttl': int
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'default_ttl': {'range': (1, 86400)}
        }
        self._validate_field_values(config, value_rules, result)
    
    def _validate_sessions_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证会话配置
        
        Args:
            config: 会话配置字典
            result: 验证结果
        """
        type_rules = {
            'auto_cleanup': bool,
            'max_inactive_duration': int
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'max_inactive_duration': {'range': (1, 86400 * 7)}  # 1秒到7天
        }
        self._validate_field_values(config, value_rules, result)
    
    def _validate_threads_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证线程配置
        
        Args:
            config: 线程配置字典
            result: 验证结果
        """
        type_rules = {
            'auto_cleanup': bool,
            'max_inactive_duration': int
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'max_inactive_duration': {'range': (1, 86400 * 7)}  # 1秒到7天
        }
        self._validate_field_values(config, value_rules, result)
    
    def _validate_checkpoints_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证检查点配置
        
        Args:
            config: 检查点配置字典
            result: 验证结果
        """
        type_rules = {
            'auto_cleanup': bool,
            'max_checkpoints_per_thread': int,
            'cleanup_interval': int
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'max_checkpoints_per_thread': {'range': (1, 1000)},
            'cleanup_interval': {'range': (1, 3600)}  # 1秒到1小时
        }
        self._validate_field_values(config, value_rules, result)
    
    def _validate_monitoring_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证监控配置
        
        Args:
            config: 监控配置字典
            result: 验证结果
        """
        type_rules = {
            'enabled': bool,
            'statistics_interval': int,
            'performance_tracking': bool,
            'memory_tracking': bool
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'statistics_interval': {'range': (1, 3600)}  # 1秒到1小时
        }
        self._validate_field_values(config, value_rules, result)
    
    def _validate_error_handling_config(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证错误处理配置
        
        Args:
            config: 错误处理配置字典
            result: 验证结果
        """
        type_rules = {
            'retry_attempts': int,
            'retry_delay': (int, float),
            'fallback_to_memory': bool,
            'log_errors': bool
        }
        self._validate_field_types(config, type_rules, result)
        
        value_rules = {
            'retry_attempts': {'range': (0, 10)},
            'retry_delay': {'range': (0.1, 60.0)}  # 0.1秒到60秒
        }
        self._validate_field_values(config, value_rules, result)
        
        # 业务逻辑验证
        if config.get('retry_attempts', 0) > 5:
            result.add_warning("重试次数设置过高，可能导致长时间等待")
        
        if config.get('retry_delay', 0) > 30.0:
            result.add_warning("重试延迟设置过长，可能影响响应速度")


def create_state_config_validator(**kwargs) -> StateConfigValidator:
    """创建状态配置验证器实例
    
    Args:
        **kwargs: 其他参数
        
    Returns:
        状态配置验证器实例
    """
    return StateConfigValidator(**kwargs)


__all__ = [
    "StateConfigValidator",
    "create_state_config_validator"
]