"""Workflow manager implementation following the new architecture.

This module provides the workflow manager service that handles workflow lifecycle,
execution, and coordination with other services.
"""

from typing import Dict, Any, Optional, List
from src.core.workflow.interfaces import IWorkflow, IWorkflowState
from src.core.workflow.workflow import Workflow
from .orchestrator import WorkflowOrchestrator
from .execution.executor import WorkflowExecutorService
from .registry import WorkflowRegistry


class WorkflowManager:
    """Workflow manager service.
    
    This class provides high-level workflow management capabilities,
    including workflow creation, execution, monitoring, and lifecycle management.
    """
    
    def __init__(
        self,
        orchestrator: WorkflowOrchestrator,
        executor: WorkflowExecutorService,
        registry: WorkflowRegistry
    ):
        """Initialize the workflow manager.
        
        Args:
            orchestrator: Workflow orchestrator service
            executor: Workflow executor service
            registry: Workflow registry service
        """
        self._orchestrator = orchestrator
        self._executor = executor
        self._registry = registry
    
    def create_workflow(self, workflow_id: str, name: str, config: Dict[str, Any]) -> IWorkflow:
        """Create a new workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            name: Human-readable name for the workflow
            config: Workflow configuration
            
        Returns:
            Created workflow instance
        """
        workflow = Workflow(workflow_id, name)
        
        # Configure the workflow based on the provided config
        self._configure_workflow(workflow, config)
        
        # Register the workflow
        self._registry.register_workflow(workflow_id, workflow)
        
        return workflow
    
    def execute_workflow(
        self, 
        workflow_id: str, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """Execute a workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            initial_state: Initial state for the workflow execution
            config: Execution configuration
            
        Returns:
            Final workflow state after execution
        """
        import uuid
        from src.core.workflow.interfaces import ExecutionContext
        from src.core.workflow.states.factory import WorkflowStateFactory
        
        # Get the workflow from registry
        workflow = self._registry.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Create default state if not provided
        if initial_state is None:
            initial_state = WorkflowStateFactory.create_workflow_state(
                workflow_id=workflow_id,
                workflow_name=workflow.name,
                input_text=""
            )
        
        # Create execution context with required parameters
        if config is None:
            config = {}
        
        execution_context = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=str(uuid.uuid4()),
            metadata=config.get("metadata", {}),
            config=config
        )
        
        # Execute the workflow
        return self._executor.execute(workflow, initial_state, execution_context)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow status information
        """
        workflow = self._registry.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": "registered",
            "execution_count": self._executor.get_execution_count(workflow_id)
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows.
        
        Returns:
            List of workflow information
        """
        workflow_ids = self._registry.list_workflows()
        result = []
        for workflow_id in workflow_ids:
            workflow = self._registry.get_workflow(workflow_id)
            if workflow:
                result.append({
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "status": "registered"
                })
        return result
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow.
        
        Args:
            workflow_id: ID of the workflow to delete
            
        Returns:
            True if the workflow was deleted, False if it didn't exist
        """
        return self._registry.unregister_workflow(workflow_id)
    
    def _configure_workflow(self, workflow: Workflow, config: Dict[str, Any]) -> None:
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