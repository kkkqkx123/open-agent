"""触发器函数加载器

从配置文件和代码中加载触发器函数。
"""

from datetime import datetime, timedelta
import re
import yaml
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from src.interfaces.dependency_injection import get_logger

from .registry import TriggerFunctionRegistry, TriggerFunctionConfig
from .config import TriggerCompositionConfig, TriggerFunctionConfigLoader

logger = get_logger(__name__)


class TriggerFunctionLoader:
    """触发器函数加载器
    
    负责从配置文件和代码中加载触发器函数。
    """
    
    def __init__(self, registry: TriggerFunctionRegistry, config_manager: Optional[Any] = None):
        self.registry = registry
        # 如果config_manager为None，使用默认管理器
        if config_manager is None:
            try:
                from src.core.config.config_manager import get_default_manager
                config_manager = get_default_manager()
            except Exception:
                pass
        self.config_manager = config_manager
        self._rest_functions: Dict[str, Callable] = {}
    
    def load_from_config_directory(self, config_dir: str) -> None:
        """从配置目录加载触发器函数
        
        Args:
            config_dir: 配置目录路径
        """
        config_path = Path(config_dir)
        if not config_path.exists():
            logger.warning(f"触发器函数配置目录不存在: {config_dir}")
            return
        
        # 加载触发器函数配置
        trigger_functions_dir = config_path / "trigger_functions"
        if trigger_functions_dir.exists():
            self._load_trigger_functions_from_directory(trigger_functions_dir)
        
        # 加载触发器组合配置
        trigger_compositions_dir = config_path / "trigger_compositions"
        if trigger_compositions_dir.exists():
            self._load_trigger_compositions_from_directory(trigger_compositions_dir)
    
    def _load_trigger_functions_from_directory(self, dir_path: Path) -> None:
        """从目录加载触发器函数配置
        
        Args:
            dir_path: 配置目录路径
        """
        for config_file in dir_path.glob("*.yaml"):
            if config_file.name.startswith("_"):
                continue  # 跳过组配置文件
                
            try:
                # 使用统一配置管理器加载
                if self.config_manager is not None:
                    config_data = self.config_manager.load_config_for_module(
                        str(config_file.relative_to(config_file.parent.parent)),
                        "workflow"
                    )
                else:
                    # 降级到直接加载YAML
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}
                
                self._process_trigger_functions_config(config_data, config_file)
                logger.debug(f"加载触发器函数配置: {config_file}")
                
            except Exception as e:
                logger.error(f"加载触发器函数配置失败 {config_file}: {e}")
    
    def _load_trigger_compositions_from_directory(self, dir_path: Path) -> None:
        """从目录加载触发器组合配置
        
        Args:
            dir_path: 配置目录路径
        """
        for config_file in dir_path.glob("*.yaml"):
            if config_file.name.startswith("_"):
                continue  # 跳过组配置文件
                
            try:
                composition_config = TriggerFunctionConfigLoader.load_from_file(str(config_file))
                self.registry.register_composition(composition_config)
                logger.debug(f"加载触发器组合配置: {config_file}")
                
            except Exception as e:
                logger.error(f"加载触发器组合配置失败 {config_file}: {e}")
    
    def _process_trigger_functions_config(self, config_data: Dict[str, Any], config_file: Path) -> None:
        """处理触发器函数配置
        
        Args:
            config_data: 配置数据
            config_file: 配置文件路径
        """
        trigger_functions = config_data.get("trigger_functions", {})
        category = config_data.get("category", "custom")
        
        for name, func_config in trigger_functions.items():
            # 创建触发器函数配置
            trigger_func_config = TriggerFunctionConfig(
                name=name,
                description=func_config.get("description", ""),
                function_type=func_config.get("function_type", "custom"),
                parameters=func_config.get("parameters", {}),
                implementation=func_config.get("implementation", "config"),
                metadata=func_config.get("metadata", {}),
                dependencies=func_config.get("dependencies", []),
                return_schema=func_config.get("return_schema", {}),
                input_schema=func_config.get("input_schema", {})
            )
            
            # 根据实现方式创建触发器函数
            trigger_function = self._create_trigger_function(name, func_config)
            
            if trigger_function:
                self.registry.register_function(name, trigger_function, trigger_func_config)
    
    def _create_trigger_function(self, name: str, config: Dict[str, Any]) -> Optional[Callable]:
        """根据配置创建触发器函数
        
        Args:
            name: 触发器函数名称
            config: 触发器函数配置
            
        Returns:
            Optional[Callable]: 触发器函数，如果创建失败返回None
        """
        implementation = config.get("implementation", "config")
        
        if implementation == "rest":
            return self._get_rest_function(name)
        elif implementation == "config":
            return self._create_config_based_function(config)
        elif implementation.startswith("custom."):
            # 自定义函数，从模块加载
            module_path = implementation[7:]  # 移除 "custom." 前缀
            return self._load_custom_function(module_path)
        else:
            logger.warning(f"未知的实现方式: {implementation}")
            return None
    
    def _create_config_based_function(self, config: Dict[str, Any]) -> Callable:
        """创建基于配置的触发器函数
        
        Args:
            config: 触发器函数配置
            
        Returns:
            Callable: 触发器函数
        """
        func_type = config.get("function_type", "custom")
        
        if func_type == "evaluate":
            return self._create_evaluate_function(config)
        elif func_type == "execute":
            return self._create_execute_function(config)
        elif func_type == "condition":
            return self._create_condition_function(config)
        elif func_type == "time_check":
            return self._create_time_check_function(config)
        elif func_type == "state_check":
            return self._create_state_check_function(config)
        elif func_type == "event_check":
            return self._create_event_check_function(config)
        else:
            logger.warning(f"未知的配置函数类型: {func_type}")
            return lambda state, context, **kwargs: {}
    
    def _create_evaluate_function(self, config: Dict[str, Any]) -> Callable:
        """创建评估函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 评估函数
        """
        evaluate_type = config.get("evaluate_type", "condition")
        
        if evaluate_type == "condition":
            condition = config.get("condition", "True")
            
            def evaluate_function(state: Dict[str, Any], context: Dict[str, Any]) -> bool:
                try:
                    # 创建安全的执行环境
                    safe_globals = {
                        "__rests__": {
                            "len": len,
                            "str": str,
                            "int": int,
                            "float": float,
                            "bool": bool,
                            "list": list,
                            "dict": dict,
                            "any": any,
                            "all": all,
                            "abs": abs,
                            "min": min,
                            "max": max,
                            "sum": sum,
                        },
                        "state": state,
                        "context": context,
                    }
                    
                    # 执行条件表达式
                    result = eval(condition, safe_globals)
                    return bool(result)
                    
                except Exception:
                    return False
            
            return evaluate_function
        
        elif evaluate_type == "time_interval":
            interval_seconds = config.get("interval_seconds", 60)
            
            def evaluate_function(state: Dict[str, Any], context: Dict[str, Any]) -> bool:
                trigger_config = context.get("trigger_config", {})
                last_triggered = trigger_config.get("last_triggered")
                
                if not last_triggered:
                    return True
                
                last_time = datetime.fromisoformat(last_triggered) if isinstance(last_triggered, str) else last_triggered
                return (datetime.now() - last_time).total_seconds() >= interval_seconds
            
            return evaluate_function
        
        else:
            return lambda state, context: False
    
    def _create_execute_function(self, config: Dict[str, Any]) -> Callable:
        """创建执行函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 执行函数
        """
        execute_type = config.get("execute_type", "simple")
        
        if execute_type == "simple":
            message = config.get("message", "触发器执行")
            
            def execute_function(state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "message": message,
                    "executed_at": datetime.now().isoformat(),
                    "trigger_id": context.get("trigger_id", "unknown")
                }
            
            return execute_function
        
        elif execute_type == "state_summary":
            def execute_function(state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "state_summary": {
                        "messages_count": len(state.get("messages", [])),
                        "tool_results_count": len(state.get("tool_results", [])),
                        "current_step": state.get("current_step", ""),
                        "iteration_count": state.get("iteration_count", 0)
                    },
                    "executed_at": datetime.now().isoformat(),
                    "trigger_id": context.get("trigger_id", "unknown")
                }
            
            return execute_function
        
        else:
            return lambda state, context: {"executed_at": datetime.now().isoformat()}
    
    def _create_condition_function(self, config: Dict[str, Any]) -> Callable:
        """创建条件函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 条件函数
        """
        condition_type = config.get("condition_type", "state_check")
        state_key = config.get("state_key", "")
        expected_value = config.get("expected_value", "")
        
        def condition_function(state: Dict[str, Any], context: Dict[str, Any]) -> bool:
            if condition_type == "state_check":
                return state.get(state_key) == expected_value
            elif condition_type == "threshold":
                threshold = config.get("threshold", 0)
                comparison = config.get("comparison", ">=")
                state_value = state.get(state_key, 0)
                
                try:
                    if comparison == ">=":
                        return state_value >= threshold
                    elif comparison == ">":
                        return state_value > threshold
                    elif comparison == "<=":
                        return state_value <= threshold
                    elif comparison == "<":
                        return state_value < threshold
                    elif comparison == "==":
                        return state_value == threshold
                except (TypeError, ValueError):
                    pass
            
            return False
        
        return condition_function
    
    def _create_time_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建时间检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 时间检查函数
        """
        trigger_time = config.get("trigger_time", "00:00")
        
        def time_check_function(state: Dict[str, Any], context: Dict[str, Any]) -> bool:
            now = datetime.now()
            
            # 检查是否为间隔时间（秒数）
            if trigger_time.isdigit():
                interval_seconds = int(trigger_time)
                trigger_config = context.get("trigger_config", {})
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
                    
                    trigger_config = context.get("trigger_config", {})
                    last_triggered = trigger_config.get("last_triggered")
                    
                    if not last_triggered:
                        return True
                    
                    last_time = datetime.fromisoformat(last_triggered) if isinstance(last_triggered, str) else last_triggered
                    return now >= next_trigger and now.date() >= last_time.date()
                except (ValueError, AttributeError):
                    return False
        
        return time_check_function
    
    def _create_state_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建状态检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 状态检查函数
        """
        condition = config.get("condition", "True")
        
        def state_check_function(state: Dict[str, Any], context: Dict[str, Any]) -> bool:
            try:
                # 创建安全的执行环境
                safe_globals = {
                    "__rests__": {
                        "len": len,
                        "str": str,
                        "int": int,
                        "float": float,
                        "bool": bool,
                        "list": list,
                        "dict": dict,
                        "any": any,
                        "all": all,
                        "abs": abs,
                        "min": min,
                        "max": max,
                        "sum": sum,
                    },
                    "state": state,
                    "context": context,
                }
                
                # 执行条件表达式
                result = eval(condition, safe_globals)
                return bool(result)
                
            except Exception:
                return False
        
        return state_check_function
    
    def _create_event_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建事件检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 事件检查函数
        """
        event_type = config.get("event_type", "")
        event_pattern = config.get("event_pattern", "")
        
        def event_check_function(state: Dict[str, Any], context: Dict[str, Any]) -> bool:
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
        
        return event_check_function
    
    def _get_rest_function(self, name: str) -> Optional[Callable]:
        """获取内置函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 内置函数，如果不存在返回None
        """
        return self._rest_functions.get(name)
    
    def _load_custom_function(self, module_path: str) -> Optional[Callable]:
        """加载自定义函数
        
        Args:
            module_path: 模块路径
            
        Returns:
            Optional[Callable]: 自定义函数，如果加载失败返回None
        """
        try:
            module = importlib.import_module(module_path)
            
            # 查找触发器函数
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and not name.startswith('_'):
                    return obj
            
            logger.warning(f"在模块 {module_path} 中未找到触发器函数")
            return None
            
        except Exception as e:
            logger.error(f"加载自定义函数失败 {module_path}: {e}")
            return None
    
    def register_rest_functions(self, rest_functions: Dict[str, Callable]) -> None:
        """注册内置函数
        
        Args:
            rest_functions: 内置函数字典
        """
        self._rest_functions.update(rest_functions)
        logger.debug(f"注册 {len(rest_functions)} 个内置函数")