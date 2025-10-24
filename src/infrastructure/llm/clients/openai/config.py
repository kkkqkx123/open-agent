"""OpenAI扩展配置"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

from ...config import OpenAIConfig as BaseOpenAIConfig


@dataclass
class OpenAIConfig(BaseOpenAIConfig):
    """OpenAI扩展配置，支持API格式选择"""

    # API格式选择
    api_format: str = "chat_completion"  # chat_completion | responses
    api_format_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # 降级配置
    fallback_enabled: bool = True
    fallback_formats: List[str] = field(default_factory=lambda: ["chat_completion"])

    def __post_init__(self) -> None:
        """初始化后处理"""
        super().__post_init__()

        # 设置默认的API格式配置
        if not self.api_format_configs:
            self.api_format_configs = {
                "chat_completion": {
                    "endpoint": "/chat/completions",
                    "supports_multiple_choices": True,
                    "legacy_structured_output": True,
                },
                "responses": {
                    "endpoint": "/responses",
                    "supports_reasoning": True,
                    "native_storage": True,
                    "structured_output_format": "text.format",
                },
            }

    def get_api_format_config(self, format_name: str) -> Dict[str, Any]:
        """
        获取特定API格式的配置

        Args:
            format_name: API格式名称

        Returns:
            Dict[str, Any]: API格式配置
        """
        return self.api_format_configs.get(format_name, {})

    def is_api_format_supported(self, format_name: str) -> bool:
        """
        检查是否支持指定的API格式

        Args:
            format_name: API格式名称

        Returns:
            bool: 是否支持
        """
        return format_name in self.api_format_configs

    def get_fallback_formats(self) -> List[str]:
        """
        获取降级格式列表

        Returns:
            List[str]: 降级格式列表
        """
        if not self.fallback_enabled:
            return []

        # 排除当前使用的格式
        current_format = self.api_format
        fallbacks = [fmt for fmt in self.fallback_formats if fmt != current_format]

        return fallbacks

    def switch_api_format(self, format_name: str) -> None:
        """
        切换API格式

        Args:
            format_name: 新的API格式

        Raises:
            ValueError: 不支持的API格式
        """
        if not self.is_api_format_supported(format_name):
            raise ValueError(f"不支持的API格式: {format_name}")

        self.api_format = format_name
