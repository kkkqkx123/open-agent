"""事件触发器实现

提供事件触发器的具体实现逻辑。
"""

import re
from typing import Dict, Any, List, Optional

from src.interfaces.state.workflow import IWorkflowState


class EventTriggerImplementation:
    """事件触发器实现类
    
    提供事件触发器的评估和执行逻辑，支持基于事件类型和模式的触发。
    """
    
    @staticmethod
    def evaluate(state: IWorkflowState, context: Dict[str, Any]) -> bool:
        """事件触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = context.get("trigger_config", {})
        event_type = trigger_config.get("event_type")
        event_pattern = trigger_config.get("event_pattern")
        
        if not event_type:
            return False
        
        # 检查上下文中是否有匹配的事件
        events = context.get("events", [])
        
        for event in events:
            if event.get("type") == event_type:
                if event_pattern:
                    # 检查事件内容是否匹配模式
                    event_data = str(event.get("data", ""))
                    if re.search(event_pattern, event_data):
                        return True
                else:
                    # 没有模式，只要事件类型匹配就触发
                    return True
        
        return False
    
    @staticmethod
    def execute(state: IWorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """事件触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        from datetime import datetime
        
        trigger_config = context.get("trigger_config", {})
        event_type = trigger_config.get("event_type")
        event_pattern = trigger_config.get("event_pattern")
        
        # 查找匹配的事件
        matching_events = []
        events = context.get("events", [])
        
        for event in events:
            if event.get("type") == event_type:
                if event_pattern:
                    event_data = str(event.get("data", ""))
                    if re.search(event_pattern, event_data):
                        matching_events.append(event)
                else:
                    matching_events.append(event)
        
        return {
            "event_type": event_type,
            "event_pattern": event_pattern,
            "matching_events": matching_events,
            "executed_at": datetime.now().isoformat(),
            "message": f"事件触发器执行，匹配事件数: {len(matching_events)}"
        }
    
    @staticmethod
    def find_matching_events(event_type: str, events: List[Dict[str, Any]], 
                           event_pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """查找匹配的事件
        
        Args:
            event_type: 事件类型
            events: 事件列表
            event_pattern: 事件模式（可选）
            
        Returns:
            List[Dict[str, Any]]: 匹配的事件列表
        """
        matching_events = []
        
        for event in events:
            if event.get("type") == event_type:
                if event_pattern:
                    event_data = str(event.get("data", ""))
                    if re.search(event_pattern, event_data):
                        matching_events.append(event)
                else:
                    matching_events.append(event)
        
        return matching_events