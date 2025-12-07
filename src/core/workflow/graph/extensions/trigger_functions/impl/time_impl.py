"""时间触发器实现

提供时间触发器的具体实现逻辑。
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.interfaces.state.workflow import IWorkflowState


class TimeTriggerImplementation:
    """时间触发器实现类
    
    提供时间触发器的评估和执行逻辑，支持间隔时间和特定时间点两种模式。
    """
    
    @staticmethod
    def evaluate(state: IWorkflowState, context: Dict[str, Any]) -> bool:
        """时间触发器评估函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        trigger_config = context.get("trigger_config", {})
        trigger_time = trigger_config.get("trigger_time")
        
        if not trigger_time:
            return False
        
        now = datetime.now()
        
        # 检查是否为间隔时间（秒数）
        if trigger_time.isdigit():
            interval_seconds = int(trigger_time)
            last_triggered = trigger_config.get("last_triggered")
            
            if not last_triggered:
                return True
            
            last_time = datetime.fromisoformat(last_triggered) if isinstance(last_triggered, str) else last_triggered
            return (now - last_time).total_seconds() >= interval_seconds
        else:
            # 解析时间格式 "HH:MM"
            try:
                hour, minute = map(int, trigger_time.split(":"))
                next_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 如果今天的时间已过，则设置为明天
                if next_trigger <= now:
                    next_trigger += timedelta(days=1)
                
                last_triggered = trigger_config.get("last_triggered")
                if not last_triggered:
                    return True
                
                last_time = datetime.fromisoformat(last_triggered) if isinstance(last_triggered, str) else last_triggered
                return now >= next_trigger and now.date() >= last_time.date()
            except (ValueError, AttributeError):
                return False
    
    @staticmethod
    def execute(state: IWorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """时间触发器执行函数
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        trigger_config = context.get("trigger_config", {})
        trigger_time = trigger_config.get("trigger_time")
        
        return {
            "trigger_time": trigger_time,
            "executed_at": datetime.now().isoformat(),
            "message": f"时间触发器执行，触发时间: {trigger_time}"
        }
    
    @staticmethod
    def calculate_next_trigger(trigger_time: str, last_triggered: Optional[datetime] = None) -> Optional[datetime]:
        """计算下一次触发时间
        
        Args:
            trigger_time: 触发时间，格式为 "HH:MM" 或间隔秒数
            last_triggered: 上次触发时间
            
        Returns:
            Optional[datetime]: 下一次触发时间
        """
        now = datetime.now()
        
        # 检查是否为间隔时间（秒数）
        if trigger_time.isdigit():
            interval_seconds = int(trigger_time)
            if last_triggered is None:
                return now + timedelta(seconds=interval_seconds)
            else:
                return last_triggered + timedelta(seconds=interval_seconds)
        else:
            # 解析时间格式 "HH:MM"
            try:
                hour, minute = map(int, trigger_time.split(":"))
                next_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 如果今天的时间已过，则设置为明天
                if next_trigger <= now:
                    next_trigger += timedelta(days=1)
                
                return next_trigger
            except (ValueError, AttributeError):
                # 如果解析失败，设置为1小时后
                return now + timedelta(hours=1)