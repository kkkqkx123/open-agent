"""死循环检测Hook

检测和防止工作流中的死循环。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.hooks import HookPoint, HookContext, HookExecutionResult
from .base import ConfigurableHook

logger = get_logger(__name__)


class DeadLoopDetectionHook(ConfigurableHook):
    """死循环检测Hook
    
    检测和防止工作流中的死循环，通过跟踪节点执行次数和状态变化。
    """
    
    def __init__(self):
        """初始化死循环检测Hook"""
        super().__init__(
            hook_id="dead_loop_detection",
            name="死循环检测Hook",
            description="检测和防止工作流中的死循环，通过跟踪节点执行次数和状态变化",
            version="1.0.0"
        )
        
        # 设置默认配置
        self.set_default_config({
            "max_execution_count": 100,
            "max_state_repeats": 10,
            "enable_state_hashing": True,
            "detection_window": 50
        })
        
        self._execution_counts: Dict[str, int] = {}
        self._state_history: List[str] = []
        self._state_hashes: Dict[str, int] = {}
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点"""
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE]
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """执行前检测死循环"""
        node_type = context.node_type
        if not node_type:
            return HookExecutionResult(should_continue=True)
        
        # 检查执行次数
        current_count = self._execution_counts.get(node_type, 0) + 1
        max_count = self.get_config_value("max_execution_count", 100)
        
        if current_count > max_count:
            logger.warning(f"检测到可能的死循环：节点 {node_type} 执行次数超过限制 ({current_count} > {max_count})")
            return HookExecutionResult(
                should_continue=False,
                force_next_node="error_handler",
                metadata={
                    "dead_loop_detected": True,
                    "node_type": node_type,
                    "execution_count": current_count,
                    "max_count": max_count
                }
            )
        
        # 检查状态重复
        if self.get_config_value("enable_state_hashing", True):
            state_hash = self._calculate_state_hash(context.state)
            if state_hash:
                repeat_count = self._state_hashes.get(state_hash, 0) + 1
                max_repeats = self.get_config_value("max_state_repeats", 10)
                
                if repeat_count > max_repeats:
                    logger.warning(f"检测到可能的死循环：状态重复次数超过限制 ({repeat_count} > {max_repeats})")
                    return HookExecutionResult(
                        should_continue=False,
                        force_next_node="error_handler",
                        metadata={
                            "dead_loop_detected": True,
                            "reason": "state_repeat",
                            "state_hash": state_hash,
                            "repeat_count": repeat_count,
                            "max_repeats": max_repeats
                        }
                    )
                
                self._state_hashes[state_hash] = repeat_count
        
        self._log_execution(HookPoint.BEFORE_EXECUTE)
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """执行后更新统计信息"""
        node_type = context.node_type
        if node_type:
            self._execution_counts[node_type] = self._execution_counts.get(node_type, 0) + 1
        
        # 更新状态历史
        if self.get_config_value("enable_state_hashing", True):
            state_hash = self._calculate_state_hash(context.state)
            if state_hash:
                self._state_history.append(state_hash)
                
                # 限制历史记录长度
                window_size = self.get_config_value("detection_window", 50)
                if len(self._state_history) > window_size:
                    # 移除最旧的记录
                    old_hash = self._state_history.pop(0)
                    self._state_hashes[old_hash] = self._state_hashes.get(old_hash, 1) - 1
                    if self._state_hashes[old_hash] <= 0:
                        del self._state_hashes[old_hash]
        
        self._log_execution(HookPoint.AFTER_EXECUTE)
        return HookExecutionResult(should_continue=True)
    
    def _calculate_state_hash(self, state: Any) -> Optional[str]:
        """计算状态哈希
        
        Args:
            state: 状态对象
            
        Returns:
            Optional[str]: 状态哈希，如果无法计算则返回None
        """
        try:
            import hashlib
            
            if state is None:
                return None
            
            # 尝试获取状态的字符串表示
            if hasattr(state, 'to_dict'):
                state_str = str(state.to_dict())
            elif hasattr(state, '__dict__'):
                state_str = str(state.__dict__)
            else:
                state_str = str(state)
            
            # 计算MD5哈希
            return hashlib.md5(state_str.encode()).hexdigest()[:16]
            
        except Exception as e:
            logger.error(f"计算状态哈希失败: {e}")
            return None
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "execution_counts": self._execution_counts.copy(),
            "state_history_length": len(self._state_history),
            "unique_state_hashes": len(self._state_hashes),
            "most_executed_node": max(self._execution_counts.items(), key=lambda x: x[1])[0] if self._execution_counts else None
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._execution_counts.clear()
        self._state_history.clear()
        self._state_hashes.clear()
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Hook配置"""
        errors = super().validate_config(config)
        
        # 验证max_execution_count
        max_count = config.get("max_execution_count")
        if max_count is not None and (not isinstance(max_count, int) or max_count < 1):
            errors.append("max_execution_count必须是大于0的整数")
        
        # 验证max_state_repeats
        max_repeats = config.get("max_state_repeats")
        if max_repeats is not None and (not isinstance(max_repeats, int) or max_repeats < 1):
            errors.append("max_state_repeats必须是大于0的整数")
        
        # 验证detection_window
        window = config.get("detection_window")
        if window is not None and (not isinstance(window, int) or window < 1):
            errors.append("detection_window必须是大于0的整数")
        
        return errors