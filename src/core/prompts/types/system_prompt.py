"""
系统提示词类型实现

提供系统提示词的处理和消息创建功能
"""

from typing import Dict, Any, List, Optional
from src.interfaces.prompts.types import IPromptType, PromptType
from src.interfaces.messages import IMessageFactory


class SystemPromptType(IPromptType):
    """系统提示词类型"""
    
    def __init__(self, message_factory: Optional[IMessageFactory] = None):
        """初始化系统提示词类型
        
        Args:
            message_factory: 消息工厂接口，用于创建消息对象
        """
        self._message_factory = message_factory
    
    @property
    def type_name(self) -> str:
        return PromptType.SYSTEM.value
    
    @property
    def injection_order(self) -> int:
        return 10  # 最先注入
    
    async def process_prompt(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """处理系统提示词"""
        # 可以在这里添加变量替换等处理逻辑
        processed_content = content
        
        # 替换变量
        if context:
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                if isinstance(value, str):
                    processed_content = processed_content.replace(placeholder, value)
        
        return processed_content
    
    def create_message(self, content: str) -> Any:
        """创建系统消息"""
        if self._message_factory:
            return self._message_factory.create_system_message(content)
        else:
            # 降级处理：如果没有提供消息工厂，使用默认实现
            from src.infrastructure.messages.factory import get_message_factory
            factory = get_message_factory()
            return factory.create_system_message(content)
    
    def validate_content(self, content: str) -> List[str]:
        """验证系统提示词内容"""
        errors = []
        
        # 检查内容是否为空
        if not content.strip():
            errors.append("系统提示词内容不能为空")
        
        # 检查长度
        if len(content) > 10000:
            errors.append("系统提示词内容过长")
        
        # 检查是否包含基本结构
        if "你是一个" not in content and "你是一个" not in content.lower():
            errors.append("系统提示词应该包含角色定义")
        
        return errors