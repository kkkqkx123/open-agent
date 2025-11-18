"""
配置管理器 - 统一的配置管理入口
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic, Callable

from ..common.cache import ConfigCache, get_global_cache_manager, clear_cache
from .config_loader import ConfigLoader
from .config_processor import ConfigProcessor
from .base import (
    BaseConfig, 
    ConfigType, 
    ValidationRule,
    ConfigInheritance,
    ConfigMetadata
)
from .models import ToolSetConfig
from .exceptions import (
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError
)
from .file_watcher import ConfigFileWatcher
from .error_recovery import ConfigErrorRecovery, ConfigValidatorWithRecovery
from .callback_manager import (
    get_global_callback_manager,
    trigger_config_callbacks,
    ConfigCallbackManager,
    ConfigChangeContext
)

T = TypeVar('T', bound=BaseConfig)


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(
        self,
        base_path: Optional[Path] = None,
        use_cache: bool = True,
        auto_reload: bool = False,
        enable_error_recovery: bool = True,
        enable_callback_manager: bool = True
    ):
        """初始化配置管理器"""
        self.base_path = base_path or Path("configs")
        
        # 初始化加载器
        self.loader = ConfigLoader(self.base_path)
        
        # 初始化处理器
        self.processor = ConfigProcessor(self.loader)
        
        # 初始化注册表
        self.registry = ConfigRegistry()
        
        # 自动重载配置
        self.auto_reload = auto_reload
        
        # 使用统一缓存系统
        self._config_cache = ConfigCache()
        self._model_cache = ConfigCache()
        
        # 文件监听器
        self._file_watcher: Optional[ConfigFileWatcher] = None
        
        # 错误恢复
        self._error_recovery: Optional[ConfigErrorRecovery] = None
        if enable_error_recovery:
            self._error_recovery = ConfigErrorRecovery()
            self._validator_with_recovery = ConfigValidatorWithRecovery(
                self._error_recovery
            )
        
        # 回调管理器
        self._callback_manager: Optional[ConfigCallbackManager] = None
        if enable_callback_manager:
            self._callback_manager = get_global_callback_manager()
    
    def load_config(self, config_path: str, config_type: Optional[ConfigType] = None) -> Dict[str, Any]:
        """加载并处理配置"""
        try:
            # 检查缓存
            cache_key = config_path
            cached_config = self._config_cache.get(cache_key)
            if cached_config is not None:
                return cached_config
            
            # 加载原始配置（带错误恢复）
            try:
                raw_config = self.loader.load(config_path)
            except Exception as e:
                if self._error_recovery:
                    # 尝试错误恢复
                    full_path = self.base_path / config_path
                    if self._error_recovery.recover_config(str(full_path), e):
                        # 恢复成功，再次尝试加载
                        try:
                            raw_config = self.loader.load(config_path)
                        except Exception as recovery_error:
                            raise ConfigError(
                                f"配置恢复后仍然无法加载: {recovery_error}"
                            )
                    else:
                        raise ConfigError(f"无法恢复配置文件: {e}")
                else:
                    raise ConfigError(f"加载配置文件失败: {e}")
            
            # 处理配置（继承、环境变量、验证）
            processed_config = self.processor.process(raw_config, config_path)
            
            # 缓存处理后的配置
            self._config_cache.put(cache_key, processed_config)
            
            return processed_config
            
        except ConfigNotFoundError:
            raise
        except Exception as e:
            raise ConfigError(f"加载配置失败: {e}", config_path)
    
    def load_config_model(self, config_path: str, model_class: Optional[Type[T]] = None) -> T:
        """加载配置并转换为模型实例"""
        # 获取配置数据
        config_data = self.load_config(config_path)
        
        # 确定模型类
        if model_class is None:
            # 根据配置类型自动选择模型
            config_type = config_data.get("type")
            if config_type:
                try:
                    final_model_class = get_config_model(ConfigType(config_type))
                except (ValueError, KeyError):
                    final_model_class = BaseConfig  # type: ignore[assignment]
            else:
                final_model_class = BaseConfig  # type: ignore[assignment]
        else:
            final_model_class = model_class  # type: ignore[assignment]
        
        try:
            # 检查模型缓存
            cache_key = f"{config_path}:{final_model_class.__name__}"
            cached_model = self._model_cache.get(cache_key)
            if cached_model is not None:
                return cached_model  # type: ignore[return-value]
            
            # 创建模型实例
            model_instance = final_model_class(**config_data)
            
            # 缓存模型实例
            self._model_cache.put(cache_key, model_instance)
            
            return model_instance  # type: ignore[return-value]
            
        except Exception as e:
            raise ConfigValidationError(f"配置模型转换失败: {e}", config_path)
    
    def load_llm_config(self, config_path: str) -> Any:
        """加载LLM配置"""
        return self.load_config_model(config_path, model_class=self._get_llm_model_class())
    
    def load_tool_config(self, config_path: str) -> Any:
        """加载工具配置"""
        return self.load_config_model(config_path, model_class=self._get_tool_model_class())
    
    def load_tool_set_config(self, config_path: str) -> Any:
        """加载工具集配置"""
        return self.load_config_model(config_path, model_class=self._get_tool_set_model_class())
    
    def load_global_config(self, config_path: str) -> Any:
        """加载全局配置"""
        return self.load_config_model(config_path, model_class=self._get_global_model_class())
    
    def register_config(self, name: str, config_path: str, config_type: ConfigType) -> None:
        """注册配置到管理器"""
        try:
            config_data = self.load_config(config_path)
            model_class = get_config_model(config_type)
            config_model = model_class(**config_data)
            
            self.registry.register(name, config_model, config_type)
            
        except Exception as e:
            raise ConfigError(f"注册配置失败: {e}", config_path)
    
    def get_registered_config(self, name: str) -> Any:
        """获取已注册的配置"""
        return self.registry.get(name)
    
    def get_registered_configs_by_type(self, config_type: ConfigType) -> List[str]:
        """按类型获取已注册的配置"""
        return self.registry.list_configs_by_type(config_type)
    
    def list_config_files(self, directory: Optional[str] = None, recursive: bool = True) -> List[str]:
        """列出配置文件"""
        return self.loader.get_config_files(directory, recursive)
    
    def reload_config(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置"""
        # 清除缓存
        self._config_cache.clear()
        self._model_cache.clear()
        
        # 清除加载器缓存
        self.loader.invalidate_cache(config_path)
        
        # 重新加载
        return self.load_config(config_path)
    
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存"""
        if config_path:
            # 清除指定配置的缓存
            # 简化实现：清除所有缓存
            self._config_cache.clear()
            self._model_cache.clear()
            
            # 清除加载器缓存
            self.loader.invalidate_cache(config_path)
        else:
            # 清除所有缓存
            self._config_cache.clear()
            self._model_cache.clear()
            self.loader.clear_cache()
    
    def validate_config(self, config_data: Dict[str, Any], config_type: Optional[ConfigType] = None) -> bool:
        """验证配置数据"""
        try:
            if config_type:
                errors = validate_config_with_model(config_data, config_type)
                if errors:
                    raise ConfigValidationError(f"配置验证失败: {'; '.join(errors)}")
            else:
                # 基础验证
                if not isinstance(config_data, dict):
                    raise ConfigValidationError("配置必须是字典类型")
                if not config_data:
                    raise ConfigValidationError("配置不能为空")
                if "name" not in config_data:
                    raise ConfigValidationError("配置必须包含 'name' 字段")
            
            return True
            
        except Exception as e:
            raise ConfigValidationError(f"配置验证失败: {e}")
    
    def merge_configs(self, *config_paths: str) -> Dict[str, Any]:
        """合并多个配置"""
        configs = []
        for path in config_paths:
            config = self.load_config(path)
            configs.append(config)
        
        # 使用处理器的合并逻辑
        return self.processor._merge_configs(*configs)
    
    def process_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理配置数据（不加载文件）"""
        return self.processor.process(config_data)
    
    def resolve_env_vars(self, obj: Any) -> Any:
        """解析环境变量"""
        return self.processor._resolve_env_vars(obj)
    
    def watch_for_changes(
        self, 
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> None:
        """监听配置文件变化
        
        Args:
            callback: 配置变化回调函数，接收文件路径和配置数据
        """
        if self._file_watcher is None:
            self._file_watcher = ConfigFileWatcher(self)
            
        if callback:
            # 为所有YAML文件添加回调
            self._file_watcher.add_callback("*.yaml", callback)
            self._file_watcher.add_callback("*.yml", callback)
            
        # 开始监听
        if not self._file_watcher.is_watching():
            self._file_watcher.start()
    
    def stop_watching(self) -> None:
        """停止监听配置文件变化"""
        if self._file_watcher is not None:
            self._file_watcher.stop()
            self._file_watcher = None
    
    def is_watching(self) -> bool:
        """检查是否正在监听配置文件变化"""
        return self._file_watcher is not None and self._file_watcher.is_watching()
    
    def register_callback(
        self,
        callback_id: str,
        callback: Callable[[ConfigChangeContext], None],
        priority: Any = None,  # 使用Any避免导入问题
        once: bool = False,
        filter_paths: Optional[List[str]] = None,
    ) -> None:
        """注册配置变更回调
        
        Args:
            callback_id: 回调ID
            callback: 回调函数
            priority: 优先级
            once: 是否只执行一次
            filter_paths: 路径过滤器
        """
        if self._callback_manager:
            # 导入优先级枚举
            from .callback_manager import CallbackPriority
            if priority is None:
                priority = CallbackPriority.NORMAL
            self._callback_manager.register_callback(
                callback_id, callback, priority, once, filter_paths
            )
    
    def unregister_callback(self, callback_id: str) -> bool:
        """注销配置变更回调
        
        Args:
            callback_id: 回调ID
            
        Returns:
            是否成功注销
        """
        if self._callback_manager:
            return self._callback_manager.unregister_callback(callback_id)
        return False
    
    def trigger_callbacks(
        self,
        config_path: str,
        old_config: Optional[Dict[str, Any]],
        new_config: Dict[str, Any],
        source: str = "file_watcher",
    ) -> None:
        """触发配置变更回调
        
        Args:
            config_path: 配置文件路径
            old_config: 旧配置
            new_config: 新配置
            source: 变更来源
        """
        if self._callback_manager:
            self._callback_manager.trigger_callbacks(
                config_path, old_config, new_config, source
            )
    
    def _get_llm_model_class(self) -> Type[BaseConfig]:
        """获取LLM模型类"""
        from .models import LLMConfig
        return LLMConfig  # type: ignore[return-value]
    
    def _get_tool_model_class(self) -> Type[BaseConfig]:
        """获取工具模型类"""
        from .models import ToolConfig
        return ToolConfig  # type: ignore[return-value]
    
    def _get_tool_set_model_class(self) -> Type[BaseConfig]:
        """获取工具集模型类"""
        from .models import ToolSetConfig
        return ToolSetConfig  # type: ignore[return-value]
    
    def _get_global_model_class(self) -> Type[BaseConfig]:
        """获取全局模型类"""
        from .models import GlobalConfig
        return GlobalConfig  # type: ignore[return-value]
    
    def get_config_info(self, config_path: str) -> Dict[str, Any]:
        """获取配置信息"""
        try:
            config_data = self.load_config(config_path)
            
            info = {
                "path": config_path,
                "name": config_data.get("name", "unknown"),
                "type": config_data.get("type", "unknown"),
                "exists": True,
                "size": len(str(config_data)),
                "keys": list(config_data.keys())
            }
            
            # 检查继承
            if "inherits_from" in config_data:
                info["inherits_from"] = config_data["inherits_from"]
            
            return info
            
        except ConfigNotFoundError:
            return {
                "path": config_path,
                "exists": False,
                "error": "配置未找到"
            }
        except Exception as e:
            return {
                "path": config_path,
                "exists": True,
                "error": str(e)
            }
    
    def export_config(self, config_path: str, output_path: str, format: str = "yaml") -> None:
        """导出配置"""
        config_data = self.load_config(config_path)
        
        output_file = Path(output_path)
        
        if format.lower() == "yaml":
            import yaml
            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        elif format.lower() == "json":
            import json
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        else:
            raise ConfigError(f"不支持的导出格式: {format}")
    
    def create_config_template(self, config_type: ConfigType, output_path: str) -> None:
        """创建配置模板"""
        # 创建示例配置
        if config_type == ConfigType.LLM:
            template = {
                "name": "example_llm",
                "type": "llm",
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "${OPENAI_API_KEY}",
                "temperature": 0.7,
                "max_tokens": 2048
            }
        elif config_type == ConfigType.TOOL:
            template = {
                "name": "example_tool",
                "type": "tool",
                "tool_type": "rest",
                "description": "示例工具",
                "enabled": True,
                "parameters": {}
            }
        elif config_type == ConfigType.TOOL_SET:
            template = {
                "name": "example_tool_set",
                "type": "tool_set",
                "description": "示例工具集",
                "tools": ["tool1", "tool2"],
                "category": "general"
            }
        elif config_type == ConfigType.GLOBAL:
            template = {
                "name": "global",
                "type": "global",
                "app_name": "Modular Agent Framework",
                "log_level": "INFO",
                "environment": "development"
            }
        else:
            template = {
                "name": "example_config",
                "type": config_type.value
            }
        
        # 导出模板
        output_file = Path(output_path)
        import yaml
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(template, f, default_flow_style=False, allow_unicode=True)


# 配置注册表
class ConfigRegistry:
    """配置注册表"""
    
    def __init__(self) -> None:
        """初始化配置注册表"""
        self._configs: Dict[str, BaseConfig] = {}
        self._config_types: Dict[str, ConfigType] = {}
    
    def register(self, name: str, config: BaseConfig, config_type: ConfigType) -> None:
        """注册配置
        
        Args:
            name: 配置名称
            config: 配置实例
            config_type: 配置类型
        """
        self._configs[name] = config
        self._config_types[name] = config_type
    
    def get(self, name: str) -> Optional[BaseConfig]:
        """获取已注册的配置
        
        Args:
            name: 配置名称
            
        Returns:
            配置实例或None
        """
        return self._configs.get(name)
    
    def list_configs_by_type(self, config_type: ConfigType) -> List[str]:
        """按类型获取已注册的配置列表
        
        Args:
            config_type: 配置类型
            
        Returns:
            配置名称列表
        """
        return [name for name, ctype in self._config_types.items() if ctype == config_type]
    
    def unregister(self, name: str) -> bool:
        """注销配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否成功注销
        """
        if name in self._configs:
            del self._configs[name]
            del self._config_types[name]
            return True
        return False
    
    def list_all_configs(self) -> List[str]:
        """列出所有已注册的配置
        
        Returns:
            配置名称列表
        """
        return list(self._configs.keys())


# 工具函数
def get_config_model(config_type: ConfigType) -> type[BaseConfig]:
    """获取配置类型对应的模型类
    
    Args:
        config_type: 配置类型
        
    Returns:
        配置模型类
        
    Raises:
        ValueError: 如果配置类型不支持
    """
    # 这里可以根据需要返回具体的配置模型类
    # 目前返回 BaseConfig 作为默认
    return BaseConfig


def validate_config_with_model(config_dict: Dict[str, Any], config_type: ConfigType) -> List[str]:
    """使用配置模型验证配置
    
    Args:
        config_dict: 配置字典
        config_type: 配置类型
        
    Returns:
        验证错误列表
    """
    # 简化的验证逻辑
    try:
        if not isinstance(config_dict, dict):
            return ["配置必须是字典类型"]
        if not config_dict:
            return ["配置不能为空"]
        return []
    except Exception as e:
        return [str(e)]


# 全局配置管理器实例
_default_manager: Optional[ConfigManager] = None


def get_default_manager() -> ConfigManager:
    """获取默认配置管理器"""
    global _default_manager
    if _default_manager is None:
        _default_manager = ConfigManager()
    return _default_manager


def load_config(config_path: str) -> Dict[str, Any]:
    """便捷函数：加载配置"""
    return get_default_manager().load_config(config_path)


def load_config_model(config_path: str, model_class: Optional[Type[T]] = None) -> T:
    """便捷函数：加载配置模型"""
    return get_default_manager().load_config_model(config_path, model_class)


# 便捷函数：特定类型配置加载
def load_llm_config(config_path: str) -> Any:
    """加载LLM配置"""
    return get_default_manager().load_llm_config(config_path)


def load_tool_config(config_path: str) -> Any:
    """加载工具配置"""
    return get_default_manager().load_tool_config(config_path)


def load_tool_set_config(config_path: str) -> Any:
    """加载工具集配置"""
    return get_default_manager().load_tool_set_config(config_path)


def load_global_config(config_path: str) -> Any:
    """加载全局配置"""
    return get_default_manager().load_global_config(config_path)