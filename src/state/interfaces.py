"""State interfaces module.

This module defines the core state interfaces for the application following the new architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


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
    def update_data(self, updates: Dict[str, Any]) -> None:
        """Update multiple data entries in the state.
        
        Args:
            updates: Dictionary of key-value pairs to update
        """
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