"""模板渲染器工具类

提供模板渲染和变量替换的工具方法。
"""

import re
import os
from typing import Dict, Any, List, Optional, Union
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class TemplateRenderer:
    """模板渲染器工具类
    
    支持的模板语法：
    1. {variable} - 简单变量替换
    2. {{var:variable_name}} - 显式变量引用
    3. {{env:ENV_VAR}} - 环境变量引用
    4. {{config:config.path}} - 配置引用
    5. {{for item in items}}...{{endfor}} - 循环
    6. {{if condition}}...{{endif}} - 条件
    """
    
    # 简单变量模式
    SIMPLE_VAR_PATTERN = re.compile(r'\{([^}]+)\}')
    
    # 显式变量模式
    VAR_PATTERN = re.compile(r'\{\{\s*var\s*:\s*([^}]+)\s*\}\}', re.IGNORECASE)
    
    # 环境变量模式
    ENV_PATTERN = re.compile(r'\{\{\s*env\s*:\s*([^}]+)\s*\}\}', re.IGNORECASE)
    
    # 配置引用模式
    CONFIG_PATTERN = re.compile(r'\{\{\s*config\s*:\s*([^}]+)\s*\}\}', re.IGNORECASE)
    
    # 循环模式
    LOOP_PATTERN = re.compile(
        r'\{\{\s*for\s+(\w+)\s+in\s+(\w+)\s*\}\}(.*?)\{\{\s*endfor\s*\}\}',
        re.IGNORECASE | re.DOTALL
    )
    
    # 条件模式
    IF_PATTERN = re.compile(
        r'\{\{\s*if\s+([^}]+)\s*\}\}(.*?)\{\{\s*endif\s*\}\}',
        re.IGNORECASE | re.DOTALL
    )
    
    @classmethod
    def render_template(cls, template: str, context: Dict[str, Any]) -> str:
        """渲染模板
        
        Args:
            template: 模板字符串
            context: 上下文变量
            
        Returns:
            渲染后的字符串
        """
        try:
            result = template
            
            # 1. 处理循环
            result = cls._process_loops(result, context)
            
            # 2. 处理条件
            result = cls._process_conditions(result, context)
            
            # 3. 处理环境变量
            result = cls._process_environment_variables(result)
            
            # 4. 处理配置引用
            result = cls._process_config_references(result, context)
            
            # 5. 处理显式变量引用
            result = cls._process_variables(result, context)
            
            # 6. 处理简单变量引用
            result = cls._process_simple_variables(result, context)
            
            return result
            
        except Exception as e:
            logger.warning(f"模板渲染失败: {e}")
            return template
    
    @classmethod
    def _process_simple_variables(cls, content: str, context: Dict[str, Any]) -> str:
        """处理简单变量引用 {variable}"""
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(context.get(var_name, match.group(0)))
        
        return cls.SIMPLE_VAR_PATTERN.sub(replace_var, content)
    
    @classmethod
    def _process_variables(cls, content: str, context: Dict[str, Any]) -> str:
        """处理显式变量引用 {{var:variable_name}}"""
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(context.get(var_name, match.group(0)))
        
        return cls.VAR_PATTERN.sub(replace_var, content)
    
    @classmethod
    def _process_environment_variables(cls, content: str) -> str:
        """处理环境变量引用 {{env:ENV_VAR}}"""
        def replace_env(match):
            env_name = match.group(1).strip()
            return os.getenv(env_name, "")
        
        return cls.ENV_PATTERN.sub(replace_env, content)
    
    @classmethod
    def _process_config_references(cls, content: str, context: Dict[str, Any]) -> str:
        """处理配置引用 {{config:config.path}}"""
        def replace_config(match):
            config_path = match.group(1).strip()
            
            try:
                # 从上下文中获取配置值
                keys = config_path.split('.')
                value = context
                
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        logger.warning(f"配置路径不存在: {config_path}")
                        return match.group(0)
                
                return str(value) if value is not None else ""
                
            except Exception as e:
                logger.warning(f"解析配置引用失败: {config_path}, 错误: {e}")
                return match.group(0)
        
        return cls.CONFIG_PATTERN.sub(replace_config, content)
    
    @classmethod
    def _process_loops(cls, content: str, context: Dict[str, Any]) -> str:
        """处理循环 {{for item in items}}...{{endfor}}"""
        def replace_loop(match):
            var_name = match.group(1)
            collection_name = match.group(2)
            loop_content = match.group(3)
            
            try:
                # 获取集合
                collection = context.get(collection_name, [])
                if not isinstance(collection, (list, tuple)):
                    logger.warning(f"循环集合不是列表类型: {collection_name}")
                    return match.group(0)
                
                # 生成循环内容
                result_parts = []
                for item in collection:
                    loop_context = context.copy()
                    loop_context[var_name] = item
                    
                    # 递归渲染循环内容
                    rendered_item = cls.render_template(loop_content, loop_context)
                    result_parts.append(rendered_item)
                
                return "\n".join(result_parts)
                
            except Exception as e:
                logger.warning(f"处理循环失败: {var_name} in {collection_name}, 错误: {e}")
                return match.group(0)
        
        # 多次处理以支持嵌套循环
        result = content
        while cls.LOOP_PATTERN.search(result):
            result = cls.LOOP_PATTERN.sub(replace_loop, result, 1)
        
        return result
    
    @classmethod
    def _process_conditions(cls, content: str, context: Dict[str, Any]) -> str:
        """处理条件 {{if condition}}...{{endif}}"""
        def replace_condition(match):
            condition = match.group(1).strip()
            conditional_content = match.group(2)
            
            try:
                # 评估条件
                if cls._evaluate_condition(condition, context):
                    # 条件为真，渲染内容
                    return cls.render_template(conditional_content, context)
                else:
                    # 条件为假，返回空字符串
                    return ""
                    
            except Exception as e:
                logger.warning(f"处理条件失败: {condition}, 错误: {e}")
                return match.group(0)
        
        # 多次处理以支持嵌套条件
        result = content
        while cls.IF_PATTERN.search(result):
            result = cls.IF_PATTERN.sub(replace_condition, result, 1)
        
        return result
    
    @classmethod
    def _evaluate_condition(cls, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件表达式
        
        Args:
            condition: 条件表达式
            context: 上下文变量
            
        Returns:
            条件是否为真
        """
        try:
            # 简单的条件评估
            # 支持的格式：
            # 1. variable - 检查变量是否存在且为真
            # 2. variable == value - 检查变量是否等于值
            # 3. variable != value - 检查变量是否不等于值
            # 4. variable in list - 检查变量是否在列表中
            
            # 替换变量
            def replace_vars(match):
                var_name = match.group(1)
                if var_name in context:
                    value = context[var_name]
                    if isinstance(value, str):
                        return f'"{value}"'
                    else:
                        return str(value)
                else:
                    return "None"
            
            # 替换变量引用
            condition_with_values = re.sub(r'(\w+)', replace_vars, condition)
            
            # 安全评估条件
            # 注意：这里使用eval是为了简化实现，在生产环境中应该使用更安全的方法
            return bool(eval(condition_with_values))
            
        except Exception as e:
            logger.warning(f"评估条件失败: {condition}, 错误: {e}")
            return False
    
    @classmethod
    def extract_variables(cls, template: str) -> List[str]:
        """提取模板中的变量
        
        Args:
            template: 模板字符串
            
        Returns:
            变量名列表
        """
        variables = set()
        
        # 提取简单变量
        for match in cls.SIMPLE_VAR_PATTERN.finditer(template):
            var_name = match.group(1).strip()
            if not cls._is_control_structure(var_name):
                variables.add(var_name)
        
        # 提取显式变量
        for match in cls.VAR_PATTERN.finditer(template):
            var_name = match.group(1).strip()
            variables.add(var_name)
        
        # 提取循环变量
        for match in cls.LOOP_PATTERN.finditer(template):
            var_name = match.group(1)  # 循环变量
            collection_name = match.group(2)  # 集合变量
            variables.add(collection_name)
            
            # 递归提取循环内容中的变量
            loop_content = match.group(3)
            variables.update(cls.extract_variables(loop_content))
        
        # 提取条件中的变量
        for match in cls.IF_PATTERN.finditer(template):
            condition = match.group(1)
            conditional_content = match.group(2)
            
            # 提取条件中的变量
            condition_vars = re.findall(r'\w+', condition)
            variables.update(condition_vars)
            
            # 递归提取条件内容中的变量
            variables.update(cls.extract_variables(conditional_content))
        
        return list(variables)
    
    @classmethod
    def _is_control_structure(cls, text: str) -> bool:
        """检查是否是控制结构关键字"""
        control_keywords = {
            'for', 'in', 'endfor', 'if', 'endif', 'else', 'elif',
            'and', 'or', 'not', 'True', 'False', 'None'
        }
        return text in control_keywords
    
    @classmethod
    def validate_template(cls, template: str) -> List[str]:
        """验证模板语法
        
        Args:
            template: 模板字符串
            
        Returns:
            验证错误列表
        """
        errors = []
        
        try:
            # 检查循环语法
            cls._validate_loops(template, errors)
            
            # 检查条件语法
            cls._validate_conditions(template, errors)
            
            # 检查变量引用
            cls._validate_variables(template, errors)
            
        except Exception as e:
            errors.append(f"模板验证时发生错误: {e}")
        
        return errors
    
    @classmethod
    def _validate_loops(cls, template: str, errors: List[str]) -> None:
        """验证循环语法"""
        open_loops = []
        
        for match in cls.LOOP_PATTERN.finditer(template):
            open_loops.append(match)
        
        # 检查是否有未闭合的循环
        loop_count = len(open_loops)
        endfor_count = len(re.findall(r'\{\{\s*endfor\s*\}\}', template, re.IGNORECASE))
        
        if loop_count != endfor_count:
            errors.append(f"循环数量不匹配: {loop_count} 个循环开始, {endfor_count} 个循环结束")
    
    @classmethod
    def _validate_conditions(cls, template: str, errors: List[str]) -> None:
        """验证条件语法"""
        if_count = len(re.findall(r'\{\{\s*if\s+', template, re.IGNORECASE))
        endif_count = len(re.findall(r'\{\{\s*endif\s*\}\}', template, re.IGNORECASE))
        
        if if_count != endif_count:
            errors.append(f"条件数量不匹配: {if_count} 个条件开始, {endif_count} 个条件结束")
    
    @classmethod
    def _validate_variables(cls, template: str, errors: List[str]) -> None:
        """验证变量引用"""
        # 检查简单变量语法
        for match in cls.SIMPLE_VAR_PATTERN.finditer(template):
            var_name = match.group(1).strip()
            if not var_name:
                errors.append("发现空的变量名")
        
        # 检查显式变量语法
        for match in cls.VAR_PATTERN.finditer(template):
            var_name = match.group(1).strip()
            if not var_name:
                errors.append("发现空的变量名")