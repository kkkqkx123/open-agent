"""Workflow factory implementation following the new architecture.

This module provides the workflow factory service that creates workflows
from configurations and templates.
"""

from typing import Dict, Any, List, Optional, Type
from src.interfaces.workflow.core import IWorkflow, IWorkflowTemplate
from src.interfaces.workflow.services_core import IWorkflowFactory
from src.core.workflow.workflow import Workflow
from src.core.workflow.templates import get_global_template_registry
from src.core.workflow.orchestration.manager import WorkflowManager
from src.core.workflow.registry.registry import WorkflowRegistry


class WorkflowFactory(IWorkflowFactory):
    """Workflow factory implementation.
    
    This class provides methods to create workflows from various sources
    including configurations, templates, and predefined types.
    """
    
    def __init__(self, registry: WorkflowRegistry):
        """Initialize the workflow factory.
        
        Args:
            registry: Workflow registry service
        """
        self._registry = registry
        self._template_registry: Dict[str, Dict[str, Any]] = {}
        self._workflow_types: Dict[str, Type[IWorkflow]] = {
            "default": Workflow
        }
        self._template_manager = get_global_template_registry()
    
    def create_from_config(self, config: Dict[str, Any]) -> IWorkflow:
        """Create a workflow from a configuration dictionary.
        
        Args:
            config: Workflow configuration
            
        Returns:
            Created workflow instance
        """
        workflow_id = config.get("workflow_id")
        if not workflow_id:
            raise ValueError("workflow_id is required in configuration")
        
        name = config.get("name", workflow_id)
        
        # Create the workflow
        workflow = Workflow(workflow_id, name)
        
        # Configure the workflow
        self._configure_workflow(workflow, config)
        
        return workflow
    
    def create_from_template(self, template_name: str, params: Dict[str, Any]) -> IWorkflow:
        """Create a workflow from a template.
        
        Args:
            template_name: Name of the template to use
            params: Parameters to customize the template
            
        Returns:
            Created workflow instance
        """
        # 首先尝试使用新的模板系统
        template = self._template_manager.get_template(template_name)
        if template:
            # 使用新的模板系统创建工作流
            workflow_name = params.get("name", f"{template_name}_workflow")
            workflow_description = params.get("description", f"Workflow created from {template_name} template")
            return template.create_workflow(workflow_name, workflow_description, params)
        
        # 回退到旧的模板系统
        if template_name not in self._template_registry:
            raise ValueError(f"Template not found: {template_name}")
        
        template_config = self._template_registry[template_name]
        
        # Merge template with parameters
        config = self._merge_template_with_params(template_config, params)
        
        return self.create_from_config(config)
    
    def create_workflow_type(self, workflow_type: str, **kwargs: Any) -> IWorkflow:
        """Create a workflow of a specific type.
        
        Args:
            workflow_type: Type of workflow to create
            **kwargs: Additional arguments for workflow creation
            
        Returns:
            Created workflow instance
        """
        if workflow_type not in self._workflow_types:
            raise ValueError(f"Workflow type not found: {workflow_type}")
        
        workflow_class = self._workflow_types[workflow_type]
        return workflow_class(**kwargs)
    
    def register_template(self, name: str, template: Dict[str, Any]) -> None:
        """Register a workflow template.
        
        Args:
            name: Name of the template
            template: Template configuration
        """
        self._template_registry[name] = template
    
    def register_template_instance(self, template: IWorkflowTemplate) -> None:
        """Register a workflow template instance.
        
        Args:
            template: Template instance
        """
        self._template_manager.register_template(template)
    
    def register_workflow_type(self, name: str, workflow_class: Type[IWorkflow]) -> None:
        """Register a workflow type.
        
        Args:
            name: Name of the workflow type
            workflow_class: Workflow class
        """
        self._workflow_types[name] = workflow_class
    
    def list_templates(self) -> List[str]:
        """List all registered templates.
        
        Returns:
            List of template names
        """
        # 合并新旧模板系统的模板
        old_templates = list(self._template_registry.keys())
        new_templates = self._template_manager.list_templates()
        return list(set(old_templates + new_templates))
    
    def list_workflow_types(self) -> List[str]:
        """List all registered workflow types.
        
        Returns:
            List of workflow type names
        """
        return list(self._workflow_types.keys())
    
    def _configure_workflow(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """Configure a workflow based on the provided configuration.
        
        Args:
            workflow: Workflow to configure
            config: Configuration dictionary
        """
        # Add nodes
        for node_config in config.get("nodes", []):
            workflow.add_node(node_config)
        
        # Add edges
        for edge_config in config.get("edges", []):
            workflow.add_edge(edge_config)
        
        # Set entry point if specified
        if "entry_point" in config:
            workflow.set_entry_point(config["entry_point"])
        
        # Set metadata if specified
        if "metadata" in config:
            workflow.metadata = config["metadata"]
    
    def _merge_template_with_params(self, template: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a template with parameters.
        
        Args:
            template: Template configuration
            params: Parameters to merge
            
        Returns:
            Merged configuration
        """
        # Create a deep copy of the template
        config = template.copy()
        
        # Override with parameters
        for key, value in params.items():
            if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                # Merge dictionaries
                config[key].update(value)
            else:
                # Replace values
                config[key] = value
        
        return config