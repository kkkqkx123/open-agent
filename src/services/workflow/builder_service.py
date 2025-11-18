"""Workflow builder service implementation following the new architecture.

This module provides the workflow builder service that handles workflow
construction from configurations and validation.
"""

from typing import Dict, Any, List
from src.core.workflow.interfaces import IWorkflow
from src.core.workflow.workflow import Workflow
from src.core.workflow.graph.builder import GraphBuilder
from src.core.workflow.graph.builder.validator import WorkflowConfigValidator
from .interfaces import IWorkflowBuilderService


class WorkflowBuilderService(IWorkflowBuilderService):
    """Workflow builder service implementation.
    
    This class provides methods to build workflows from configurations,
    validate configurations, and manage the building process.
    """
    
    def __init__(self):
        """Initialize the workflow builder service."""
        self._validator = WorkflowConfigValidator()
        self._graph_builder = GraphBuilder()
    
    def build_workflow(self, config: Dict[str, Any]) -> IWorkflow:
        """Build a workflow from configuration.
        
        Args:
            config: Workflow configuration
            
        Returns:
            Built workflow instance
        """
        # Validate the configuration
        errors = self.validate_config(config)
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
        
        # Extract workflow information
        workflow_id = config.get("workflow_id")
        if not workflow_id:
            raise ValueError("workflow_id is required")
        
        name = config.get("name", workflow_id)
        
        # Create the workflow
        workflow = Workflow(workflow_id, name)
        
        # Build the graph
        graph = self._graph_builder.build_graph(config)
        workflow.set_graph(graph)
        
        # Set entry point if specified
        if "entry_point" in config:
            workflow.set_entry_point(config["entry_point"])
        
        # Set metadata if specified
        if "metadata" in config:
            workflow.set_metadata(config["metadata"])
        
        return workflow
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate a workflow configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors
        """
        return self._validator.validate(config)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the configuration schema.
        
        Returns:
            Configuration schema
        """
        return self._validator.get_schema()