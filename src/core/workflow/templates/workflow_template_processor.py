"""
工作流模板处理器

提供工作流特定的模板处理功能，包括步骤循环等逻辑
"""

from typing import Dict, Any, List
import re


class WorkflowTemplateProcessor:
    """工作流模板处理器"""
    
    @staticmethod
    def process_template(content: str, context: Dict[str, Any]) -> str:
        """处理工作流模板"""
        processed_content = content
        
        # 处理步骤循环
        processed_content = WorkflowTemplateProcessor._process_step_loops(
            processed_content, context
        )
        
        # 处理条件逻辑
        processed_content = WorkflowTemplateProcessor._process_conditional_logic(
            processed_content, context
        )
        
        # 处理变量替换
        processed_content = WorkflowTemplateProcessor._replace_variables(
            processed_content, context
        )
        
        return processed_content
    
    @staticmethod
    def _process_step_loops(content: str, context: Dict[str, Any]) -> str:
        """处理步骤循环"""
        # 处理步骤循环语法: {{for step in steps}}...{{endfor}}
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
                
                # 递归处理步骤模板
                step_content = WorkflowTemplateProcessor.process_template(
                    step_template, step_context
                )
                
                result.append(step_content)
            
            return "\n".join(result)
        
        return re.sub(pattern, replace_step_loop, content, flags=re.DOTALL)
    
    @staticmethod
    def _process_conditional_logic(content: str, context: Dict[str, Any]) -> str:
        """处理条件逻辑"""
        # 处理 if-else 语句: {{if condition}}...{{else}}...{{endif}}
        pattern = r'\{\{if\s+(\w+)\}\}(.*?)\{\{else\}\}(.*?)\{\{endif\}\}'
        
        def replace_conditional(match):
            condition = match.group(1)
            if_content = match.group(2)
            else_content = match.group(3)
            
            if context.get(condition, False):
                return WorkflowTemplateProcessor.process_template(if_content, context)
            else:
                return WorkflowTemplateProcessor.process_template(else_content, context)
        
        # 先处理带 else 的条件
        content = re.sub(pattern, replace_conditional, content, flags=re.DOTALL)
        
        # 处理不带 else 的条件: {{if condition}}...{{endif}}
        pattern_simple = r'\{\{if\s+(\w+)\}\}(.*?)\{\{endif\}\}'
        
        def replace_conditional_simple(match):
            condition = match.group(1)
            if_content = match.group(2)
            
            if context.get(condition, False):
                return WorkflowTemplateProcessor.process_template(if_content, context)
            else:
                return ""
        
        content = re.sub(pattern_simple, replace_conditional_simple, content, flags=re.DOTALL)
        
        return content
    
    @staticmethod
    def _replace_variables(content: str, context: Dict[str, Any]) -> str:
        """替换变量"""
        def replace_variable(match):
            var_name = match.group(1).strip()
            
            # 支持嵌套属性访问: {{user.name}}
            if "." in var_name:
                parts = var_name.split(".")
                value = context
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
            else:
                value = context.get(var_name)
            
            return str(value) if value is not None else ""
        
        # 替换变量语法: {{variable_name}}
        pattern = r'\{\{([^}]+)\}\}'
        return re.sub(pattern, replace_variable, content)
    
    @staticmethod
    def validate_template(content: str) -> List[str]:
        """验证模板语法"""
        errors = []
        
        # 检查未闭合的循环
        for_count = len(re.findall(r'\{\{for\s+', content))
        endfor_count = len(re.findall(r'\{\{endfor\}\}', content))
        if for_count != endfor_count:
            errors.append(f"循环标签不匹配: for标签({for_count}) != endfor标签({endfor_count})")
        
        # 检查未闭合的条件
        if_count = len(re.findall(r'\{\{if\s+', content))
        endif_count = len(re.findall(r'\{\{endif\}\}', content))
        if if_count != endif_count:
            errors.append(f"条件标签不匹配: if标签({if_count}) != endif标签({endif_count})")
        
        # 检查 else 标签
        else_count = len(re.findall(r'\{\{else\}\}', content))
        if else_count > if_count:
            errors.append("else标签数量超过了if标签数量")
        
        return errors