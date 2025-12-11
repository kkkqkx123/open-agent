"""工作流模板注册表

提供模板的注册、获取和管理功能。
"""

from typing import Dict, List, Optional, Any
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.templates import IWorkflowTemplate
from src.interfaces.workflow.core import IWorkflow  # noqa: F401
from src.interfaces.workflow.exceptions import WorkflowTemplateError

logger = get_logger(__name__)


class WorkflowTemplateRegistry:
    """工作流模板注册表实现"""
    
    def __init__(self) -> None:
        """初始化模板注册表"""
        self._templates: Dict[str, IWorkflowTemplate] = {}
        self._template_metadata: Dict[str, Dict[str, Any]] = {}
        logger.info("WorkflowTemplateRegistry初始化完成")
    
    def register_template(self, template: IWorkflowTemplate) -> None:
        """注册模板
        
        Args:
            template: 模板实例
        """
        if template is None:
            raise ValueError("模板实例不能为None")
        
        template_name = template.name
        if template_name in self._templates:
            logger.warning(f"模板 '{template_name}' 已存在，将被覆盖")
        
        self._templates[template_name] = template
        
        # 存储模板元数据
        self._template_metadata[template_name] = {
            "name": template_name,
            "description": template.description,
            "category": template.category,
            "version": template.version,
            "parameters": template.get_parameters(),
            "registered_at": "auto_generated"
        }
        
        logger.info(f"注册模板: {template_name}")
    
    def get_template(self, name: str) -> Optional[IWorkflowTemplate]:
        """获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[IWorkflowTemplate]: 模板实例，如果不存在则返回None
        """
        return self._templates.get(name)
    
    def list_templates(self) -> List[str]:
        """列出所有模板
        
        Returns:
            List[str]: 模板名称列表
        """
        return list(self._templates.keys())
    
    def unregister_template(self, name: str) -> bool:
        """注销模板
        
        Args:
            name: 模板名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._templates:
            del self._templates[name]
            if name in self._template_metadata:
                del self._template_metadata[name]
            logger.info(f"注销模板: {name}")
            return True
        return False
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[Dict[str, Any]]: 模板信息
        """
        if name not in self._templates:
            return None
        
        template = self._templates[name]
        metadata = self._template_metadata.get(name, {})
        
        return {
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "version": template.version,
            "parameters": template.get_parameters(),
            "metadata": metadata
        }
    
    def list_templates_info(self) -> List[Dict[str, Any]]:
        """列出所有模板信息

        Returns:
            List[Dict[str, Any]]: 模板信息列表
        """
        return [info for info in (self.get_template_info(name) for name in self.list_templates()) if info is not None]
    
    def validate_template_config(self, template_name: str, config: Dict[str, Any]) -> List[str]:
        """验证模板配置
        
        Args:
            template_name: 模板名称
            config: 配置参数
            
        Returns:
            List[str]: 验证错误列表
        """
        template = self.get_template(template_name)
        if not template:
            return [f"模板不存在: {template_name}"]
        
        return template.validate_parameters(config)
    
    def create_workflow_from_template(self, template_name: str, name: str, 
                                     description: str, config: Dict[str, Any]) -> IWorkflow:
        """使用模板创建工作流
        
        Args:
            template_name: 模板名称
            name: 工作流名称
            description: 工作流描述
            config: 配置参数
            
        Returns:
            IWorkflow: 工作流实例
        """
        template = self.get_template(template_name)
        if not template:
            raise WorkflowTemplateError(f"模板不存在: {template_name}", template_name=template_name)
        
        # 验证参数
        errors = template.validate_parameters(config)
        if errors:
            raise WorkflowTemplateError(
                f"参数验证失败: {'; '.join(errors)}", 
                template_name=template_name
            )
        
        # 创建工作流
        return template.create_workflow(name, description, config)
    
    def search_templates(self, keyword: str) -> List[str]:
        """搜索模板
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[str]: 匹配的模板名称列表
        """
        keyword = keyword.lower()
        matching_templates = []
        
        for name, template in self._templates.items():
            # 搜索名称和描述
            if (keyword in name.lower() or 
                keyword in template.description.lower() or
                keyword in template.category.lower()):
                matching_templates.append(name)
                continue
            
            # 搜索参数描述
            for param in template.get_parameters():
                if ("description" in param and 
                    keyword in param["description"].lower()):
                    matching_templates.append(name)
                    break
        
        return matching_templates
    
    def get_templates_by_category(self, category: str) -> List[str]:
        """根据类别获取模板
        
        Args:
            category: 模板类别
            
        Returns:
            List[str]: 模板名称列表
        """
        category_templates = []
        
        for name, template in self._templates.items():
            if category.lower() in template.category.lower():
                category_templates.append(name)
        
        return category_templates
    
    def clear(self) -> None:
        """清除所有模板"""
        self._templates.clear()
        self._template_metadata.clear()
        logger.info("清除所有模板")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_templates = len(self._templates)
        categories = {}
        
        for name, template in self._templates.items():
            category = template.category
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_templates": total_templates,
            "categories": categories,
            "template_names": self.list_templates()
        }


# 全局模板注册表实例
_global_registry: Optional[WorkflowTemplateRegistry] = None


def get_global_template_registry() -> WorkflowTemplateRegistry:
    """获取全局模板注册表
    
    Returns:
        WorkflowTemplateRegistry: 全局模板注册表
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = WorkflowTemplateRegistry()
        _register_builtin_templates(_global_registry)
    return _global_registry


def _register_builtin_templates(registry: WorkflowTemplateRegistry) -> None:
    """注册内置模板
    
    Args:
        registry: 模板注册表
    """
    try:
        # 延迟导入避免循环依赖
        from .react import ReActWorkflowTemplate, EnhancedReActTemplate
        from .plan_execute import PlanExecuteWorkflowTemplate, CollaborativePlanExecuteTemplate
        
        # 注册ReAct模板
        registry.register_template(ReActWorkflowTemplate())
        registry.register_template(EnhancedReActTemplate())
        
        # 注册Plan-Execute模板
        registry.register_template(PlanExecuteWorkflowTemplate())
        registry.register_template(CollaborativePlanExecuteTemplate())
        
        # 注意：提示词代理模板已移除，因为它们与新的提示词系统架构不兼容
        
        logger.info("内置模板注册完成")
    except Exception as e:
        logger.error(f"注册内置模板失败: {e}")


def register_template(template: IWorkflowTemplate) -> None:
    """注册模板到全局注册表
    
    Args:
        template: 模板实例
    """
    registry = get_global_template_registry()
    registry.register_template(template)


def get_template(name: str) -> Optional[IWorkflowTemplate]:
    """从全局注册表获取模板
    
    Args:
        name: 模板名称
        
    Returns:
        Optional[IWorkflowTemplate]: 模板实例
    """
    registry = get_global_template_registry()
    return registry.get_template(name)


def list_templates() -> List[str]:
    """列出全局注册表中的所有模板
    
    Returns:
        List[str]: 模板名称列表
    """
    registry = get_global_template_registry()
    return registry.list_templates()


def create_workflow_from_template(template_name: str, name: str, 
                                 description: str, config: Dict[str, Any]) -> IWorkflow:
    """使用模板创建工作流
    
    Args:
        template_name: 模板名称
        name: 工作流名称
        description: 工作流描述
        config: 配置参数
        
    Returns:
        IWorkflow: 工作流实例
    """
    registry = get_global_template_registry()
    return registry.create_workflow_from_template(template_name, name, description, config)