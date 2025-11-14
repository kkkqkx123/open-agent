"""提示词注册表实现"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from infrastructure.config.config_loader import IConfigLoader
from src.infrastructure.exceptions import ConfigurationError
from .interfaces import IPromptRegistry
from .models import PromptMeta


class PromptRegistry(IPromptRegistry):
    """提示词注册表实现"""
    
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader
        self._registry: Dict[str, Dict[str, PromptMeta]] = {
            "system": {},
            "rules": {},
            "user_commands": {}
        }
        self._load_registry()
        
    def _load_registry(self) -> None:
        """加载注册表配置"""
        try:
            registry_config = self.config_loader.load("prompts.yaml")
        except ConfigurationError as e:
            raise ConfigurationError(f"无法加载提示词注册表配置: {e}")
        
        for category, prompts in registry_config.items():
            if category not in self._registry:
                self._registry[category] = {}
                
            for prompt_data in prompts:
                meta = PromptMeta(
                    name=prompt_data["name"],
                    category=category,
                    path=Path(prompt_data["path"]),
                    description=prompt_data["description"],
                    is_composite=prompt_data.get("is_composite", False),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # 检查重名
                if meta.name in self._registry[category]:
                    raise ValueError(f"提示词名称重复: {category}.{meta.name}")
                    
                self._registry[category][meta.name] = meta
                
    def get_prompt_meta(self, category: str, name: str) -> PromptMeta:
        """获取提示词元信息"""
        if category not in self._registry:
            raise ValueError(f"不支持的提示词类别: {category}")
            
        if name not in self._registry[category]:
            raise ValueError(f"提示词不存在: {category}.{name}")
            
        return self._registry[category][name]
        
    def list_prompts(self, category: str) -> List[PromptMeta]:
        """列出指定类别的所有提示词"""
        if category not in self._registry:
            raise ValueError(f"不支持的提示词类别: {category}")
            
        return list(self._registry[category].values())
        
    def register_prompt(self, category: str, meta: PromptMeta) -> None:
        """注册提示词"""
        if category not in self._registry:
            self._registry[category] = {}
            
        # 检查重名
        if meta.name in self._registry[category]:
            raise ValueError(f"提示词名称重复: {category}.{meta.name}")
            
        self._registry[category][meta.name] = meta
        
    def validate_registry(self) -> bool:
        """验证注册表完整性"""
        for category, prompts in self._registry.items():
            for name, meta in prompts.items():
                if not meta.validate_path():
                    raise FileNotFoundError(f"提示词文件不存在: {meta.path}")
                    
        return True