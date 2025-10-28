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
        config_dir: Optional[Union[str, Path]] = None,
        enable_hot_reload: bool = True,
        validation_enabled: bool = True,
    ) -> None:
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
            enable_hot_reload: 是否启用热重载
            validation_enabled: 是否启用配置验证
        """
        self.config_dir = Path(config_dir) if config_dir else Path("configs/llms")
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
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
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
        module_config_file = self.config_dir / "_group.yaml"
        
        if module_config_file.exists():
            config_data = self._load_config_file(module_config_file)
            if config_data:
                self._module_config = LLMModuleConfig.from_dict(config_data)
        else:
            # 使用默认配置
            self._module_config = LLMModuleConfig()
            logger.warning("模块配置文件不存在，使用默认配置")
    
    def _load_client_configs(self) -> None:
        """加载客户端配置"""
        self._client_configs.clear()
        
        # 扫描配置文件
        for config_file in self.config_dir.glob("*.yaml"):
            if config_file.name.startswith("_"):
                continue  # 跳过组配置文件
            
            try:
                config_data = self._load_config_file(config_file)
                if config_data:
                    client_config = LLMClientConfig.from_dict(config_data)
                    model_key = f"{client_config.model_type}:{client_config.model_name}"
                    self._client_configs[model_key] = client_config
                    
                    # 缓存原始配置数据
                    self._config_cache[str(config_file)] = config_data
                    
            except Exception as e:
                logger.error(f"加载客户端配置失败 {config_file}: {e}")
    
    def _load_config_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载单个配置文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    logger.warning(f"不支持的配置文件格式: {file_path}")
                    return None
            
            # 环境变量替换
            config_data = self._substitute_env_vars(config_data)
            
            # 配置验证
            if self.validation_enabled:
                errors = self.validator.validate_config(config_data)
                if errors:
                    error_msg = f"配置验证失败 {file_path}:\n" + "\n".join(f"  - {error}" for error in errors)
                    raise LLMConfigurationError(error_msg)
            
            return config_data
            
        except Exception as e:
            logger.error(f"读取配置文件失败 {file_path}: {e}")
            return None
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """递归替换环境变量"""
        if isinstance(data, dict):
            return {key: self._substitute_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            return self._replace_env_vars(data)
        else:
            return data
    
    def _replace_env_vars(self, text: str) -> str:
        """替换字符串中的环境变量"""
        import re
        
        def replace_var(match):
            var_expr = match.group(1)
            
            # 支持默认值格式: ${VAR:default}
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                return os.getenv(var_expr.strip(), '')
        
        # 匹配 ${VAR} 或 ${VAR:default} 格式
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_var, text)
    
    def _start_hot_reload(self) -> None:
        """启动热重载"""
        try:
            self._observer = Observer()
            handler = ConfigFileHandler(self)
            self._observer.schedule(handler, str(self.config_dir), recursive=False)  # type: ignore
            self._observer.start()  # type: ignore
            logger.info("配置热重载已启动")
        except Exception as e:
            logger.error(f"启动热重载失败: {e}")
            self.enable_hot_reload = False
    
    def _stop_hot_reload(self) -> None:
        """停止热重载"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("配置热重载已停止")
    
    def _reload_config_file(self, file_path: Path) -> None:
        """重新加载配置文件"""
        with self._lock:
            try:
                # 重新加载配置数据
                config_data = self._load_config_file(file_path)
                if config_data is None:
                    return
                
                # 更新缓存
                self._config_cache[str(file_path)] = config_data
                
                # 如果是模块配置文件
                if file_path.name == "_group.yaml":
                    self._module_config = LLMModuleConfig.from_dict(config_data)
                else:
                    # 客户端配置
                    client_config = LLMClientConfig.from_dict(config_data)
                    model_key = f"{client_config.model_type}:{client_config.model_name}"
                    self._client_configs[model_key] = client_config
                
                # 触发回调
                for callback in self._reload_callbacks:
                    try:
                        callback(str(file_path), config_data)
                    except Exception as e:
                        logger.error(f"配置重载回调执行失败: {e}")
                
                logger.info(f"配置文件重新加载成功: {file_path}")
                
            except Exception as e:
                logger.error(f"重新加载配置文件失败 {file_path}: {e}")
    
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
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = LLMConfigManager()
    return _global_config_manager


def set_global_config_manager(manager: LLMConfigManager) -> None:
    """设置全局配置管理器"""
    global _global_config_manager
    _global_config_manager = manager