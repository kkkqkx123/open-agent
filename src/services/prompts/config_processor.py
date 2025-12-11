"""提示词配置处理器

处理新的提示词配置格式，支持多种配置方式和继承。
"""

import os
import re
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from src.interfaces.dependency_injection import get_logger
import yaml

from ...core.config.config_manager import ConfigManager
from ...interfaces.prompts.models import PromptConfig

logger = get_logger(__name__)


class PromptConfigProcessor:
    """提示词配置处理器
    
    支持的配置格式：
    1. 直接定义（向后兼容）
    2. 引用文件化提示词
    3. 模板化提示词
    4. 组合式提示词
    5. 缓存配置
    6. 提示词变量
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self._config_manager = config_manager
        self._variable_pattern = re.compile(r'\$\{([^}]+)\}')
        self._reference_pattern = re.compile(r'\{\{\s*ref\s*:\s*([^}]+)\s*\}\}')
        
        logger.debug("提示词配置处理器初始化完成")
    
    def process_node_config(self, config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理节点配置
        
        Args:
            config: 原始配置
            context: 上下文变量
            
        Returns:
            处理后的配置
        """
        context = context or {}
        processed_config = config.copy()
        
        try:
            # 1. 处理环境变量注入
            processed_config = self._process_environment_variables(processed_config)
            
            # 2. 处理提示词引用
            processed_config = self._process_prompt_references(processed_config, context)
            
            # 3. 处理模板化提示词
            processed_config = self._process_template_prompts(processed_config, context)
            
            # 4. 处理组合式提示词
            processed_config = self._process_composite_prompts(processed_config, context)
            
            # 5. 处理文件引用
            processed_config = self._process_file_references(processed_config, context)
            
            # 6. 设置默认缓存配置
            processed_config = self._set_default_cache_config(processed_config)
            
            logger.debug(f"节点配置处理完成: {len(processed_config)} 个字段")
            
        except Exception as e:
            logger.warning(f"处理节点配置失败: {e}")
            # 返回原始配置作为后备
            return config
        
        return processed_config
    
    def _process_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理环境变量注入"""
        processed_config = {}
        
        for key, value in config.items():
            if isinstance(value, str):
                # 处理 ${VAR:DEFAULT} 格式
                def replace_env_var(match):
                    var_expr = match.group(1)
                    if ':' in var_expr:
                        var_name, default_value = var_expr.split(':', 1)
                        return os.getenv(var_name.strip(), default_value.strip())
                    else:
                        return os.getenv(var_expr.strip(), '')
                
                processed_value = self._variable_pattern.sub(replace_env_var, value)
                processed_config[key] = processed_value
            else:
                processed_config[key] = value
        
        return processed_config
    
    def _process_prompt_references(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理提示词引用"""
        processed_config = config.copy()
        
        # 处理 system_prompt_ref
        if "system_prompt_ref" in processed_config:
            ref = processed_config["system_prompt_ref"]
            resolved_content = self._resolve_reference(ref, context)
            if resolved_content:
                processed_config["system_prompt"] = resolved_content
        
        # 处理 user_prompt_ref
        if "user_prompt_ref" in processed_config:
            ref = processed_config["user_prompt_ref"]
            resolved_content = self._resolve_reference(ref, context)
            if resolved_content:
                processed_config["user_input"] = resolved_content
        
        return processed_config
    
    def _process_template_prompts(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理模板化提示词"""
        processed_config = config.copy()
        
        # 处理 system_prompt_template
        if "system_prompt_template" in processed_config:
            template = processed_config["system_prompt_template"]
            rendered_content = self._render_template(template, context)
            if rendered_content:
                processed_config["system_prompt"] = rendered_content
        
        # 处理 user_prompt_template
        if "user_prompt_template" in processed_config:
            template = processed_config["user_prompt_template"]
            rendered_content = self._render_template(template, context)
            if rendered_content:
                processed_config["user_input"] = rendered_content
        
        return processed_config
    
    def _process_composite_prompts(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理组合式提示词"""
        processed_config = config.copy()
        
        # 处理 system_prompt_parts
        if "system_prompt_parts" in processed_config:
            parts = processed_config["system_prompt_parts"]
            if isinstance(parts, list):
                combined_content = ""
                for part in parts:
                    resolved_part = self._resolve_reference(part, context)
                    if resolved_part:
                        combined_content += resolved_part + "\n\n"
                
                if combined_content.strip():
                    processed_config["system_prompt"] = combined_content.strip()
        
        # 处理 prompt_ids
        if "prompt_ids" in processed_config:
            # 这个字段会在后续的提示词服务中处理
            pass
        
        return processed_config
    
    def _process_file_references(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """处理文件引用"""
        processed_config = config.copy()
        
        # 处理 system_prompt_file
        if "system_prompt_file" in processed_config:
            file_path = processed_config["system_prompt_file"]
            file_content = self._load_file_content(file_path, context)
            if file_content:
                processed_config["system_prompt"] = file_content
        
        # 处理 user_prompt_file
        if "user_prompt_file" in processed_config:
            file_path = processed_config["user_prompt_file"]
            file_content = self._load_file_content(file_path, context)
            if file_content:
                processed_config["user_input"] = file_content
        
        return processed_config
    
    def _set_default_cache_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """设置默认缓存配置"""
        processed_config = config.copy()
        
        # 设置默认缓存范围
        if "prompt_cache_scope" not in processed_config:
            processed_config["prompt_cache_scope"] = "state"
        
        # 设置默认缓存TTL
        if "prompt_cache_ttl" not in processed_config:
            processed_config["prompt_cache_ttl"] = 3600
        
        return processed_config
    
    def _resolve_reference(self, ref: str, context: Dict[str, Any]) -> Optional[str]:
        """解析引用"""
        try:
            # 这里应该调用提示词注册表来解析引用
            # 为了简化，我们暂时返回None，实际使用时需要集成提示词系统
            logger.debug(f"解析引用: {ref}")
            return None
        except Exception as e:
            logger.warning(f"解析引用失败: {ref}, 错误: {e}")
            return None
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> Optional[str]:
        """渲染模板"""
        try:
            # 简单的模板渲染，支持 {variable} 格式
            def replace_var(match):
                var_name = match.group(1)
                return str(context.get(var_name, match.group(0)))
            
            # 处理 {variable} 格式
            simple_pattern = re.compile(r'\{([^}]+)\}')
            rendered = simple_pattern.sub(replace_var, template)
            
            return rendered
        except Exception as e:
            logger.warning(f"渲染模板失败: {e}")
            return None
    
    def _load_file_content(self, file_path: str, context: Dict[str, Any]) -> Optional[str]:
        """加载文件内容"""
        try:
            # 构建完整路径
            if not os.path.isabs(file_path):
                # 相对于提示词目录
                full_path = Path("configs/prompts") / file_path
            else:
                full_path = Path(file_path)
            
            # 检查文件是否存在
            if not full_path.exists():
                logger.warning(f"文件不存在: {full_path}")
                return None
            
            # 读取文件内容
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 处理文件内容中的模板变量
            if context:
                content = self._render_template(content, context) or content
            
            return content
            
        except Exception as e:
            logger.warning(f"加载文件内容失败: {file_path}, 错误: {e}")
            return None
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置格式
        
        Args:
            config: 配置字典
            
        Returns:
            验证错误列表
        """
        errors = []
        
        try:
            # 检查缓存范围
            cache_scope = config.get("prompt_cache_scope")
            if cache_scope and cache_scope not in ["state", "thread", "session", "none"]:
                errors.append(f"无效的缓存范围: {cache_scope}")
            
            # 检查缓存TTL
            cache_ttl = config.get("prompt_cache_ttl")
            if cache_ttl is not None and (not isinstance(cache_ttl, int) or cache_ttl < 0):
                errors.append(f"无效的缓存TTL: {cache_ttl}")
            
            # 检查提示词变量
            prompt_variables = config.get("prompt_variables")
            if prompt_variables is not None and not isinstance(prompt_variables, dict):
                errors.append("prompt_variables 必须是字典类型")
            
            # 检查组合式提示词
            system_prompt_parts = config.get("system_prompt_parts")
            if system_prompt_parts is not None and not isinstance(system_prompt_parts, list):
                errors.append("system_prompt_parts 必须是列表类型")
            
            # 检查提示词ID列表
            prompt_ids = config.get("prompt_ids")
            if prompt_ids is not None and not isinstance(prompt_ids, list):
                errors.append("prompt_ids 必须是列表类型")
            
        except Exception as e:
            errors.append(f"配置验证时发生错误: {e}")
        
        return errors
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置Schema"""
        return {
            "type": "object",
            "properties": {
                # 传统方式
                "system_prompt": {
                    "type": "string",
                    "description": "系统提示词（传统方式）"
                },
                "system_prompt_id": {
                    "type": "string",
                    "description": "系统提示词ID（提示词系统）"
                },
                "user_prompt_id": {
                    "type": "string",
                    "description": "用户提示词ID（提示词系统）"
                },
                # 新的配置方式
                "system_prompt_ref": {
                    "type": "string",
                    "description": "系统提示词引用（文件化提示词）"
                },
                "system_prompt_template": {
                    "type": "string",
                    "description": "系统提示词模板（支持变量替换）"
                },
                "system_prompt_parts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "系统提示词组件列表（组合式提示词）"
                },
                "system_prompt_file": {
                    "type": "string",
                    "description": "系统提示词文件路径"
                },
                "user_prompt_ref": {
                    "type": "string",
                    "description": "用户提示词引用"
                },
                "user_prompt_template": {
                    "type": "string",
                    "description": "用户提示词模板"
                },
                "user_prompt_file": {
                    "type": "string",
                    "description": "用户提示词文件路径"
                },
                "prompt_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "提示词ID列表"
                },
                # 变量和缓存
                "prompt_variables": {
                    "type": "object",
                    "description": "提示词变量"
                },
                "prompt_cache_scope": {
                    "type": "string",
                    "enum": ["state", "thread", "session", "none"],
                    "default": "state",
                    "description": "提示词缓存范围"
                },
                "prompt_cache_ttl": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 3600,
                    "description": "提示词缓存TTL（秒）"
                },
                # 其他配置
                "user_input": {
                    "type": "string",
                    "description": "用户输入"
                },
                "temperature": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "default": 0.7,
                    "description": "生成温度"
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4096,
                    "default": 1000,
                    "description": "最大生成令牌数"
                }
            }
        }
    
    def create_example_configs(self) -> Dict[str, Dict[str, Any]]:
        """创建示例配置"""
        return {
            "traditional": {
                "system_prompt": "你是一个智能助手",
                "user_input": "请回答：{{question}}",
                "prompt_variables": {
                    "question": "什么是人工智能？"
                }
            },
            "file_reference": {
                "system_prompt_ref": "system.assistant",
                "user_input": "请分析以下内容：{{content}}",
                "prompt_variables": {
                    "content": "用户输入的内容"
                },
                "prompt_cache_scope": "session",
                "prompt_cache_ttl": 7200
            },
            "template": {
                "system_prompt_template": "你是一个{role}，负责{task}",
                "prompt_variables": {
                    "role": "数据分析师",
                    "task": "数据分析"
                },
                "user_input": "请分析：{{data}}"
            },
            "composite": {
                "system_prompt_parts": [
                    "system.base",
                    "system.assistant_specific",
                    "rules.data_analysis"
                ],
                "prompt_variables": {
                    "analysis_type": "趋势分析"
                }
            },
            "file_based": {
                "system_prompt_file": "system/assistant.md",
                "user_prompt_file": "templates/analysis.md",
                "prompt_variables": {
                    "data_source": "user_input"
                }
            },
            "mixed": {
                "system_prompt_parts": [
                    "system.base",
                    "system.assistant_specific"
                ],
                "user_input_template": "请作为{role}分析：{{content}}",
                "prompt_variables": {
                    "role": "专家",
                    "content": "具体内容"
                },
                "prompt_cache_scope": "thread",
                "prompt_cache_ttl": 1800
            }
        }


# 全局配置处理器实例
_global_processor: Optional[PromptConfigProcessor] = None


def get_prompt_config_processor(config_manager: Optional[ConfigManager] = None) -> PromptConfigProcessor:
    """获取全局提示词配置处理器实例"""
    global _global_processor
    if _global_processor is None:
        _global_processor = PromptConfigProcessor(config_manager)
    return _global_processor


def process_node_config(config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """处理节点配置的便捷函数"""
    processor = get_prompt_config_processor()
    return processor.process_node_config(config, context)


def validate_prompt_config(config: Dict[str, Any]) -> List[str]:
    """验证提示词配置的便捷函数"""
    processor = get_prompt_config_processor()
    return processor.validate_config(config)