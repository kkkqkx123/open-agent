"""Agent配置模型"""

from typing import List, Dict, Any, Optional
from pydantic import Field, field_validator

from .base import BaseConfig


class AgentConfig(BaseConfig):
    """Agent配置模型"""

    # 基础配置
    name: str = Field(..., description="Agent名称")
    llm: str = Field(..., description="使用的LLM配置名称")

    # 工具配置
    tool_sets: List[str] = Field(default_factory=list, description="工具集列表")
    tools: List[str] = Field(default_factory=list, description="直接使用的工具列表")

    # 提示词配置
    system_prompt: str = Field("", description="系统提示词")
    rules: List[str] = Field(default_factory=list, description="规则列表")
    user_command: str = Field("", description="用户命令")

    # 继承配置
    group: Optional[str] = Field(None, description="所属组名称")

    # 高级配置
    max_iterations: int = Field(10, description="最大迭代次数")
    timeout: int = Field(60, description="超时时间（秒）")
    retry_count: int = Field(3, description="重试次数")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证名称"""
        if not v or not v.strip():
            raise ValueError("Agent名称不能为空")
        return v.strip()

    @field_validator("llm")
    @classmethod
    def validate_llm(cls, v: str) -> str:
        """验证LLM配置名称"""
        if not v or not v.strip():
            raise ValueError("LLM配置名称不能为空")
        return v.strip()

    @field_validator("max_iterations")
    @classmethod
    def validate_max_iterations(cls, v: int) -> int:
        """验证最大迭代次数"""
        if v < 1:
            raise ValueError("最大迭代次数必须大于0")
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """验证超时时间"""
        if v < 1:
            raise ValueError("超时时间必须大于0秒")
        return v

    @field_validator("retry_count")
    @classmethod
    def validate_retry_count(cls, v: int) -> int:
        """验证重试次数"""
        if v < 0:
            raise ValueError("重试次数不能为负数")
        return v

    def has_tool_set(self, tool_set: str) -> bool:
        """检查是否包含指定工具集"""
        return tool_set in self.tool_sets

    def has_tool(self, tool: str) -> bool:
        """检查是否包含指定工具"""
        return tool in self.tools

    def add_tool_set(self, tool_set: str) -> None:
        """添加工具集"""
        if tool_set not in self.tool_sets:
            self.tool_sets.append(tool_set)

    def add_tool(self, tool: str) -> None:
        """添加工具"""
        if tool not in self.tools:
            self.tools.append(tool)

    def remove_tool_set(self, tool_set: str) -> None:
        """移除工具集"""
        if tool_set in self.tool_sets:
            self.tool_sets.remove(tool_set)

    def remove_tool(self, tool: str) -> None:
        """移除工具"""
        if tool in self.tools:
            self.tools.remove(tool)

    def get_all_tools(self) -> List[str]:
        """获取所有工具（包括工具集中的工具）"""
        # 注意：这里只返回直接配置的工具，工具集中的工具需要在运行时解析
        return self.tools.copy()

    def add_rule(self, rule: str) -> None:
        """添加规则"""
        if rule not in self.rules:
            self.rules.append(rule)

    def remove_rule(self, rule: str) -> None:
        """移除规则"""
        if rule in self.rules:
            self.rules.remove(rule)

    def has_rule(self, rule: str) -> bool:
        """检查是否包含指定规则"""
        return rule in self.rules
