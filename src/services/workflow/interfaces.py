"""Service layer interfaces for workflow management.

This module defines the interfaces for workflow services in the service layer,
providing contracts for workflow management, execution, and orchestration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from src.core.workflow.interfaces import IWorkflow, IWorkflowState


class IWorkflowManager(ABC):
    """Interface for workflow manager service."""
    
    @abstractmethod
    def create_workflow(self, workflow_id: str, name: str, config: Dict[str, Any]) -> IWorkflow:
        """Create a new workflow."""
        pass
    
    @abstractmethod
    def execute_workflow(
        self, 
        workflow_id: str, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """Execute a workflow."""
        pass
    
    @abstractmethod
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        pass
    
    @abstractmethod
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows."""
        pass
    
    @abstractmethod
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        pass


class IWorkflowFactory(ABC):
    """Interface for workflow factory service."""
    
    @abstractmethod
    def create_from_config(self, config: Dict[str, Any]) -> IWorkflow:
        """Create a workflow from a configuration dictionary."""
        pass
    
    @abstractmethod
    def create_from_template(self, template_name: str, params: Dict[str, Any]) -> IWorkflow:
        """Create a workflow from a template."""
        pass
    
    @abstractmethod
    def create_workflow_type(self, workflow_type: str, **kwargs) -> IWorkflow:
        """Create a workflow of a specific type."""
        pass
    
    @abstractmethod
    def register_template(self, name: str, template: Dict[str, Any]) -> None:
        """Register a workflow template."""
        pass
    
    @abstractmethod
    def register_workflow_type(self, name: str, workflow_class: type) -> None:
        """Register a workflow type."""
        pass
    
    @abstractmethod
    def list_templates(self) -> List[str]:
        """List all registered templates."""
        pass
    
    @abstractmethod
    def list_workflow_types(self) -> List[str]:
        """List all registered workflow types."""
        pass


class IWorkflowExecutor(ABC):
    """Interface for workflow executor service."""
    
    @abstractmethod
    def execute(
        self, 
        workflow: IWorkflow, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """Execute a workflow."""
        pass
    
    @abstractmethod
    async def execute_async(
        self, 
        workflow: IWorkflow, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IWorkflowState:
        """Execute a workflow asynchronously."""
        pass
    
    @abstractmethod
    def execute_stream(
        self, 
        workflow: IWorkflow, 
        initial_state: Optional[IWorkflowState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[IWorkflowState, None]:
        """Execute a workflow with streaming results."""
        pass
    
    @abstractmethod
    def get_execution_count(self, workflow_id: str) -> int:
        """Get the execution count for a workflow."""
        pass


class IWorkflowOrchestrator(ABC):
    """Interface for workflow orchestrator service."""
    
    @abstractmethod
    def orchestrate(
        self, 
        workflows: List[IWorkflow], 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, IWorkflowState]:
        """Orchestrate multiple workflows."""
        pass
    
    @abstractmethod
    async def orchestrate_async(
        self, 
        workflows: List[IWorkflow], 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, IWorkflowState]:
        """Orchestrate multiple workflows asynchronously."""
        pass
    
    @abstractmethod
    def add_workflow_dependency(self, workflow_id: str, depends_on: str) -> None:
        """Add a dependency between workflows."""
        pass
    
    @abstractmethod
    def remove_workflow_dependency(self, workflow_id: str, depends_on: str) -> None:
        """Remove a dependency between workflows."""
        pass
    
    @abstractmethod
    def get_workflow_dependencies(self, workflow_id: str) -> List[str]:
        """Get dependencies for a workflow."""
        pass


class IWorkflowRegistry(ABC):
    """Interface for workflow registry service."""
    
    @abstractmethod
    def register_workflow(self, workflow: IWorkflow) -> None:
        """Register a workflow."""
        pass
    
    @abstractmethod
    def unregister_workflow(self, workflow_id: str) -> bool:
        """Unregister a workflow."""
        pass
    
    @abstractmethod
    def get_workflow(self, workflow_id: str) -> Optional[IWorkflow]:
        """Get a workflow by ID."""
        pass
    
    @abstractmethod
    def list_workflows(self) -> List[IWorkflow]:
        """List all registered workflows."""
        pass
    
    @abstractmethod
    def workflow_exists(self, workflow_id: str) -> bool:
        """Check if a workflow exists."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all registered workflows."""
        pass


class IWorkflowBuilderService(ABC):
    """Interface for workflow builder service."""
    
    @abstractmethod
    def build_workflow(self, config: Dict[str, Any]) -> IWorkflow:
        """Build a workflow from configuration."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate a workflow configuration."""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the configuration schema."""
        pass