"""配置模板系统实现"""

import logging
import re
from typing import Dict, Any, List, Optional, Union, Set
from abc import ABC, abstractmethod

from src.interfaces.configuration import (
    IConfigurationTemplate,
    ValidationResult
)

logger = logging.getLogger(__name__)


class ConfigurationTemplate(IConfigurationTemplate):
    """配置模板实现"""
    
    def __init__(self, template_name: str, template_content: Dict[str, Any]):
        self._template_name = template_name
        self._template_content = template_content
        self._variables = self._extract_variables()
    
    def get_template_name(self) -> str:
        """获取模板名称"""
        return self._template_name
    
    def get_template_content(self) -> Dict[str, Any]:
        """获取模板内容"""
        return self._template_content.copy()
    
    def render(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """渲染模板"""
        try:
            rendered_content = self._render_dict(self._template_content, variables)
            logger.debug(f"模板 {self._template_name} 渲染完成")
            return rendered_content  # type: ignore
        except Exception as e:
            logger.error(f"渲染模板 {self._template_name} 失败: {e}")
            raise
    
    def validate_template(self) -> ValidationResult:
        """验证模板格式"""
        errors = []
        warnings = []
        
        try:
            # 检查模板内容是否为字典
            if not isinstance(self._template_content, dict):
                errors.append("模板内容必须是字典类型")
                return ValidationResult(False, errors, warnings)
            
            # 检查变量引用
            undefined_vars = self._check_undefined_variables()
            if undefined_vars:
                warnings.append(f"模板中存在未定义的变量: {undefined_vars}")
            
            # 检查循环引用
            circular_refs = self._check_circular_references()
            if circular_refs:
                errors.append(f"模板中存在循环引用: {circular_refs}")
            
        except Exception as e:
            errors.append(f"模板验证异常: {e}")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def _extract_variables(self) -> List[str]:
        """提取模板中的变量"""
        variables: Set[str] = set()
        self._extract_variables_from_dict(self._template_content, variables)
        return list(variables)
    
    def _extract_variables_from_dict(self, obj: Any, variables: Set[str]) -> None:
        """从字典中提取变量"""
        if isinstance(obj, dict):
            for value in obj.values():
                self._extract_variables_from_dict(value, variables)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_variables_from_dict(item, variables)
        elif isinstance(obj, str):
            # 查找变量引用 ${variable_name}
            matches = re.findall(r'\$\{([^}]+)\}', obj)
            variables.update(matches)
    
    def _render_dict(self, obj: Any, variables: Dict[str, Any]) -> Any:
        """渲染字典"""
        if isinstance(obj, dict):
            return {key: self._render_dict(value, variables) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._render_dict(item, variables) for item in obj]
        elif isinstance(obj, str):
            return self._render_string(obj, variables)
        else:
            return obj
    
    def _render_string(self, template_str: str, variables: Dict[str, Any]) -> str:
        """渲染字符串"""
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1)
            if var_name in variables:
                return str(variables[var_name])
            else:
                # 变量未定义，保持原样
                logger.warning(f"变量 {var_name} 未定义，保持原样")
                return str(match.group(0))
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, template_str)
    
    def _check_undefined_variables(self) -> List[str]:
        """检查未定义的变量"""
        # 这里只是简单检查，实际使用时需要根据上下文确定哪些变量是必需的
        return []
    
    def _check_circular_references(self) -> List[str]:
        """检查循环引用"""
        # 简单的循环引用检查
        circular_refs: List[str] = []
        self._check_circular_refs_in_dict(self._template_content, [], circular_refs)
        return circular_refs
    
    def _check_circular_refs_in_dict(self, obj: Any, path: List[str], circular_refs: List[str]) -> None:
        """检查字典中的循环引用"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = path + [key]
                if isinstance(value, str) and '${' in value:
                    # 检查是否引用了路径中的某个键
                    matches = re.findall(r'\$\{([^}]+)\}', value)
                    for match in matches:
                        if match in new_path:
                            circular_refs.append(f"{' -> '.join(new_path)} -> {match}")
                else:
                    self._check_circular_refs_in_dict(value, new_path, circular_refs)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = path + [f"[{i}]"]
                self._check_circular_refs_in_dict(item, new_path, circular_refs)


class TemplateManager:
    """模板管理器"""
    
    def __init__(self) -> None:
        self._templates: Dict[str, IConfigurationTemplate] = {}
        self._template_variables: Dict[str, Dict[str, Any]] = {}
    
    def register_template(self, template: IConfigurationTemplate) -> None:
        """注册模板"""
        template_name = template.get_template_name()
        
        # 验证模板
        validation_result = template.validate_template()
        if not validation_result.is_success():
            error_msg = f"模板 {template_name} 验证失败: {validation_result.errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self._templates[template_name] = template
        logger.debug(f"注册模板: {template_name}")
    
    def unregister_template(self, template_name: str) -> None:
        """注销模板"""
        if template_name in self._templates:
            del self._templates[template_name]
            if template_name in self._template_variables:
                del self._template_variables[template_name]
            logger.debug(f"注销模板: {template_name}")
        else:
            logger.warning(f"模板不存在: {template_name}")
    
    def get_template(self, template_name: str) -> Optional[IConfigurationTemplate]:
        """获取模板"""
        return self._templates.get(template_name)
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """渲染模板"""
        template = self._templates.get(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        # 合并模板变量和传入变量
        merged_variables = self._template_variables.get(template_name, {}).copy()
        merged_variables.update(variables)
        
        return template.render(merged_variables)
    
    def set_template_variables(self, template_name: str, variables: Dict[str, Any]) -> None:
        """设置模板变量"""
        if template_name not in self._templates:
            raise ValueError(f"模板不存在: {template_name}")
        
        self._template_variables[template_name] = variables.copy()
        logger.debug(f"设置模板变量: {template_name}")
    
    def get_template_variables(self, template_name: str) -> Dict[str, Any]:
        """获取模板变量"""
        return self._template_variables.get(template_name, {}).copy()
    
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self._templates.keys())
    
    def validate_all_templates(self) -> Dict[str, ValidationResult]:
        """验证所有模板"""
        results = {}
        for template_name, template in self._templates.items():
            results[template_name] = template.validate_template()
        return results


class PredefinedTemplates:
    """预定义模板集合"""
    
    @staticmethod
    def create_development_template() -> ConfigurationTemplate:
        """创建开发环境模板"""
        template_content = {
            "environment": "development",
            "debug": True,
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "database": {
                "host": "${DB_HOST:localhost}",
                "port": "${DB_PORT:5432}",
                "name": "${DB_NAME:dev_db}",
                "username": "${DB_USER:dev_user}",
                "password": "${DB_PASSWORD:dev_pass}"
            },
            "cache": {
                "type": "memory",
                "ttl": 300
            },
            "services": {
                "state": {
                    "enabled": True,
                    "storage": {
                        "default": "memory"
                    }
                },
                "llm": {
                    "enabled": True,
                    "mock_mode": True
                },
                "workflow": {
                    "enabled": True,
                    "debug_mode": True
                }
            }
        }
        
        return ConfigurationTemplate("development", template_content)
    
    @staticmethod
    def create_production_template() -> ConfigurationTemplate:
        """创建生产环境模板"""
        template_content = {
            "environment": "production",
            "debug": False,
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "/var/log/app.log"
            },
            "database": {
                "host": "${DB_HOST}",
                "port": "${DB_PORT:5432}",
                "name": "${DB_NAME}",
                "username": "${DB_USER}",
                "password": "${DB_PASSWORD}",
                "ssl": True,
                "pool_size": 20
            },
            "cache": {
                "type": "redis",
                "host": "${REDIS_HOST}",
                "port": "${REDIS_PORT:6379}",
                "ttl": 3600
            },
            "services": {
                "state": {
                    "enabled": True,
                    "storage": {
                        "default": "sqlite",
                        "sqlite": {
                            "db_path": "${STATE_DB_PATH:/data/state.db}"
                        }
                    }
                },
                "llm": {
                    "enabled": True,
                    "mock_mode": False
                },
                "workflow": {
                    "enabled": True,
                    "debug_mode": False
                }
            }
        }
        
        return ConfigurationTemplate("production", template_content)
    
    @staticmethod
    def create_testing_template() -> ConfigurationTemplate:
        """创建测试环境模板"""
        template_content = {
            "environment": "testing",
            "debug": True,
            "logging": {
                "level": "WARNING",
                "format": "%(levelname)s - %(message)s"
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db",
                "username": "test_user",
                "password": "test_pass"
            },
            "cache": {
                "type": "memory",
                "ttl": 60
            },
            "services": {
                "state": {
                    "enabled": True,
                    "storage": {
                        "default": "memory"
                    }
                },
                "llm": {
                    "enabled": True,
                    "mock_mode": True
                },
                "workflow": {
                    "enabled": True,
                    "debug_mode": True
                }
            }
        }
        
        return ConfigurationTemplate("testing", template_content)
    
    @staticmethod
    def create_microservice_template() -> ConfigurationTemplate:
        """创建微服务模板"""
        template_content = {
            "environment": "${ENVIRONMENT:development}",
            "service_name": "${SERVICE_NAME}",
            "service_version": "${SERVICE_VERSION:1.0.0}",
            "debug": "${DEBUG:false}",
            "logging": {
                "level": "${LOG_LEVEL:INFO}",
                "format": "%(asctime)s - ${SERVICE_NAME} - %(levelname)s - %(message)s"
            },
            "http": {
                "host": "${HTTP_HOST:0.0.0.0}",
                "port": "${HTTP_PORT:8080}",
                "workers": "${HTTP_WORKERS:1}"
            },
            "discovery": {
                "enabled": "${DISCOVERY_ENABLED:false}",
                "service_url": "${SERVICE_URL}",
                "registry_url": "${REGISTRY_URL}"
            },
            "services": {
                "state": {
                    "enabled": "${STATE_ENABLED:true}",
                    "storage": {
                        "default": "${STATE_STORAGE:memory}"
                    }
                }
            }
        }
        
        return ConfigurationTemplate("microservice", template_content)


class TemplateRenderer:
    """模板渲染器"""
    
    def __init__(self, template_manager: TemplateManager):
        self._template_manager = template_manager
    
    def render_configuration(self, template_name: str, 
                           variables: Optional[Dict[str, Any]] = None,
                           overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """渲染配置"""
        # 渲染模板
        rendered_config = self._template_manager.render_template(
            template_name, 
            variables or {}
        )
        
        # 应用覆盖配置
        if overrides:
            rendered_config = self._merge_config(rendered_config, overrides)
        
        return rendered_config
    
    def _merge_config(self, base_config: Dict[str, Any], 
                     override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result


# 全局模板管理器实例
_global_template_manager: Optional[TemplateManager] = None


def get_global_template_manager() -> TemplateManager:
    """获取全局模板管理器"""
    global _global_template_manager
    if _global_template_manager is None:
        _global_template_manager = TemplateManager()
        # 注册预定义模板
        _register_predefined_templates(_global_template_manager)
    return _global_template_manager


def _register_predefined_templates(manager: TemplateManager) -> None:
    """注册预定义模板"""
    templates = [
        PredefinedTemplates.create_development_template(),
        PredefinedTemplates.create_production_template(),
        PredefinedTemplates.create_testing_template(),
        PredefinedTemplates.create_microservice_template()
    ]
    
    for template in templates:
        try:
            manager.register_template(template)
        except Exception as e:
            logger.error(f"注册预定义模板失败: {e}")


# 便捷函数
def render_template(template_name: str, 
                   variables: Optional[Dict[str, Any]] = None,
                   overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """便捷的模板渲染函数"""
    manager = get_global_template_manager()
    renderer = TemplateRenderer(manager)
    return renderer.render_configuration(template_name, variables, overrides)


def register_template(template: IConfigurationTemplate) -> None:
    """便捷的模板注册函数"""
    manager = get_global_template_manager()
    manager.register_template(template)