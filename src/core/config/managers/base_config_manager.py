"""配置管理器基类

提供所有配置管理器的通用功能模板。
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from pathlib import Path

from src.interfaces.dependency_injection import get_logger
from src.interfaces.config import IConfigManager


logger = get_logger(__name__)


class BaseConfigManager(ABC):
    """配置管理器基类
    
    提供配置加载、验证、保存等通用功能。
    子类应重写具体的配置数据模型和验证器。
    """
    
    def __init__(self, config_manager: IConfigManager, config_path: Optional[str] = None):
        """初始化配置管理器基类
        
        Args:
            config_manager: 统一配置管理器
            config_path: 配置文件路径
        """
        self.config_manager = config_manager
        self.config_path = config_path or self._get_default_config_path()
        self._config_data = None
        
        # 加载配置
        self._load_config()
    
    @abstractmethod
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径
        
        Returns:
            默认配置文件路径
        """
        pass
    
    @abstractmethod
    def _get_config_module(self) -> str:
        """获取配置模块名
        
        Returns:
            配置模块名（用于config_manager.load_config的第二个参数）
        """
        pass
    
    @abstractmethod
    def _create_config_data(self, config_dict: Dict[str, Any]) -> Any:
        """创建配置数据对象
        
        Args:
            config_dict: 配置字典
            
        Returns:
            配置数据对象
        """
        pass
    
    @abstractmethod
    def _get_validator(self) -> Any:
        """获取配置验证器
        
        Returns:
            配置验证器实例
        """
        pass
    
    @abstractmethod
    def _create_default_config(self) -> Any:
        """创建默认配置
        
        Returns:
            默认配置数据对象
        """
        pass
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            # 检查配置文件是否存在
            if not self._config_file_exists():
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config_data = self._create_default_config()
                return
            
            # 使用统一配置管理器加载配置
            config_dict = self.config_manager.load_config(
                self.config_path, 
                self._get_config_module()
            )
            
            # 创建配置数据
            self._config_data = self._create_config_data(config_dict)
            
            # 验证配置
            validator = self._get_validator()
            validation_result = validator.validate(config_dict)
            if not validation_result.is_valid:
                logger.error(f"配置验证失败: {validation_result.errors}")
                self._config_data = self._create_default_config()
                return
            
            logger.info(f"已加载配置: {self.config_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            self._config_data = self._create_default_config()
    
    def _config_file_exists(self) -> bool:
        """检查配置文件是否存在"""
        try:
            return Path(self.config_path).exists()
        except Exception:
            return False
    
    def get_config_data(self) -> Any:
        """获取配置数据
        
        Returns:
            配置数据对象
        """
        if self._config_data is None:
            self._load_config()
        assert self._config_data is not None, "配置数据加载失败"
        return self._config_data
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._load_config()
        logger.info("配置已重新加载")
    
    def save_config(self, path: Optional[str] = None) -> None:
        """保存配置到文件
        
        Args:
            path: 保存路径，如果为None则使用当前配置路径
        """
        save_path = path or self.config_path
        try:
            # 确保目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            import yaml
            config_dict = self.get_config_data().to_dict()
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            验证是否通过
        """
        try:
            config_dict = self.get_config_data().to_dict()
            validator = self._get_validator()
            validation_result = validator.validate(config_dict)
            return validation_result.is_valid
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def _process_env_variables(self, config_data: Any) -> Any:
        """处理环境变量注入
        
        Args:
            config_data: 配置数据对象
            
        Returns:
            处理后的配置数据对象
        """
        # 创建配置副本
        config_dict = config_data.to_dict()
        config_section = config_dict.get('config', config_dict)
        
        # 处理配置中的环境变量
        if isinstance(config_section, dict):
            for key, value in config_section.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    # 解析环境变量格式: ${ENV_VAR:DEFAULT}
                    env_expr = value[2:-1]  # 移除 ${ 和 }
                    
                    if ":" in env_expr:
                        env_var, default_value = env_expr.split(":", 1)
                    else:
                        env_var, default_value = env_expr, ""
                    
                    # 获取环境变量值
                    env_value = os.getenv(env_var, default_value)
                    
                    # 尝试转换类型
                    config_section[key] = self._convert_env_value(env_value)
        
        return self._create_config_data(config_dict)
    
    @staticmethod
    def _convert_env_value(value: str) -> Any:
        """转换环境变量值类型
        
        Args:
            value: 环境变量值
            
        Returns:
            转换后的值
        """
        # 布尔值
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False
        
        # 整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # 字符串
        return value
