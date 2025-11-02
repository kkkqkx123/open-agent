"""Hook与Trigger协调机制

协调Hook系统和Trigger系统的执行，避免功能冲突和重复。
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import logging

from .interfaces import IHookManager, HookContext, HookPoint, HookExecutionResult
from ..triggers.base import ITrigger, TriggerEvent, TriggerType
from ..triggers.system import TriggerSystem
from ..state import WorkflowState

logger = logging.getLogger(__name__)


class HookTriggerCoordinator:
    """Hook与Trigger协调器"""
    
    def __init__(
        self, 
        hook_manager: Optional[IHookManager] = None,
        trigger_system: Optional[TriggerSystem] = None
    ) -> None:
        """初始化协调器
        
        Args:
            hook_manager: Hook管理器
            trigger_system: Trigger系统
        """
        self.hook_manager = hook_manager
        self.trigger_system = trigger_system
        self._coordination_rules = self._init_coordination_rules()
        self._execution_history: List[Dict[str, Any]] = []
    
    def _init_coordination_rules(self) -> Dict[str, Any]:
        """初始化协调规则"""
        return {
            # Hook优先级高于Trigger的功能
            "hook_priority_features": {
                "dead_loop_detection",  # Hook的死循环检测优先于Trigger的迭代限制
                "error_recovery",       # Hook的错误恢复优先于Trigger的错误处理
                "performance_monitoring"  # Hook的性能监控优先于Trigger的状态监控
            },
            # Trigger专有功能
            "trigger_only_features": {
                "time_based",           # 基于时间的触发
                "external_events",      # 外部事件触发
                "cross_node_monitoring"  # 跨节点监控
            },
            # 需要协调的功能
            "coordinated_features": {
                "state_monitoring",     # 状态监控
                "metrics_collection"    # 指标收集
            }
        }
    
    def coordinate_node_execution(
        self,
        node_type: str,
        state: WorkflowState,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """协调节点执行
        
        Args:
            node_type: 节点类型
            state: 工作流状态
            config: 节点配置
            
        Returns:
            Dict[str, Any]: 协调结果
        """
        coordination_result = {
            "node_type": node_type,
            "hooks_executed": [],
            "triggers_evaluated": [],
            "conflicts_resolved": [],
            "final_decision": None
        }
        
        # 1. 执行Hook（优先级更高）
        hook_result = None
        if self.hook_manager:
            hook_result = self._execute_hooks_with_coordination(
                node_type, state, config, coordination_result
            )
            if hook_result and not hook_result.should_continue:
                coordination_result["final_decision"] = {
                    "source": "hooks",
                    "action": "interrupt",
                    "reason": "Hook要求中断执行",
                    "next_node": hook_result.force_next_node
                }
                return coordination_result
        
        # 2. 评估Trigger（仅限Trigger专有功能）
        if self.trigger_system:
            trigger_result = self._evaluate_triggers_with_coordination(
                node_type, state, config, coordination_result
            )
            if trigger_result["should_trigger"]:
                coordination_result["final_decision"] = {
                    "source": "triggers",
                    "action": "trigger",
                    "reason": "Trigger条件满足",
                    "events": trigger_result["events"]
                }
        
        # 3. 记录协调历史
        self._record_coordination_history(coordination_result)
        
        return coordination_result
    
    def _execute_hooks_with_coordination(
        self,
        node_type: str,
        state: WorkflowState,
        config: Dict[str, Any],
        coordination_result: Dict[str, Any]
    ) -> HookExecutionResult:
        """执行Hook并协调"""
        if not self.hook_manager:
            return HookExecutionResult(should_continue=True)

        hooks = self.hook_manager.get_hooks_for_node(node_type)

        # 过滤掉与Trigger功能重复的Hook
        filtered_hooks = self._filter_hooks_for_coordination(hooks)

        coordination_result["hooks_executed"] = [hook.hook_type for hook in filtered_hooks]

        # 执行前置Hook
        before_context = HookContext(
            node_type=node_type,
            state=state,
            config=config,
            hook_point=HookPoint.BEFORE_EXECUTE
        )

        before_result = self.hook_manager.execute_hooks(HookPoint.BEFORE_EXECUTE, before_context)

        return before_result
    
    def _evaluate_triggers_with_coordination(
        self,
        node_type: str,
        state: WorkflowState,
        config: Dict[str, Any],
        coordination_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估Trigger并协调"""
        if not self.trigger_system:
            return {"should_trigger": False, "events": []}

        # 只评估Trigger专有功能的触发器
        trigger_types_to_evaluate = [
            TriggerType.TIME,
            TriggerType.EVENT
        ]

        context = {
            "node_type": node_type,
            "config": config,
            "coordination_mode": True
        }

        evaluated_triggers = []
        triggered_events = []

        for trigger_info in self.trigger_system.list_triggers():
            trigger_type = trigger_info["type"]

            # 跳过Hook优先级的功能
            if self._is_hook_priority_feature(trigger_type):
                continue

            # 只评估Trigger专有功能
            if trigger_type in [t.value for t in trigger_types_to_evaluate]:
                trigger = self.trigger_system.get_trigger(trigger_info["id"])
                if trigger and trigger.is_enabled():
                    try:
                        if trigger.evaluate(state, context):
                            event = trigger.execute(state, context)
                            triggered_events.append(event)
                            evaluated_triggers.append(trigger_info["id"])
                    except Exception as e:
                        logger.warning(f"Trigger {trigger_info['id']} 评估失败: {e}")

        coordination_result["triggers_evaluated"] = evaluated_triggers

        return {
            "should_trigger": len(triggered_events) > 0,
            "events": triggered_events
        }
    
    def _filter_hooks_for_coordination(self, hooks: List) -> List:
        """过滤Hook以避免与Trigger功能重复"""
        filtered_hooks = []
        
        for hook in hooks:
            hook_type = hook.hook_type
            
            # 保留Hook专有功能
            if hook_type in [
                "logging",
                "metrics_collection",
                "custom_validation"
            ]:
                filtered_hooks.append(hook)
            
            # 保留Hook优先级更高的功能
            elif hook_type in [
                "dead_loop_detection",
                "error_recovery",
                "performance_monitoring"
            ]:
                filtered_hooks.append(hook)
            
            # 对于协调功能，检查是否需要特殊处理
            elif hook_type in self._coordination_rules["coordinated_features"]:
                # 可以在这里添加特殊的协调逻辑
                filtered_hooks.append(hook)
        
        return filtered_hooks
    
    def _is_hook_priority_feature(self, trigger_type: str) -> bool:
        """检查是否为Hook优先级的功能"""
        hook_priority_mapping = {
            "custom": "dead_loop_detection",  # 自定义触发器可能包含死循环检测
            "state": "performance_monitoring"  # 状态触发器可能与性能监控重叠
        }
        
        return trigger_type in hook_priority_mapping
    
    def _record_coordination_history(self, coordination_result: Dict[str, Any]) -> None:
        """记录协调历史"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "node_type": coordination_result["node_type"],
            "hooks_executed": coordination_result["hooks_executed"],
            "triggers_evaluated": coordination_result["triggers_evaluated"],
            "final_decision": coordination_result["final_decision"]
        }
        
        self._execution_history.append(history_entry)
        
        # 限制历史记录大小
        if len(self._execution_history) > 1000:
            self._execution_history = self._execution_history[-1000:]
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """获取协调统计信息"""
        if not self._execution_history:
            return {"total_executions": 0}
        
        stats = {
            "total_executions": len(self._execution_history),
            "hook_usage": {},
            "trigger_usage": {},
            "conflict_resolutions": 0,
            "coordination_efficiency": 0.0
        }
        
        for entry in self._execution_history:
            # 统计Hook使用情况
            for hook_type in entry["hooks_executed"]:
                if hook_type not in stats["hook_usage"]:
                    stats["hook_usage"][hook_type] = 0
                stats["hook_usage"][hook_type] += 1
            
            # 统计Trigger使用情况
            for trigger_id in entry["triggers_evaluated"]:
                if trigger_id not in stats["trigger_usage"]:
                    stats["trigger_usage"][trigger_id] = 0
                stats["trigger_usage"][trigger_id] += 1
            
            # 统计冲突解决
            if entry["final_decision"] and entry["final_decision"].get("source") == "hooks":
                stats["conflict_resolutions"] += 1
        
        # 计算协调效率
        if stats["total_executions"] > 0:
            stats["coordination_efficiency"] = (
                stats["conflict_resolutions"] / stats["total_executions"]
            )
        
        return stats
    
    def update_coordination_rules(self, new_rules: Dict[str, Any]) -> None:
        """更新协调规则
        
        Args:
            new_rules: 新的协调规则
        """
        self._coordination_rules.update(new_rules)
        logger.info("协调规则已更新")
    
    def add_hook_priority_feature(self, feature_name: str) -> None:
        """添加Hook优先级功能
        
        Args:
            feature_name: 功能名称
        """
        self._coordination_rules["hook_priority_features"].add(feature_name)
        logger.info(f"已添加Hook优先级功能: {feature_name}")
    
    def add_trigger_only_feature(self, feature_name: str) -> None:
        """添加Trigger专有功能
        
        Args:
            feature_name: 功能名称
        """
        self._coordination_rules["trigger_only_features"].add(feature_name)
        logger.info(f"已添加Trigger专有功能: {feature_name}")
    
    def clear_coordination_history(self) -> None:
        """清除协调历史"""
        self._execution_history.clear()
        logger.info("协调历史已清除")