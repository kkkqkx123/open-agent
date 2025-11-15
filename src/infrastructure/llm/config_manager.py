"""LLM配置管理器 - 统一配置加载、验证和热重载"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List, Union, Callable, Type
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock, Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import LLMClientConfig, LLMModuleConfig
from .exceptions import LLMConfigurationError
from ..config.interfaces import IConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class ConfigValidationRule:
    """配置验证规则"""
    field_path: str  # 字段路径，如 "model_type", "timeout"
    required: bool = True
    field_type: Optional[Type] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable[[Any], bool]] = None
    error_message: Optional[str] = None


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self) -> None:
        """初始化配置验证器"""
        self.rules: List[ConfigValidationRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """设置默认验证规则"""
        # LLMClientConfig 验证规则
        self.rules.extend([
            ConfigValidationRule(
                field_path="model_type",
                required=True,
                field_type=str,
                allowed_values=["openai", "gemini", "anthropic", "claude", "mock"],
                error_message="model_type必须是支持的类型: openai, gemini, anthropic, claude, mock"
            ),
            ConfigValidationRule(
                field_path="model_name",
                required=True,
                field_type=str,
                error_message="model_name是必需的字符串字段"
            ),
            ConfigValidationRule(
                field_path="timeout",
                required=False,
                field_type=int,
                min_value=1,
                max_value=300,
                error_message="timeout必须是1-300之间的整数"
            ),
            ConfigValidationRule(
                field_path="max_retries",
                required=False,
                field_type=int,
                min_value=0,
                max_value=10,
                error_message="max_retries必须是0-10之间的整数"
            ),
            ConfigValidationRule(
                field_path="temperature",
                required=False,
                field_type=float,
                min_value=0.0,
                max_value=2.0,
                error_message="temperature必须是0.0-2.0之间的浮点数"
            ),
            ConfigValidationRule(
                field_path="max_tokens",
                required=False,
                field_type=int,
                min_value=1,
                max_value=100000,
                error_message="max_tokens必须是1-100000之间的整数"
            ),
        ])
    
    def add_rule(self, rule: ConfigValidationRule) -> None:
        """添加验证规则"""
        self.rules.append(rule)
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        errors = []
        
        for rule in self.rules:
            try:
                value = self._get_nested_value(config, rule.field_path)
                
                # 检查必需字段
                if rule.required and value is None:
                    errors.append(f"必需字段 '{rule.field_path}' 缺失")
                    continue
                
                # 如果值为None且不是必需的，跳过其他验证
                if value is None:
                    continue
                
                # 类型验证
                if rule.field_type and not isinstance(value, rule.field_type):
                    errors.append(
                        f"字段 '{rule.field_path}' 类型错误: "
                        f"期望 {rule.field_type.__name__}, 实际 {type(value).__name__}"
                    )
                    continue
                
                # 数值范围验证
                if isinstance(value, (int, float)):
                    if rule.min_value is not None and value < rule.min_value:
                        errors.append(
                            f"字段 '{rule.field_path}' 值过小: "
                            f"最小值 {rule.min_value}, 实际值 {value}"
                        )
                    if rule.max_value is not None and value > rule.max_value:
                        errors.append(
                            f"字段 '{rule.field_path}' 值过大: "
                            f"最大值 {rule.max_value}, 实际值 {value}"
                        )
                
                # 允许值验证
                if rule.allowed_values and value not in rule.allowed_values:
                    errors.append(
                        f"字段 '{rule.field_path}' 值无效: "
                        f"允许值 {rule.allowed_values}, 实际值 {value}"
                    )
                
                # 自定义验证
                if rule.custom_validator and not rule.custom_validator(value):
                    errors.append(
                        rule.error_message or 
                        f"字段 '{rule.field_path}' 自定义验证失败"
                    )
                    
            except Exception as e:
                errors.append(f"验证字段 '{rule.field_path}' 时出错: {str(e)}")
        
        return errors
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典中的值"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, config_manager: 'LLMConfigManager') -> None:
        """初始化文件处理器"""
        self.config_manager = config_manager
        self.last_modified = {}
    
    def on_modified(self, event) -> None:
        """文件修改事件处理"""
        if event.is_directory:
            return
        
        file_path = Path(str(event.src_path))
        
        # 检查是否是配置文件
        if not self._is_config_file(file_path):
            return
        
        # 防抖处理
        current_time = datetime.now().timestamp()
        last_time = self.last_modified.get(str(file_path), 0)
        
        if current_time - last_time < 1.0:  # 1秒内的重复变更忽略
            return
        
        self.last_modified[str(file_path)] = current_time
        
        try:
            logger.info(f"检测到配置文件变更: {file_path}")
            self.config_manager._reload_config_file(file_path)
        except Exception as e:
            logger.error(f"重新加载配置文件失败 {file_path}: {e}")
    
    def _is_config_file(self, file_path: Path) -> bool:
        """检查是否是配置文件"""
        return file_path.suffix.lower() in ['.yaml', '.yml', '.json']


class LLMConfigManager:
    """LLM配置管理器"""
    
    def __init__(
        self,
        config_loader: IConfigLoader,
        config_subdir: str = "llms",
        enable_hot_reload: bool = True,
        validation_enabled: bool = True,
    ) -> None:
        """
        初始化配置管理器
        
        Args:
            config_loader: 核心配置加载器实例
            config_subdir: 相对于configs的子目录
            enable_hot_reload: 是否启用热重载
            validation_enabled: 是否启用配置验证
        """
        self.config_loader = config_loader
        self.config_subdir = config_subdir
        self.config_dir = Path("configs") / self.config_subdir
        self.enable_hot_reload = enable_hot_reload
        self.validation_enabled = validation_enabled
        
        # 配置缓存
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._client_configs: Dict[str, LLMClientConfig] = {}
        self._module_config: Optional[LLMModuleConfig] = None
        
        # 验证器
        self.validator = ConfigValidator()
        
        # 热重载相关
        self._observer: Optional[Any] = None
        self._lock = Lock()
        
        # 回调函数
        self._reload_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # 初始化
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化配置管理器"""
        # 加载所有配置
        self._load_all_configs()
        
        # 启动热重载
        if self.enable_hot_reload:
            self._start_hot_reload()
    
    def _load_all_configs(self) -> None:
        """加载所有配置文件"""
        try:
            # 加载模块配置
            self._load_module_config()
            
            # 加载客户端配置
            self._load_client_configs()
            
            logger.info(f"配置加载完成，共加载 {len(self._client_configs)} 个客户端配置")
            
        except Exception as e:
            raise LLMConfigurationError(f"配置加载失败: {e}")
    
    def _load_module_config(self) -> None:
        """加载模块配置"""
        module_config_path = f"{self.config_subdir}/_group.yaml"
        
        try:
            config_data = self._load_config_file(module_config_path)
            if config_data:
                self._module_config = LLMModuleConfig.from_dict(config_data)
        except Exception as e:
            # 使用默认配置
            self._module_config = LLMModuleConfig()
            logger.warning(f"模块配置文件加载失败或不存在，使用默认配置: {e}")
    
    def _load_client_configs(self) -> None:
        """加载客户端配置"""
        self._client_configs.clear()
        
        # 注意：这里我们无法直接通过 IConfigLoader 列出文件
        # 这是一个设计权衡，为了保持 IConfigLoader 接口的简洁性
        # 我们假设已知的配置文件列表，或者在未来扩展 IConfigLoader 接口
        # 作为临时方案，我们仍然需要扫描目录，但只用于获取文件名
        config_dir = Path("configs") / self.config_subdir
        if not config_dir.exists():
            logger.warning(f"LLM配置目录不存在: {config_dir}")
            return

        for config_file in config_dir.glob("*.yaml"):
            if config_file.name.startswith("_"):
                continue  # 跳过组配置文件
            
            try:
                config_path = f"{self.config_subdir}/{config_file.name}"
                config_data = self._load_config_file(config_path)
                if config_data:
                    client_config = LLMClientConfig.from_dict(config_data)
                    model_key = f"{client_config.model_type}:{client_config.model_name}"
                    self._client_configs[model_key] = client_config
                    
                    # 缓存原始配置数据
                    self._config_cache[config_path] = config_data
                    
            except Exception as e:
                logger.error(f"加载客户端配置失败 {config_file.name}: {e}")
    
    def _load_config_file(self, config_path: str) -> Optional[Dict[str, Any]]:
        """加载单个配置文件"""
        try:
            # 委托给核心加载器，它负责读取、解析、环境变量、继承等所有事
            config_data = self.config_loader.load(config_path)
            
            # 配置验证逻辑保留，因为这是 LLMConfigManager 的特定职责
            if self.validation_enabled:
                errors = self.validator.validate_config(config_data)
                if errors:
                    error_msg = f"配置验证失败 {config_path}:\n" + "\n".join(f"  - {error}" for error in errors)
                    raise LLMConfigurationError(error_msg)
            
            return config_data
            
        except Exception as e:
            logger.error(f"读取配置文件失败 {config_path}: {e}")
            return None

    def _reload_config_file(self, file_path: Path) -> None:
        """重新加载配置文件（用于向后兼容）"""
        config_path = f"{self.config_subdir}/{file_path.name}"
        config_data = self._load_config_file(config_path)
        if config_data:
            self._on_config_file_changed(config_path, config_data)

    # _substitute_env_vars 和 _replace_env_vars 方法已被移除，
    # 因为这些功能现在由 IConfigLoader 提供
    
    def _start_hot_reload(self) -> None:
        """启动热重载"""
        if not self.enable_hot_reload:
            return
            
        try:
            # 将自己的回调函数注册到核心加载器
            # 核心加载器会处理文件监控，并在文件变化时调用我们的回调
            self.config_loader.watch_for_changes(callback=self._on_config_file_changed)
            logger.info("配置热重载已启动 (通过 IConfigLoader)")
        except Exception as e:
            logger.error(f"启动热重载失败: {e}")
            self.enable_hot_reload = False
    
    def _stop_hot_reload(self) -> None:
        """停止热重载"""
        try:
            # 委托给核心加载器停止监控
            self.config_loader.stop_watching()
            logger.info("配置热重载已停止 (通过 IConfigLoader)")
        except Exception as e:
            logger.error(f"停止热重载失败: {e}")
    
    def _on_config_file_changed(self, config_path: str, config_data: Dict[str, Any]) -> None:
        """新的回调函数，由 IConfigLoader 调用"""
        # 检查是否是 LLM 配置文件
        if not config_path.startswith(self.config_subdir + "/"):
            return
            
        file_name = Path(config_path).name
        logger.info(f"检测到LLM配置文件变更: {file_name}")
        
        with self._lock:
            try:
                # 更新缓存
                self._config_cache[config_path] = config_data
                
                # 如果是模块配置文件
                if file_name == "_group.yaml":
                    self._module_config = LLMModuleConfig.from_dict(config_data)
                else:
                    # 客户端配置
                    client_config = LLMClientConfig.from_dict(config_data)
                    model_key = f"{client_config.model_type}:{client_config.model_name}"
                    self._client_configs[model_key] = client_config
                
                # 触发回调
                for callback in self._reload_callbacks:
                    try:
                        callback(config_path, config_data)
                    except Exception as e:
                        logger.error(f"配置重载回调执行失败: {e}")
                
                logger.info(f"LLM配置文件重新加载成功: {file_name}")
            except Exception as e:
                logger.error(f"重新加载LLM配置文件失败 {file_name}: {e}")
    
    def get_client_config(self, model_type: str, model_name: str) -> Optional[LLMClientConfig]:
        """获取客户端配置"""
        model_key = f"{model_type}:{model_name}"
        return self._client_configs.get(model_key)
    
    def get_module_config(self) -> LLMModuleConfig:
        """获取模块配置"""
        return self._module_config or LLMModuleConfig()
    
    def list_available_models(self) -> List[str]:
        """列出所有可用模型"""
        return list(self._client_configs.keys())
    
    def add_reload_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """添加配置重载回调"""
        self._reload_callbacks.append(callback)
    
    def remove_reload_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """移除配置重载回调"""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)
    
    def reload_all_configs(self) -> None:
        """手动重新加载所有配置"""
        with self._lock:
            self._load_all_configs()
            logger.info("手动配置重载完成")
    
    def save_config(self, config: Dict[str, Any], file_name: str) -> None:
        """保存配置到文件"""
        file_path = self.config_dir / file_name
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
                elif file_path.suffix.lower() == '.json':
                    json.dump(config, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"不支持的配置文件格式: {file_path.suffix}")
            
            logger.info(f"配置已保存到: {file_path}")
            
        except Exception as e:
            raise LLMConfigurationError(f"保存配置失败: {e}")
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        return {
            "config_dir": str(self.config_dir),
            "hot_reload_enabled": self.enable_hot_reload,
            "validation_enabled": self.validation_enabled,
            "loaded_client_configs": len(self._client_configs),
            "available_models": list(self._client_configs.keys()),
            "module_config_loaded": self._module_config is not None,
            "cached_files": list(self._config_cache.keys()),
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._stop_hot_reload()


# 全局配置管理器实例
_global_config_manager: Optional[LLMConfigManager] = None


def get_global_config_manager() -> LLMConfigManager:
    """获取全局配置管理器"""
    # 注意：这个函数现在依赖于一个全局的 IConfigLoader 实例
    # 在实际应用中，这应该通过依赖注入容器来解决
    # 为了向后兼容，我们在这里创建一个默认的 YamlConfigLoader
    from ..config.loader.file_config_loader import FileConfigLoader
    
    global _global_config_manager
    if _global_config_manager is None:
        # 这是一个临时解决方案，理想情况下应该从容器获取
        default_loader = FileConfigLoader()
        _global_config_manager = LLMConfigManager(config_loader=default_loader)
    return _global_config_manager


def set_global_config_manager(manager: LLMConfigManager) -> None:
    """设置全局配置管理器"""
    global _global_config_manager
    _global_config_manager = manager