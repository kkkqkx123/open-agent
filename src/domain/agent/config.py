"""Agent配置定义"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from ...config.models.base import BaseConfig  # 使用正确的BaseConfig路径


@dataclass
class MemoryConfig:
    """记忆配置"""
    enabled: bool = True
    max_size: int = 10
    retention_time: int = 3600  # 1小时


class AgentConfig(BaseConfig):
    # 基础配置
    name: str = ""
    description: str = ""
    agent_type: str = ""  # 指定Agent类型，如"react", "plan_execute"等
    
    # 智能配置
    system_prompt: str = ""
    decision_strategy: str = ""  # 决策策略
    memory_config: Optional[MemoryConfig] = None  # 记忆配置
    
    # 工具配置
    tools: List[str] = field(default_factory=list)
    tool_sets: List[str] = field(default_factory=list)
    
    # 行为配置
    max_iterations: int = 10
    timeout: int = 300  # 5分钟超时
    retry_count: int = 3
    
    # LLM配置
    llm: str = ""  # LLM模型标识符
    
    # 其他配置
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.memory_config is None:
            self.memory_config = MemoryConfig()