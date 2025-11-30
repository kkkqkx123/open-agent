"""错误分类定义"""

from enum import Enum


class ErrorCategory(Enum):
    """错误分类"""
    VALIDATION = "validation"       # 验证错误
    CONFIGURATION = "configuration" # 配置错误
    RESOURCE = "resource"           # 资源错误
    NETWORK = "network"             # 网络错误
    STORAGE = "storage"             # 存储错误
    STATE = "state"                 # 状态错误
    EXECUTION = "execution"         # 执行错误
    INTEGRATION = "integration"     # 集成错误
    TOOL = "tool"                   # 工具错误
    WORKFLOW = "workflow"           # 工作流错误
    LLM = "llm"                     # LLM错误
    PROMPT = "prompt"               # 提示词错误