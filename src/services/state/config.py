"""状态管理服务配置模块

提供状态管理服务的配置获取、验证和服务配置功能。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional

logger = get_logger(__name__)


def get_state_service_config() -> Dict[str, Any]:
    """获取状态管理服务的默认配置
    
    Returns:
        状态管理服务的默认配置字典
    """
    return {
        "core": {
            "default_ttl": 3600,
            "max_states": 10000,
            "cleanup_interval": 300
        },
        "serializer": {
            "format": "json",
            "compression": True,
            "compression_threshold": 1024
        },
        "cache": {
            "enabled": True,
            "max_size": 1000,
            "ttl": 300,
            "eviction_policy": "lru",
            "enable_serialization": False,
            "serialization_format": "json"
        },
        "storage": {
            "default_type": "memory",
            "memory": {
                "max_size": 10000
            },
            "sqlite": {
                "database_path": "data/states.db",
                "connection_pool_size": 10,
                "compression": True,
                "compression_threshold": 1024
            },
            "file": {
                "base_path": "data/states",
                "format": "json",
                "compression": False,
                "create_subdirs": True
            }
        },
        "validation": {
            "enabled": True,
            "strict_mode": False,
            "custom_validators": []
        },
        "lifecycle": {
            "auto_cleanup": True,
            "cleanup_interval": 300,
            "event_handlers": []
        },
        "specialized": {
            "workflow": {
                "max_iterations": 100,
                "message_history_limit": 1000,
                "auto_save": True
            },
            "tools": {
                "context_isolation": True,
                "auto_expiration": True,
                "default_ttl": 1800
            },
            "sessions": {
                "auto_cleanup": True,
                "max_inactive_duration": 3600
            },
            "threads": {
                "auto_cleanup": True,
                "max_inactive_duration": 7200
            },
            "checkpoints": {
                "auto_cleanup": True,
                "max_checkpoints_per_thread": 50,
                "cleanup_interval": 600
            }
        },
        "monitoring": {
            "enabled": True,
            "statistics_interval": 60,
            "performance_tracking": True,
            "memory_tracking": True
        },
        "error_handling": {
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "fallback_to_memory": True,
            "log_errors": True
        },
        "development": {
            "debug_mode": False,
            "verbose_logging": False,
            "enable_profiling": False,
            "mock_storage": False
        }
    }


def validate_state_configuration(config: Dict[str, Any]) -> List[str]:
    """验证状态管理配置
    
    Args:
        config: 配置字典
        
    Returns:
        验证错误列表，空列表表示验证通过
    """
    errors = []
    
    if not isinstance(config, dict):
        errors.append("配置必须是字典类型")
        return errors
    
    # 验证核心配置
    if "core" in config:
        core_config = config["core"]
        if not isinstance(core_config, dict):
            errors.append("core配置必须是字典类型")
        else:
            if "default_ttl" in core_config and not isinstance(core_config["default_ttl"], int):
                errors.append("core.default_ttl必须是整数类型")
            if "max_states" in core_config and not isinstance(core_config["max_states"], int):
                errors.append("core.max_states必须是整数类型")
            if "cleanup_interval" in core_config and not isinstance(core_config["cleanup_interval"], int):
                errors.append("core.cleanup_interval必须是整数类型")
    
    # 验证序列化配置
    if "serializer" in config:
        serializer_config = config["serializer"]
        if not isinstance(serializer_config, dict):
            errors.append("serializer配置必须是字典类型")
        else:
            if "format" in serializer_config:
                valid_formats = ["json", "pickle", "msgpack"]
                if serializer_config["format"] not in valid_formats:
                    errors.append(f"serializer.format必须是以下之一: {valid_formats}")
            if "compression" in serializer_config and not isinstance(serializer_config["compression"], bool):
                errors.append("serializer.compression必须是布尔类型")
            if "compression_threshold" in serializer_config and not isinstance(serializer_config["compression_threshold"], int):
                errors.append("serializer.compression_threshold必须是整数类型")
    
    # 验证缓存配置
    if "cache" in config:
        cache_config = config["cache"]
        if not isinstance(cache_config, dict):
            errors.append("cache配置必须是字典类型")
        else:
            if "enabled" in cache_config and not isinstance(cache_config["enabled"], bool):
                errors.append("cache.enabled必须是布尔类型")
            if "max_size" in cache_config and not isinstance(cache_config["max_size"], int):
                errors.append("cache.max_size必须是整数类型")
            if "ttl" in cache_config and not isinstance(cache_config["ttl"], int):
                errors.append("cache.ttl必须是整数类型")
            if "eviction_policy" in cache_config:
                valid_policies = ["lru", "lfu", "fifo"]
                if cache_config["eviction_policy"] not in valid_policies:
                    errors.append(f"cache.eviction_policy必须是以下之一: {valid_policies}")
    
    # 验证存储配置
    if "storage" in config:
        storage_config = config["storage"]
        if not isinstance(storage_config, dict):
            errors.append("storage配置必须是字典类型")
        else:
            if "default_type" in storage_config:
                valid_types = ["memory", "sqlite", "file"]
                if storage_config["default_type"] not in valid_types:
                    errors.append(f"storage.default_type必须是以下之一: {valid_types}")
    
    # 验证验证配置
    if "validation" in config:
        validation_config = config["validation"]
        if not isinstance(validation_config, dict):
            errors.append("validation配置必须是字典类型")
        else:
            if "enabled" in validation_config and not isinstance(validation_config["enabled"], bool):
                errors.append("validation.enabled必须是布尔类型")
            if "strict_mode" in validation_config and not isinstance(validation_config["strict_mode"], bool):
                errors.append("validation.strict_mode必须是布尔类型")
            if "custom_validators" in validation_config and not isinstance(validation_config["custom_validators"], list):
                errors.append("validation.custom_validators必须是列表类型")
    
    # 验证生命周期配置
    if "lifecycle" in config:
        lifecycle_config = config["lifecycle"]
        if not isinstance(lifecycle_config, dict):
            errors.append("lifecycle配置必须是字典类型")
        else:
            if "auto_cleanup" in lifecycle_config and not isinstance(lifecycle_config["auto_cleanup"], bool):
                errors.append("lifecycle.auto_cleanup必须是布尔类型")
            if "cleanup_interval" in lifecycle_config and not isinstance(lifecycle_config["cleanup_interval"], int):
                errors.append("lifecycle.cleanup_interval必须是整数类型")
            if "event_handlers" in lifecycle_config and not isinstance(lifecycle_config["event_handlers"], list):
                errors.append("lifecycle.event_handlers必须是列表类型")
    
    # 验证监控配置
    if "monitoring" in config:
        monitoring_config = config["monitoring"]
        if not isinstance(monitoring_config, dict):
            errors.append("monitoring配置必须是字典类型")
        else:
            if "enabled" in monitoring_config and not isinstance(monitoring_config["enabled"], bool):
                errors.append("monitoring.enabled必须是布尔类型")
            if "statistics_interval" in monitoring_config and not isinstance(monitoring_config["statistics_interval"], int):
                errors.append("monitoring.statistics_interval必须是整数类型")
            if "performance_tracking" in monitoring_config and not isinstance(monitoring_config["performance_tracking"], bool):
                errors.append("monitoring.performance_tracking必须是布尔类型")
            if "memory_tracking" in monitoring_config and not isinstance(monitoring_config["memory_tracking"], bool):
                errors.append("monitoring.memory_tracking必须是布尔类型")
    
    # 验证错误处理配置
    if "error_handling" in config:
        error_handling_config = config["error_handling"]
        if not isinstance(error_handling_config, dict):
            errors.append("error_handling配置必须是字典类型")
        else:
            if "retry_attempts" in error_handling_config and not isinstance(error_handling_config["retry_attempts"], int):
                errors.append("error_handling.retry_attempts必须是整数类型")
            if "retry_delay" in error_handling_config and not isinstance(error_handling_config["retry_delay"], (int, float)):
                errors.append("error_handling.retry_delay必须是数字类型")
            if "fallback_to_memory" in error_handling_config and not isinstance(error_handling_config["fallback_to_memory"], bool):
                errors.append("error_handling.fallback_to_memory必须是布尔类型")
            if "log_errors" in error_handling_config and not isinstance(error_handling_config["log_errors"], bool):
                errors.append("error_handling.log_errors必须是布尔类型")
    
    # 验证开发配置
    if "development" in config:
        development_config = config["development"]
        if not isinstance(development_config, dict):
            errors.append("development配置必须是字典类型")
        else:
            if "debug_mode" in development_config and not isinstance(development_config["debug_mode"], bool):
                errors.append("development.debug_mode必须是布尔类型")
            if "verbose_logging" in development_config and not isinstance(development_config["verbose_logging"], bool):
                errors.append("development.verbose_logging必须是布尔类型")
            if "enable_profiling" in development_config and not isinstance(development_config["enable_profiling"], bool):
                errors.append("development.enable_profiling必须是布尔类型")
            if "mock_storage" in development_config and not isinstance(development_config["mock_storage"], bool):
                errors.append("development.mock_storage必须是布尔类型")
    
    return errors


def configure_state_services(container: Any, config: Dict[str, Any]) -> None:
    """配置状态管理服务
    
    Args:
        container: 服务容器
        config: 配置字典
    """
    try:
        # 这里应该实现具体的服务配置逻辑
        # 由于这是一个简化的实现，我们只记录日志
        logger.info("开始配置状态管理服务")
        
        # 配置核心服务
        if "core" in config:
            logger.debug(f"配置核心服务: {config['core']}")
        
        # 配置存储服务
        if "storage" in config:
            logger.debug(f"配置存储服务: {config['storage']}")
        
        # 配置缓存服务
        if "cache" in config:
            logger.debug(f"配置缓存服务: {config['cache']}")
        
        # 配置监控服务
        if "monitoring" in config:
            logger.debug(f"配置监控服务: {config['monitoring']}")
        
        logger.info("状态管理服务配置完成")
        
    except Exception as e:
        logger.error(f"配置状态管理服务失败: {e}")
        raise