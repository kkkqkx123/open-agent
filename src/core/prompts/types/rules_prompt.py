"""
规则提示词类型实现

提供规则提示词的处理和消息创建功能
"""

from typing import Dict, Any, List
from src.interfaces.prompts.types import IPromptType, PromptType


class RulesPromptType(IPromptType):
    """规则提示词类型"""
    
    @property
    def type_name(self) -> str:
        return PromptType.RULES.value
    
    @property
    def injection_order(self) -> int:
        return 20  # 在系统提示词之后注入
    
    async def process_prompt(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """处理规则提示词"""
        # 规则提示词通常不需要复杂的处理
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
        from langchain_core.messages import SystemMessage
        return SystemMessage(content=content)
    
    def validate_content(self, content: str) -> List[str]:
        """验证规则提示词内容"""
        errors = []
        
        # 检查内容是否为空
        if not content.strip():
            errors.append("规则提示词内容不能为空")
        
        # 检查长度
        if len(content) > 5000:
            errors.append("规则提示词内容过长")
        
        # 检查是否包含规则关键词
        rule_keywords = ["必须", "不能", "应该", "禁止", "要求", "遵循"]
        has_rule_keyword = any(keyword in content for keyword in rule_keywords)
        
        if not has_rule_keyword:
            errors.append("规则提示词应该包含规则关键词")
        
        return errors