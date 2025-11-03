"""
Sequential Thinking Tool Implementation

Provides a tool for dynamic and reflective problem-solving through a structured thinking process.
Supports tracking, revising, and branching of thought steps.
"""

import json
from typing import Dict, Any, List, Optional
import os


class ThoughtData:
    """Thought Data Class"""
    
    def __init__(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        next_thought_needed: bool,
        is_revision: Optional[bool] = None,
        revises_thought: Optional[int] = None,
        branch_from_thought: Optional[int] = None,
        branch_id: Optional[str] = None,
        needs_more_thoughts: Optional[bool] = None
    ):
        self.thought = thought
        self.thought_number = thought_number
        self.total_thoughts = total_thoughts
        self.next_thought_needed = next_thought_needed
        self.is_revision = is_revision
        self.revises_thought = revises_thought
        self.branch_from_thought = branch_from_thought
        self.branch_id = branch_id
        self.needs_more_thoughts = needs_more_thoughts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "thought": self.thought,
            "thoughtNumber": self.thought_number,
            "totalThoughts": self.total_thoughts,
            "nextThoughtNeeded": self.next_thought_needed,
            "isRevision": self.is_revision,
            "revisesThought": self.revises_thought,
            "branchFromThought": self.branch_from_thought,
            "branchId": self.branch_id,
            "needsMoreThoughts": self.needs_more_thoughts
        }


