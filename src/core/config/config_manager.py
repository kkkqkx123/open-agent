"""
配置管理器 - 统一的配置管理入口
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic, Callable
from functools import lru_cache

from .config_loader import ConfigLoader, CachedConfigLoader
from .config_processor import ConfigProcessor
from .models import BaseConfig, ConfigType, get_config_model, ConfigRegistry
from .exceptions import (
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError
)

T = TypeVar('T', bound=BaseConfig)


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(
        self,
        base_path: Optional[Path] = None,
        use_cache: bool = True,
        auto_reload: bool = False
    ):
        """初始化配置管理器"""
        self.base_path = base_path or Path("configs")
        
        # 初始化加载器
        if use_cache:
            self.loader = CachedConfigLoader(self.base_path)
        else:
            self.loader = ConfigLoader(self.base_path)
        
        # 初始化处理器
        self.processor = ConfigProcessor(self.loader)
        
        # 初始化注册表
        self.registry = ConfigRegistry()
        
        # 自动重载配置
        self.auto_reload = auto_reload
        self._config_cache = {}  # 处理后的配置缓存
        self._model_cache = {}   # 模型实例缓存
    
    @lru_cache(maxsize=256)
    def load_config(self, config_path: str, config_type: Optional[ConfigType] = None) -> Dict[str, Any]:
        """加载并处理配置"""
        try:
            # 加载原始配置
            raw_config = self.loader.load(config_path)
            
            # 处理配置（继承、环境变量、验证）
            processed_config = self.processor.process(raw_config, config_path)
            
            # 缓存处理后的配置
            self._config_cache[config_path] = processed_config
            
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
        final_model_class: Type[T] = model_class or BaseConfig  # type: ignore[assignment]
        if final_model_class is BaseConfig:
            # 根据配置类型自动选择模型
            config_type = config_data.get("type")
            if config_type:
                final_model_class = get_config_model(ConfigType(config_type))  # type: ignore[assignment]
        
        try:
            # 创建模型实例
            model_instance = final_model_class(**config_data)
            
            # 缓存模型实例
            cache_key = f"{config_path}:{final_model_class.__name__}"
            self._model_cache[cache_key] = model_instance
            
            return model_instance
            
        except Exception as e:
            raise ConfigValidationError(f"配置模型转换失败: {e}", config_path)
    
    def load_llm_config(self, config_path: str) -> BaseConfig:
        """加载LLM配置"""
        return self.load_config_model(config_path, model_class=self._get_llm_model_class())
    
    def load_tool_config(self, config_path: str) -> BaseConfig:
        """加载工具配置"""
        return self.load_config_model(config_path, model_class=self._get_tool_model_class())
    
    def load_tool_set_config(self, config_path: str) -> BaseConfig:
        """加载工具集配置"""
        return self.load_config_model(config_path, model_class=self._get_tool_set_model_class())
    
    def load_global_config(self, config_path: str) -> BaseConfig:
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
    
    def get_registered_config(self, name: str) -> Optional[BaseConfig]:
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
        if config_path in self._config_cache:
            del self._config_cache[config_path]
        
        # 清除lru_cache
        self.load_config.cache_clear()
        
        # 重新加载
        return self.load_config(config_path)
    
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存"""
        if config_path:
            # 清除指定配置的缓存
            if config_path in self._config_cache:
                del self._config_cache[config_path]
            
            # 清除模型缓存
            model_keys = [key for key in self._model_cache.keys() if key.startswith(config_path)]
            for key in model_keys:
                del self._model_cache[key]
        else:
            # 清除所有缓存
            self._config_cache.clear()
            self._model_cache.clear()
            self.load_config.cache_clear()
    
    def validate_config(self, config_data: Dict[str, Any], config_type: Optional[ConfigType] = None) -> bool:
        """验证配置数据"""
        try:
            if config_type:
                model_class = get_config_model(config_type)
                model_instance = model_class(**config_data)
                model_instance.validate_config()
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
    
    def _get_llm_model_class(self) -> Type[BaseConfig]:
        """获取LLM模型类"""
        from .models import LLMConfig
        return LLMConfig
    
    def _get_tool_model_class(self) -> Type[BaseConfig]:
        """获取工具模型类"""
        from .models import ToolConfig
        return ToolConfig
    
    def _get_tool_set_model_class(self) -> Type[BaseConfig]:
        """获取工具集模型类"""
        from .models import ToolSetConfig
        return ToolSetConfig
    
    def _get_global_model_class(self) -> Type[BaseConfig]:
        """获取全局模型类"""
        from .models import GlobalConfig
        return GlobalConfig
    
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
        model_class = get_config_model(config_type)
        
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
                "tool_type": "builtin",
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
def load_llm_config(config_path: str) -> BaseConfig:
    """加载LLM配置"""
    return get_default_manager().load_llm_config(config_path)


def load_tool_config(config_path: str) -> BaseConfig:
    """加载工具配置"""
    return get_default_manager().load_tool_config(config_path)


def load_tool_set_config(config_path: str) -> BaseConfig:
    """加载工具集配置"""
    return get_default_manager().load_tool_set_config(config_path)


def load_global_config(config_path: str) -> BaseConfig:
    """加载全局配置"""
    return get_default_manager().load_global_config(config_path)