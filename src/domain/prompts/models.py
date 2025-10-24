"""提示词管理模块数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List


@dataclass
class PromptMeta:
    """提示词元信息"""
    name: str                    # 提示词名称
    category: str               # 类别：system/rules/user_commands
    path: Path                  # 文件或目录路径
    description: str            # 描述
    is_composite: bool = False  # 是否为复合提示词
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    
    def validate_path(self) -> bool:
        """验证路径是否存在"""
        return self.path.exists()


@dataclass
class PromptConfig:
    """提示词配置"""
    system_prompt: Optional[str] = None      # 系统提示词名称
    rules: List[str] = field(default_factory=list)  # 规则提示词列表
    user_command: Optional[str] = None       # 用户指令名称
    cache_enabled: bool = True               # 是否启用缓存