class SequentialThinkingServer:
    """Sequential Thinking Server Class"""
    
    def __init__(self):
        self.thought_history: List[ThoughtData] = []
        self.branches: Dict[str, List[ThoughtData]] = {}
        self.disable_thought_logging = os.environ.get("DISABLE_THOUGHT_LOGGING", "").lower() == "true"
    
    def validate_thought_data(self, input_data: Dict[str, Any]) -> ThoughtData:
        """Validate thought data"""
        if not input_data.get("thought") or not isinstance(input_data["thought"], str):
            raise ValueError("Invalid thought: must be a string")
        
        if not input_data.get("thoughtNumber") or not isinstance(input_data["thoughtNumber"], int):
            raise ValueError("Invalid thoughtNumber: must be a number")
        
        if not input_data.get("totalThoughts") or not isinstance(input_data["totalThoughts"], int):
            raise ValueError("Invalid totalThoughts: must be a number")
        
        if not isinstance(input_data.get("nextThoughtNeeded"), bool):
            raise ValueError("Invalid nextThoughtNeeded: must be a boolean")
        
        return ThoughtData(
            thought=input_data["thought"],
            thought_number=input_data["thoughtNumber"],
            total_thoughts=input_data["totalThoughts"],
            next_thought_needed=input_data["nextThoughtNeeded"],
            is_revision=input_data.get("isRevision"),
            revises_thought=input_data.get("revisesThought"),
            branch_from_thought=input_data.get("branchFromThought"),
            branch_id=input_data.get("branchId"),
            needs_more_thoughts=input_data.get("needsMoreThoughts")
        )
    
    def format_thought(self, thought_data: ThoughtData) -> str:
        """Format thought output"""
        prefix = ""
        context = ""
        
        if thought_data.is_revision:
            prefix = "🔄 Revision"
            context = f" (revising thought {thought_data.revises_thought})" if thought_data.revises_thought is not None else ""
        elif thought_data.branch_from_thought:
            prefix = "🌿 Branch"
            context = f" (from thought {thought_data.branch_from_thought}, ID: {thought_data.branch_id})" if thought_data.branch_id is not None else ""
        else:
            prefix = "💭 Thought"
            context = ""
        
        header = f"{prefix} {thought_data.thought_number}/{thought_data.total_thoughts}{context}"
        border = "─" * (max(len(header), len(thought_data.thought)) + 4)
        
        return f"""
┌{border}┐
│ {header} │
├{border}┤
│ {thought_data.thought.ljust(len(border) - 2)} │
└{border}┘"""
    
    def process_thought(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process thought data"""
        try:
            validated_input = self.validate_thought_data(input_data)
            
            # If thought number exceeds total thoughts, automatically adjust total thoughts
            if validated_input.thought_number > validated_input.total_thoughts:
                validated_input.total_thoughts = validated_input.thought_number
            
            # Add to thought history
            self.thought_history.append(validated_input)
            
            # Handle branching
            if validated_input.branch_from_thought and validated_input.branch_id:
                if validated_input.branch_id not in self.branches:
                    self.branches[validated_input.branch_id] = []
                self.branches[validated_input.branch_id].append(validated_input)
            
            # Output formatted thought (if logging is not disabled)
            if not self.disable_thought_logging:
                formatted_thought = self.format_thought(validated_input)
                print(formatted_thought, flush=True)
            
            return {
                "thoughtNumber": validated_input.thought_number,
                "totalThoughts": validated_input.total_thoughts,
                "nextThoughtNeeded": validated_input.next_thought_needed,
                "branches": list(self.branches.keys()),
                "thoughtHistoryLength": len(self.thought_history)
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }


# Global server instance
_thinking_server = SequentialThinkingServer()


def sequentialthinking(
    thought: str,
    nextThoughtNeeded: bool,
    thoughtNumber: int,
    totalThoughts: int,
    isRevision: Optional[bool] = None,
    revisesThought: Optional[int] = None,
    branchFromThought: Optional[int] = None,
    branchId: Optional[str] = None,
    needsMoreThoughts: Optional[bool] = None
) -> Dict[str, Any]:
    """Sequential thinking tool main function
    
    Args:
        thought: Current thinking step
        nextThoughtNeeded: Whether more thinking steps are needed
        thoughtNumber: Current thought number
        totalThoughts: Estimated total thoughts
        isRevision: Whether revising previous thoughts
        revisesThought: The thought number being revised
        branchFromThought: Branch starting thought number
        branchId: Branch identifier
        needsMoreThoughts: Whether more thoughts are needed
        
    Returns:
        Dict[str, Any]: Dictionary containing processing results
        
    Raises:
        ValueError: Raised when input parameters are invalid
    """
    input_data = {
        "thought": thought,
        "nextThoughtNeeded": nextThoughtNeeded,
        "thoughtNumber": thoughtNumber,
        "totalThoughts": totalThoughts,
        "isRevision": isRevision,
        "revisesThought": revisesThought,
        "branchFromThought": branchFromThought,
        "branchId": branchId,
        "needsMoreThoughts": needsMoreThoughts
    }
    
    result = _thinking_server.process_thought(input_data)
    
    if "error" in result:
        raise ValueError(result["error"])
    
    return result


# Example usage
if __name__ == "__main__":
    # Test sequential thinking tool
    print("Testing sequential thinking tool:")
    
    # First thought
    try:
        result1 = sequentialthinking(
            thought="Analyze the core requirements of the problem",
            nextThoughtNeeded=True,
            thoughtNumber=1,
            totalThoughts=3
        )
        print(f"Result 1: {json.dumps(result1, indent=2, ensure_ascii=False)}")
    except ValueError as e:
        print(f"Error: {e}")
    
    # Second thought
    try:
        result2 = sequentialthinking(
            thought="Determine the technical path for the solution",
            nextThoughtNeeded=True,
            thoughtNumber=2,
            totalThoughts=3
        )
        print(f"Result 2: {json.dumps(result2, indent=2, ensure_ascii=False)}")
    except ValueError as e:
        print(f"Error: {e}")
    
    # Third thought (complete)
    try:
        result3 = sequentialthinking(
            thought="Develop implementation plan and verification scheme",
            nextThoughtNeeded=False,
            thoughtNumber=3,
            totalThoughts=3
        )
        print(f"Result 3: {json.dumps(result3, indent=2, ensure_ascii=False)}")
    except ValueError as e:
        print(f"Error: {e}")