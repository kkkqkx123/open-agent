"""
工作流提示词类型实现

提供工作流提示词的处理和消息创建功能
"""

from typing import Dict, Any, List
from ....interfaces.prompts.types import IPromptType, PromptType


class WorkflowPromptType(IPromptType):
    """工作流提示词类型"""
    
    @property
    def type_name(self) -> str:
        return PromptType.WORKFLOW.value
    
    @property
    def injection_order(self) -> int:
        return 40  # 在用户命令提示词之后注入
    
    async def process_prompt(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """处理工作流提示词"""
        # 工作流提示词可能需要处理工作流特定的变量
        processed_content = content
        
        # 替换变量
        if context:
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                if isinstance(value, str):
                    processed_content = processed_content.replace(placeholder, value)
        
        # 处理工作流特定的逻辑
        processed_content = self._process_workflow_logic(processed_content, context)
        
        return processed_content
    
    def create_message(self, content: str) -> Any:
        """创建系统消息"""
        from langchain_core.messages import SystemMessage
        return SystemMessage(content=content)
    
    def validate_content(self, content: str) -> List[str]:
        """验证工作流提示词内容"""
        errors = []
        
        # 检查内容是否为空
        if not content.strip():
            errors.append("工作流提示词内容不能为空")
        
        # 检查长度
        if len(content) > 8000:
            errors.append("工作流提示词内容过长")
        
        # 检查是否包含工作流关键词
        workflow_keywords = ["工作流", "流程", "步骤", "阶段", "节点", "执行"]
        has_workflow_keyword = any(keyword in content for keyword in workflow_keywords)
        
        if not has_workflow_keyword:
            errors.append("工作流提示词应该包含工作流关键词")
        
        return errors
    
    def _process_workflow_logic(self, content: str, context: Dict[str, Any]) -> str:
        """处理工作流特定的逻辑"""
        import re
        
        # 处理步骤循环
        pattern = r'\{\{for\s+step\s+in\s+(\w+)\}\}(.*?)\{\{endfor\}\}'
        
        def replace_step_loop(match):
            steps_var = match.group(1)
            step_template = match.group(2)
            steps = context.get(steps_var, [])
            
            if not isinstance(steps, list):
                return ""
            
            result = []
            for i, step in enumerate(steps):
                step_context = context.copy()
                step_context["step"] = step
                step_context["step_index"] = i
                step_context["step_number"] = i + 1
                
                # 替换步骤变量
                step_content = step_template
                for key, value in step_context.items():
                    placeholder = f"{{{{{key}}}}}"
                    if isinstance(value, str):
                        step_content = step_content.replace(placeholder, value)
                
                result.append(step_content)
            
            return "\n".join(result)
        
        return re.sub(pattern, replace_step_loop, content, flags=re.DOTALL)