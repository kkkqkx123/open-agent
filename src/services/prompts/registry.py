"""提示词注册表实现

负责管理提示词的元信息和注册。
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING

from ...interfaces.prompts import IPromptRegistry, PromptMeta
from ...core.common.exceptions import PromptRegistryError, PromptNotFoundError

if TYPE_CHECKING:
    from ...interfaces.common import IConfigLoader


class PromptRegistry(IPromptRegistry):
    """提示词注册表实现
    
    负责加载和管理提示词元信息。
    """
    
    def __init__(self, config_loader: "IConfigLoader") -> None:
        """初始化提示词注册表
        
        Args:
            config_loader: 配置加载器实例
        """
        self.config_loader = config_loader
        self._registry: Dict[str, Dict[str, PromptMeta]] = {
            "system": {},
            "rules": {},
            "user_commands": {}
        }
        self._load_registry()
        
    def _load_registry(self) -> None:
        """加载注册表配置
        
        从prompts.yaml配置文件加载提示词元信息。
        
        Raises:
            PromptRegistryError: 加载配置失败
        """
        try:
            registry_config = self.config_loader.load("prompts.yaml")
        except Exception as e:
            raise PromptRegistryError(f"无法加载提示词注册表配置: {e}") from e
        
        for category, prompts in registry_config.items():
            if category not in self._registry:
                self._registry[category] = {}
                
            if not isinstance(prompts, list):
                continue
                
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
                    raise PromptRegistryError(
                        f"提示词名称重复: {category}.{meta.name}"
                    )
                    
                self._registry[category][meta.name] = meta
                
    def get_prompt_meta(self, category: str, name: str) -> PromptMeta:
        """获取提示词元信息
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            PromptMeta: 提示词元信息
            
        Raises:
            PromptNotFoundError: 提示词不存在
            PromptRegistryError: 类别不支持
        """
        if category not in self._registry:
            raise PromptRegistryError(f"不支持的提示词类别: {category}")
            
        if name not in self._registry[category]:
            raise PromptNotFoundError(
                f"提示词不存在: {category}.{name}"
            )
            
        return self._registry[category][name]
        
    def list_prompts(self, category: str) -> List[PromptMeta]:
        """列出指定类别的所有提示词
        
        Args:
            category: 提示词类别
            
        Returns:
            List[PromptMeta]: 提示词元信息列表
            
        Raises:
            PromptRegistryError: 类别不支持
        """
        if category not in self._registry:
            raise PromptRegistryError(f"不支持的提示词类别: {category}")
            
        return list(self._registry[category].values())
        
    def register_prompt(self, category: str, meta: PromptMeta) -> None:
        """注册提示词
        
        Args:
            category: 提示词类别
            meta: 提示词元信息
            
        Raises:
            PromptRegistryError: 注册失败（如重名或类别不支持）
        """
        if category not in self._registry:
            self._registry[category] = {}
            
        # 检查重名
        if meta.name in self._registry[category]:
            raise PromptRegistryError(
                f"提示词名称重复: {category}.{meta.name}"
            )
            
        self._registry[category][meta.name] = meta
        
    def validate_registry(self) -> bool:
        """验证注册表完整性
        
        检查所有注册的提示词文件是否存在。
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            PromptRegistryError: 文件不存在
        """
        for category, prompts in self._registry.items():
            for name, meta in prompts.items():
                if not meta.validate_path():
                    raise PromptRegistryError(
                        f"提示词文件不存在: {meta.path}"
                    )
                    
        return True
