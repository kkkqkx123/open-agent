"""提示词依赖注入便利层

简化实现避免循环依赖，提供基本的提示词服务获取方式。
"""

import sys
from typing import Optional

from src.interfaces.messages import IMessageFactory


class _StubMessageFactory(IMessageFactory):
    """临时消息工厂实现（用于极端情况）
    
    当消息工厂初始化失败时使用此实现，确保代码不会因为
    缺少消息工厂而直接崩溃。
    """
    
    def create_system_message(self, content: str, **kwargs):
        """创建系统消息"""
        from src.infrastructure.messages.types import SystemMessage
        return SystemMessage(content=content, **kwargs)
    
    def create_human_message(self, content: str, **kwargs):
        """创建人类消息"""
        from src.infrastructure.messages.types import HumanMessage
        return HumanMessage(content=content, **kwargs)
    
    def create_ai_message(self, content: str, **kwargs):
        """创建AI消息"""
        from src.infrastructure.messages.types import AIMessage
        return AIMessage(content=content, **kwargs)
    
    def create_tool_message(self, content: str, tool_call_id: str, **kwargs):
        """创建工具消息"""
        from src.infrastructure.messages.types import ToolMessage
        return ToolMessage(content=content, tool_call_id=tool_call_id, **kwargs)
    
    def create_message_from_type(self, message_type: str, content: str, **kwargs):
        """根据类型创建消息"""
        if message_type.lower() in ["system"]:
            return self.create_system_message(content, **kwargs)
        elif message_type.lower() in ["human", "user"]:
            return self.create_human_message(content, **kwargs)
        elif message_type.lower() in ["ai", "assistant"]:
            return self.create_ai_message(content, **kwargs)
        elif message_type.lower() == "tool":
            tool_call_id = kwargs.get("tool_call_id", "stub_id")
            return self.create_tool_message(content, tool_call_id, **kwargs)
        else:
            raise ValueError(f"Unknown message type: {message_type}")


class _StubPromptTypeRegistry:
    """临时提示词类型注册表实现（用于极端情况）"""
    
    def register(self, name: str, prompt_type):
        """注册提示词类型"""
        print(f"[STUB] 注册提示词类型: {name}", file=sys.stdout)
    
    def get(self, name: str):
        """获取提示词类型"""
        print(f"[STUB] 获取提示词类型: {name}", file=sys.stdout)
        return None
    
    def list_all(self):
        """列出所有提示词类型"""
        print(f"[STUB] 列出所有提示词类型", file=sys.stdout)
        return []


class _StubPromptErrorHandler:
    """临时提示词错误处理器实现（用于极端情况）"""
    
    def handle_error(self, error: Exception, context: dict | None = None):
        """处理错误"""
        print(f"[STUB] 处理提示词错误: {error}", file=sys.stderr)
    
    def register_retry_strategy(self, error_type, strategy):
        """注册重试策略"""
        print(f"[STUB] 注册重试策略: {error_type}", file=sys.stdout)
    
    def register_fallback_strategy(self, error_type, strategy):
        """注册降级策略"""
        print(f"[STUB] 注册降级策略: {error_type}", file=sys.stdout)


# 全局实例（简化实现）
_global_message_factory: Optional[IMessageFactory] = None
_global_prompt_type_registry: Optional[object] = None
_global_prompt_error_handler: Optional[object] = None


def get_message_factory() -> IMessageFactory:
    """获取消息工厂实例
    
    简化实现：直接返回全局实例或临时实现
    
    Returns:
        IMessageFactory: 消息工厂实例
    """
    global _global_message_factory
    if _global_message_factory is not None:
        return _global_message_factory
    
    # 返回临时实现
    return _StubMessageFactory()


def get_prompt_type_registry():
    """获取提示词类型注册表实例
    
    简化实现：直接返回全局实例或临时实现
    
    Returns:
        提示词类型注册表实例
    """
    global _global_prompt_type_registry
    if _global_prompt_type_registry is not None:
        return _global_prompt_type_registry
    
    # 返回临时实现
    return _StubPromptTypeRegistry()


def get_prompt_error_handler():
    """获取提示词错误处理器实例
    
    简化实现：直接返回全局实例或临时实现
    
    Returns:
        提示词错误处理器实例
    """
    global _global_prompt_error_handler
    if _global_prompt_error_handler is not None:
        return _global_prompt_error_handler
    
    # 返回临时实现
    return _StubPromptErrorHandler()


def set_message_factory_instance(message_factory: IMessageFactory) -> None:
    """在应用启动时设置全局消息工厂实例
    
    这个函数由容器的 prompts_bindings 在服务注册后调用。
    
    Args:
        message_factory: IMessageFactory 实例
    """
    global _global_message_factory
    _global_message_factory = message_factory


def set_prompt_type_registry_instance(registry) -> None:
    """在应用启动时设置全局提示词类型注册表实例
    
    这个函数由容器的 prompts_bindings 在服务注册后调用。
    
    Args:
        registry: 提示词类型注册表实例
    """
    global _global_prompt_type_registry
    _global_prompt_type_registry = registry


def set_prompt_error_handler_instance(error_handler) -> None:
    """在应用启动时设置全局提示词错误处理器实例
    
    这个函数由容器的 prompts_bindings 在服务注册后调用。
    
    Args:
        error_handler: 提示词错误处理器实例
    """
    global _global_prompt_error_handler
    _global_prompt_error_handler = error_handler


def clear_prompt_instances() -> None:
    """清除所有提示词服务实例
    
    主要用于测试环境重置。
    """
    global _global_message_factory, _global_prompt_type_registry, _global_prompt_error_handler
    _global_message_factory = None
    _global_prompt_type_registry = None
    _global_prompt_error_handler = None


def get_prompt_injection_status() -> dict:
    """获取提示词注入状态
    
    Returns:
        状态信息字典
    """
    return {
        "has_message_factory": _global_message_factory is not None,
        "has_prompt_type_registry": _global_prompt_type_registry is not None,
        "has_prompt_error_handler": _global_prompt_error_handler is not None,
        "message_factory_type": type(_global_message_factory).__name__ if _global_message_factory else None,
        "prompt_type_registry_type": type(_global_prompt_type_registry).__name__ if _global_prompt_type_registry else None,
        "prompt_error_handler_type": type(_global_prompt_error_handler).__name__ if _global_prompt_error_handler else None
    }


# 导出的公共接口
__all__ = [
    "get_message_factory",
    "get_prompt_type_registry",
    "get_prompt_error_handler",
    "set_message_factory_instance",
    "set_prompt_type_registry_instance",
    "set_prompt_error_handler_instance",
    "clear_prompt_instances",
    "get_prompt_injection_status",
]