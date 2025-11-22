"""
用户命令提示词类型实现

提供用户命令提示词的处理和消息创建功能
"""

from typing import Dict, Any, List
from ....interfaces.prompts.types import IPromptType, PromptType


class UserCommandPromptType(IPromptType):
    """用户命令提示词类型"""
    
    @property
    def type_name(self) -> str:
        return PromptType.USER_COMMAND.value
    
    @property
    def injection_order(self) -> int:
        return 30  # 在规则提示词之后注入
    
    async def process_prompt(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """处理用户命令提示词"""
        # 用户命令提示词可能需要复杂的处理
        processed_content = content
        
        # 替换变量
        if context:
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                if isinstance(value, str):
                    processed_content = processed_content.replace(placeholder, value)
        
        # 处理条件逻辑
        processed_content = self._process_conditional_logic(processed_content, context)
        
        return processed_content
    
    def create_message(self, content: str) -> Any:
        """创建用户消息"""
        from langchain_core.messages import HumanMessage
        return HumanMessage(content=content)
    
    def validate_content(self, content: str) -> List[str]:
        """验证用户命令提示词内容"""
        errors = []
        
        # 检查内容是否为空
        if not content.strip():
            errors.append("用户命令提示词内容不能为空")
        
        # 检查长度
        if len(content) > 10000:
            errors.append("用户命令提示词内容过长")
        
        # 检查是否包含命令动词
        command_verbs = ["请", "帮助", "生成", "创建", "分析", "处理", "执行", "计算"]
        has_command_verb = any(verb in content for verb in command_verbs)
        
        if not has_command_verb:
            errors.append("用户命令提示词应该包含命令动词")
        
        return errors
    
    def _process_conditional_logic(self, content: str, context: Dict[str, Any]) -> str:
        """处理条件逻辑"""
        import re
        
        # 处理 if-else 语句
        pattern = r'\{\{if\s+(\w+)\}\}(.*?)\{\{else\}\}(.*?)\{\{endif\}\}'
        
        def replace_conditional(match):
            condition = match.group(1)
            if_content = match.group(2)
            else_content = match.group(3)
            
            if context.get(condition, False):
                return if_content
            else:
                return else_content
        
        return re.sub(pattern, replace_conditional, content, flags=re.DOTALL)