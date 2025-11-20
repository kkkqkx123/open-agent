"""State interfaces module.

This module defines the core state interfaces for the application following the new architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime


class IState(ABC):
    """State interface defining the contract for state objects in the system.
    
    This interface provides a common contract that all state implementations
    must adhere to, allowing for consistent state management across different
    components and modules.
    """
    
    @abstractmethod
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the state by key.
        
        Args:
            key: The key to retrieve data for
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or default if not found
        """
        pass
    
    @abstractmethod
    def set_data(self, key: str, value: Any) -> None:
        """Set data in the state.
        
        Args:
            key: The key to set
            value: The value to associate with the key
        """
        pass
    
    @abstractmethod
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the state by key.
        
        Args:
            key: The key to retrieve metadata for
            default: Default value to return if key is not found
            
        Returns:
            The metadata value associated with the key, or default if not found
        """
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata in the state.
        
        Args:
            key: The key to set
            value: The metadata value to associate with the key
        """
        pass
    
    @abstractmethod
    def get_id(self) -> Optional[str]:
        """Get the state ID.
        
        Returns:
            The state ID, or None if not set
        """
        pass
    
    @abstractmethod
    def set_id(self, id: str) -> None:
        """Set the state ID.
        
        Args:
            id: The ID to set
        """
        pass
    
    @abstractmethod
    def get_created_at(self) -> datetime:
        """Get the creation timestamp.
        
        Returns:
            The creation timestamp
        """
        pass
    
    @abstractmethod
    def get_updated_at(self) -> datetime:
        """Get the last update timestamp.
        
        Returns:
            The last update timestamp
        """
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """Check if the state is complete.
        
        Returns:
            True if complete, False otherwise
        """
        pass
    
    @abstractmethod
    def mark_complete(self) -> None:
        """Mark the state as complete."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the state to a dictionary representation.
        
        Returns:
            Dictionary representation of the state
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IState':
        """Create a state instance from a dictionary.
        
        Args:
            data: Dictionary representation of the state
            
        Returns:
            New instance of the state
        """
        pass


class IWorkflowState(IState):
    """Interface for workflow state objects.
    
    Extends the base state interface with workflow-specific methods
    and properties.
    """
    
    @abstractmethod
    def get_messages(self) -> List[Any]:
        """Get the list of messages in the workflow state.
        
        Returns:
            List of messages
        """
        pass
    
    @abstractmethod
    def add_message(self, message: Any) -> None:
        """Add a message to the workflow state.
        
        Args:
            message: The message to add
        """
        pass
    
    @abstractmethod
    def get_last_message(self) -> Optional[Any]:
        """Get the last message in the workflow state.
        
        Returns:
            The last message, or None if no messages
        """
        pass
    
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the state.
        
        Args:
            key: The key to retrieve
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or default if not found
        """
        pass
    
    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """Set a value in the state.
        
        Args:
            key: The key to set
            value: The value to associate with the key
        """
        pass
    
    @abstractmethod
    def get_current_node(self) -> Optional[str]:
        """Get the current node in the workflow.
        
        Returns:
            The current node name, or None if not set
        """
        pass
    
    @abstractmethod
    def set_current_node(self, node: str) -> None:
        """Set the current node in the workflow.
        
        Args:
            node: The node name to set
        """
        pass
    
    @abstractmethod
    def get_iteration_count(self) -> int:
        """Get the current iteration count.
        
        Returns:
            The current iteration count
        """
        pass
    
    @abstractmethod
    def increment_iteration(self) -> None:
        """Increment the iteration count."""
        pass
    
    @abstractmethod
    def get_thread_id(self) -> Optional[str]:
        """Get the thread ID.
        
        Returns:
            The thread ID, or None if not set
        """
        pass
    
    @abstractmethod
    def set_thread_id(self, thread_id: str) -> None:
        """Set the thread ID.
        
        Args:
            thread_id: The thread ID to set
        """
        pass
    
    @abstractmethod
    def get_session_id(self) -> Optional[str]:
        """Get the session ID.
        
        Returns:
            The session ID, or None if not set
        """
        pass
    
    @abstractmethod
    def set_session_id(self, session_id: str) -> None:
        """Set the session ID.
        
        Args:
            session_id: The session ID to set
        """
        pass


class IStateManager(ABC):
    """Interface for state managers.
    
    Defines the contract for state management implementations,
    providing CRUD operations and lifecycle management.
    """
    
    @abstractmethod
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> IState:
        """Create a new state.
        
        Args:
            state_id: Unique identifier for the state
            initial_state: Initial state data
            
        Returns:
            The created state instance
        """
        pass
    
    @abstractmethod
    def get_state(self, state_id: str) -> Optional[IState]:
        """Get state by ID.
        
        Args:
            state_id: Unique identifier for the state
            
        Returns:
            The state instance, or None if not found
        """
        pass
    
    @abstractmethod
    def update_state(self, state_id: str, updates: Dict[str, Any]) -> IState:
        """Update state.
        
        Args:
            state_id: Unique identifier for the state
            updates: Dictionary of updates to apply
            
        Returns:
            The updated state instance
        """
        pass
    
    @abstractmethod
    def delete_state(self, state_id: str) -> bool:
        """Delete state.
        
        Args:
            state_id: Unique identifier for the state
            
        Returns:
            True if state was deleted, False if not found
        """
        pass
    
    @abstractmethod
    def list_states(self) -> List[str]:
        """List all state IDs.
        
        Returns:
            List of state IDs
        """
        pass


class IStateSerializer(ABC):
    """Interface for state serializers.
    
    Defines the contract for state serialization and deserialization
    implementations.
    """
    
    @abstractmethod
    def serialize(self, state: IState) -> Union[str, bytes]:
        """Serialize state to a string or bytes.
        
        Args:
            state: The state to serialize
            
        Returns:
            Serialized state data
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: Union[str, bytes]) -> IState:
        """Deserialize state from string or bytes.
        
        Args:
            data: The serialized state data
            
        Returns:
            The deserialized state instance
        """
        pass


class IStateFactory(ABC):
    """Interface for state factories.
    
    Defines the contract for state creation implementations.
    """
    
    @abstractmethod
    def create_workflow_state(self, **kwargs: Any) -> IWorkflowState:
        """Create a workflow state.
        
        Args:
            **kwargs: Arguments for state creation
            
        Returns:
            The created workflow state
        """
        pass
    
    @abstractmethod
    def create_state_from_type(self, state_type: str, **kwargs: Any) -> IState:
        """Create a state of the specified type.
        
        Args:
            state_type: The type of state to create
            **kwargs: Arguments for state creation
            
        Returns:
            The created state
        """
        pass


class IStateLifecycleManager(ABC):
    """Interface for state lifecycle managers.
    
    Defines the contract for state lifecycle management implementations.
    """
    
    @abstractmethod
    def initialize_state(self, state: IState) -> None:
        """Initialize a state.
        
        Args:
            state: The state to initialize
        """
        pass
    
    @abstractmethod
    def cleanup_state(self, state: IState) -> None:
        """Clean up a state.
        
        Args:
            state: The state to clean up
        """
        pass
    
    @abstractmethod
    def validate_state(self, state: IState) -> List[str]:
        """Validate a state.
        
        Args:
            state: The state to validate
            
        Returns:
            List of validation errors, empty if valid
        """
        pass