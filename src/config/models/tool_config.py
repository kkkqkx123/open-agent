"""工具配置模型"""

from typing import List, Dict, Any, Optional
from pydantic import Field, field_validator

from .base import BaseConfig


class ToolConfig(BaseConfig):
    """工具配置模型"""

    # 基础配置
    name: str = Field(..., description="工具名称")
    description: str = Field("", description="工具描述")

    # 工具配置
    tools: List[str] = Field(default_factory=list, description="工具列表")
    timeout: int = Field(30, description="超时时间（秒）")
    max_retries: int = Field(3, description="最大重试次数")

    # 参数配置
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")

    # 继承配置
    group: Optional[str] = Field(None, description="所属组名称")

    # 高级配置
    enabled: bool = Field(True, description="是否启用")
    parallel: bool = Field(False, description="是否支持并行执行")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证名称"""
        if not v or not v.strip():
            raise ValueError("工具名称不能为空")
        return v.strip()

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """验证超时时间"""
        if v < 1:
            raise ValueError("超时时间必须大于0秒")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """验证最大重试次数"""
        if v < 0:
            raise ValueError("最大重试次数不能为负数")
        return v

    def has_tool(self, tool: str) -> bool:
        """检查是否包含指定工具"""
        return tool in self.tools

    def add_tool(self, tool: str) -> None:
        """添加工具"""
        if tool not in self.tools:
            self.tools.append(tool)

    def remove_tool(self, tool: str) -> None:
        """移除工具"""
        if tool in self.tools:
            self.tools.remove(tool)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters[key] = value

    def merge_parameters(self, other_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """合并参数"""
        result = self.parameters.copy()
        result.update(other_parameters)
        return result

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled

    def enable(self) -> None:
        """启用工具"""
        self.enabled = True

    def disable(self) -> None:
        """禁用工具"""
        self.enabled = False

    def supports_parallel(self) -> bool:
        """检查是否支持并行执行"""
        return self.parallel

    def enable_parallel(self) -> None:
        """启用并行执行"""
        self.parallel = True

    def disable_parallel(self) -> None:
        """禁用并行执行"""
        self.parallel = False


class ToolSetConfig(ToolConfig):
    """工具集配置模型"""

    # 工具集特有配置
    tool_sets: List[str] = Field(default_factory=list, description="子工具集列表")

    def has_tool_set(self, tool_set: str) -> bool:
        """检查是否包含指定工具集"""
        return tool_set in self.tool_sets

    def add_tool_set(self, tool_set: str) -> None:
        """添加工具集"""
        if tool_set not in self.tool_sets:
            self.tool_sets.append(tool_set)

    def remove_tool_set(self, tool_set: str) -> None:
        """移除工具集"""
        if tool_set in self.tool_sets:
            self.tool_sets.remove(tool_set)

    def get_all_tools(self) -> List[str]:
        """获取所有工具（包括工具集中的工具）"""
        # 注意：这里只返回直接配置的工具，工具集中的工具需要在运行时解析
        return self.tools.copy()
