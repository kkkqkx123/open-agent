"""路由函数加载器

从配置文件和代码中加载路由函数。
"""

import yaml
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from .registry import RouteFunctionRegistry, RouteFunctionConfig

logger = __import__("logging").getLogger(__name__)


class RouteFunctionLoader:
    """路由函数加载器
    
    负责从配置文件和代码中加载路由函数。
    """
    
    def __init__(self, registry: RouteFunctionRegistry):
        self.registry = registry
        self._builtin_functions: Dict[str, Callable] = {}
    
    def load_from_config_directory(self, config_dir: str) -> None:
        """从配置目录加载路由函数
        
        Args:
            config_dir: 配置目录路径
        """
        config_path = Path(config_dir)
        if not config_path.exists():
            logger.warning(f"路由函数配置目录不存在: {config_dir}")
            return
        
        # 加载路由函数配置
        route_functions_dir = config_path / "route_functions"
        if route_functions_dir.exists():
            self._load_route_functions_from_directory(route_functions_dir)
    
    def _load_route_functions_from_directory(self, dir_path: Path) -> None:
        """从目录加载路由函数配置
        
        Args:
            dir_path: 配置目录路径
        """
        for config_file in dir_path.glob("*.yaml"):
            if config_file.name.startswith("_"):
                continue  # 跳过组配置文件
                
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                self._process_route_functions_config(config_data, config_file)
                logger.debug(f"加载路由函数配置: {config_file}")
                
            except Exception as e:
                logger.error(f"加载路由函数配置失败 {config_file}: {e}")
    
    def _process_route_functions_config(self, config_data: Dict[str, Any], config_file: Path) -> None:
        """处理路由函数配置
        
        Args:
            config_data: 配置数据
            config_file: 配置文件路径
        """
        route_functions = config_data.get("route_functions", {})
        category = config_data.get("category", "general")
        
        for name, func_config in route_functions.items():
            # 创建路由函数配置
            route_config = RouteFunctionConfig(
                name=name,
                description=func_config.get("description", ""),
                parameters=func_config.get("parameters", {}),
                return_values=func_config.get("return_values", []),
                category=category,
                implementation=func_config.get("implementation", "config"),
                metadata=func_config.get("metadata", {})
            )
            
            # 根据实现方式创建路由函数
            route_function = self._create_route_function(name, func_config)
            
            if route_function:
                self.registry.register_route_function(name, route_function, route_config)
    
    def _create_route_function(self, name: str, config: Dict[str, Any]) -> Optional[Callable]:
        """根据配置创建路由函数
        
        Args:
            name: 路由函数名称
            config: 路由函数配置
            
        Returns:
            Optional[Callable]: 路由函数，如果创建失败返回None
        """
        implementation = config.get("implementation", "config")
        
        if implementation == "builtin":
            return self._get_builtin_function(name)
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
        """创建基于配置的路由函数
        
        Args:
            config: 路由函数配置
            
        Returns:
            Callable: 路由函数
        """
        func_type = config.get("type", "state_check")
        
        if func_type == "state_check":
            return self._create_state_check_function(config)
        elif func_type == "message_check":
            return self._create_message_check_function(config)
        elif func_type == "tool_check":
            return self._create_tool_check_function(config)
        elif func_type == "multi_condition":
            return self._create_multi_condition_function(config)
        elif func_type == "message_length_check":
            return self._create_message_length_function(config)
        elif func_type == "tool_type_check":
            return self._create_tool_type_function(config)
        elif func_type == "tool_result_check":
            return self._create_tool_result_function(config)
        elif func_type == "tool_time_check":
            return self._create_tool_time_function(config)
        elif func_type == "tool_error_analysis":
            return self._create_tool_error_analysis_function(config)
        elif func_type == "progress_check":
            return self._create_progress_check_function(config)
        elif func_type == "resource_check":
            return self._create_resource_check_function(config)
        elif func_type == "time_window_check":
            return self._create_time_window_check_function(config)
        elif func_type == "message_type_check":
            return self._create_message_type_function(config)
        elif func_type == "content_analysis":
            return self._create_content_analysis_function(config)
        elif func_type == "urgency_detection":
            return self._create_urgency_detection_function(config)
        else:
            logger.warning(f"未知的配置函数类型: {func_type}")
            return lambda state: "default"
    
    def _create_state_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建状态检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 状态检查函数
        """
        state_key = config.get("state_key", "status")
        value_mapping = config.get("value_mapping", {})
        default_target = config.get("default_route", "default")
        
        def state_check_function(state: Dict[str, Any]) -> str:
            state_value = state.get(state_key)
            result = value_mapping.get(str(state_value), default_target)
            return str(result)
        
        return state_check_function
    
    def _create_message_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建消息检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 消息检查函数
        """
        keywords = config.get("keywords", [])
        case_sensitive = config.get("case_sensitive", False)
        return_true = config.get("return_true", "matched")
        return_false = config.get("return_false", "not_matched")
        message_index = config.get("message_index", -1)
        match_all = config.get("match_all", False)
        
        def message_check_function(state: Dict[str, Any]) -> str:
            messages = state.get("messages", [])
            if not messages:
                return str(return_false)
            
            # 获取指定索引的消息
            msg_index = message_index
            if msg_index < 0:
                msg_index = len(messages) + msg_index
            
            if msg_index < 0 or msg_index >= len(messages):
                return str(return_false)
            
            message = messages[msg_index]
            if hasattr(message, 'content'):
                content = str(getattr(message, 'content', ''))
                if not case_sensitive:
                    content = content.lower()
                    search_keywords = [kw.lower() for kw in keywords]
                else:
                    search_keywords = keywords
                
                if match_all:
                    # 需要匹配所有关键词
                    if all(keyword in content for keyword in search_keywords):
                        return str(return_true)
                else:
                    # 匹配任意关键词
                    if any(keyword in content for keyword in search_keywords):
                        return str(return_true)
            
            return str(return_false)
        
        return message_check_function
    
    def _create_tool_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建工具检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 工具检查函数
        """
        has_tool_calls = config.get("has_tool_calls", True)
        has_tool_results = config.get("has_tool_results", False)
        return_true = config.get("return_true", "continue")
        return_false = config.get("return_false", "end")
        
        def tool_check_function(state: Dict[str, Any]) -> str:
            # 检查工具调用
            if has_tool_calls:
                messages = state.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
                        return str(return_true)
            
            # 检查工具结果
            if has_tool_results:
                tool_results = state.get("tool_results", [])
                if tool_results:
                    return str(return_true)
            
            return str(return_false)
        
        return tool_check_function
    
    def _create_multi_condition_function(self, config: Dict[str, Any]) -> Callable:
        """创建多条件函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 多条件函数
        """
        conditions = config.get("conditions", [])
        default_target = config.get("default_target", "default")
        
        def multi_condition_function(state: Dict[str, Any]) -> str:
            for condition in conditions:
                condition_type = condition.get("type")
                
                if condition_type == "state_check":
                    if self._evaluate_state_condition(state, condition):
                        return str(condition.get("target", default_target))
                
                elif condition_type == "tool_check":
                    if self._evaluate_tool_condition(state, condition):
                        return str(condition.get("target", default_target))
                
                elif condition_type == "message_check":
                    if self._evaluate_message_condition(state, condition):
                        return str(condition.get("target", default_target))
            
            return str(default_target)
        
        return multi_condition_function
    
    def _create_message_length_function(self, config: Dict[str, Any]) -> Callable:
        """创建消息长度检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 消息长度检查函数
        """
        short_threshold = config.get("short_threshold", 50)
        long_threshold = config.get("long_threshold", 500)
        message_index = config.get("message_index", -1)
        
        def message_length_function(state: Dict[str, Any]) -> str:
            messages = state.get("messages", [])
            if not messages:
                return "short"
            
            # 获取指定索引的消息
            msg_index = message_index
            if msg_index < 0:
                msg_index = len(messages) + msg_index
            
            if msg_index < 0 or msg_index >= len(messages):
                return "short"
            
            message = messages[msg_index]
            if hasattr(message, 'content'):
                content = str(getattr(message, 'content', ''))
                length = len(content)
                
                if length <= short_threshold:
                    return "short"
                elif length >= long_threshold:
                    return "long"
                else:
                    return "medium"
            
            return "short"
        
        return message_length_function
    
    def _create_tool_type_function(self, config: Dict[str, Any]) -> Callable:
        """创建工具类型检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 工具类型检查函数
        """
        type_mapping = config.get("type_mapping", {})
        default_route = config.get("default_route", "default_handler")
        
        def tool_type_function(state: Dict[str, Any]) -> str:
            messages = state.get("messages", [])
            if not messages:
                return str(default_route)
            
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
                tool_calls = getattr(last_message, 'tool_calls', [])
                if tool_calls:
                    tool_name = tool_calls[0].get("name", "")
                    result = type_mapping.get(tool_name, default_route)
                    return str(result)
            
            return str(default_route)
        
        return tool_type_function
    
    def _create_tool_result_function(self, config: Dict[str, Any]) -> Callable:
        """创建工具结果检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 工具结果检查函数
        """
        check_success = config.get("check_success", True)
        check_error = config.get("check_error", True)
        
        def tool_result_function(state: Dict[str, Any]) -> str:
            tool_results = state.get("tool_results", [])
            if not tool_results:
                return "no_results"
            
            has_success = False
            has_error = False
            
            for result in tool_results:
                if isinstance(result, dict):
                    if check_success and result.get("success", True):
                        has_success = True
                    if check_error and not result.get("success", True):
                        has_error = True
            
            if has_error:
                return "error"
            elif has_success:
                return "success"
            else:
                return "partial"
        
        return tool_result_function
    
    def _create_tool_time_function(self, config: Dict[str, Any]) -> Callable:
        """创建工具执行时间检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 工具执行时间检查函数
        """
        time_threshold = config.get("time_threshold", 30.0)
        comparison = config.get("comparison", "greater_than")
        
        def tool_time_function(state: Dict[str, Any]) -> str:
            tool_results = state.get("tool_results", [])
            if not tool_results:
                return "no_tools"
            
            # 检查最后一个工具结果的执行时间
            last_result = tool_results[-1]
            if isinstance(last_result, dict):
                execution_time = last_result.get("execution_time", 0)
                
                if comparison == "greater_than":
                    return "slow" if execution_time > time_threshold else "fast"
                elif comparison == "less_than":
                    return "fast" if execution_time < time_threshold else "slow"
            
            return "no_tools"
        
        return tool_time_function
    
    def _create_tool_error_analysis_function(self, config: Dict[str, Any]) -> Callable:
        """创建工具错误分析函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 工具错误分析函数
        """
        error_types = config.get("error_types", ["timeout", "permission", "not_found", "syntax"])
        default_route = config.get("default_route", "unknown_error")
        
        def tool_error_analysis_function(state: Dict[str, Any]) -> str:
            tool_results = state.get("tool_results", [])
            if not tool_results:
                return "no_error"
            
            # 检查是否有错误
            for result in tool_results:
                if isinstance(result, dict) and not result.get("success", True):
                    error_message = result.get("error", "").lower()
                    
                    for error_type in error_types:
                        if error_type in error_message:
                            return error_type
            
            return "no_error"
        
        return tool_error_analysis_function
    
    def _create_progress_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建进度检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 进度检查函数
        """
        progress_key = config.get("progress_key", "progress")
        completion_threshold = config.get("completion_threshold", 1.0)
        stages = config.get("stages", [0.25, 0.5, 0.75, 1.0])
        
        def progress_check_function(state: Dict[str, Any]) -> str:
            progress = state.get(progress_key, 0.0)
            
            if progress >= completion_threshold:
                return "complete"
            elif progress >= stages[2]:
                return "late"
            elif progress >= stages[1]:
                return "middle"
            elif progress >= stages[0]:
                return "early"
            else:
                return "initial"
        
        return progress_check_function
    
    def _create_resource_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建资源检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 资源检查函数
        """
        resource_type = config.get("resource_type", "memory")
        usage_threshold = config.get("usage_threshold", 0.8)
        comparison = config.get("comparison", "greater_than")
        
        def resource_check_function(state: Dict[str, Any]) -> str:
            resource_key = f"{resource_type}_usage"
            usage = state.get(resource_key, 0.0)
            
            if comparison == "greater_than":
                return "high_usage" if usage > usage_threshold else "normal_usage"
            elif comparison == "less_than":
                return "normal_usage" if usage < usage_threshold else "high_usage"
            
            return "unknown"
        
        return resource_check_function
    
    def _create_time_window_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建时间窗口检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 时间窗口检查函数
        """
        start_time_key = config.get("start_time_key", "start_time")
        window_duration = config.get("window_duration", 300)
        current_time_key = config.get("current_time_key", "current_time")
        
        def time_window_check_function(state: Dict[str, Any]) -> str:
            import time
            
            start_time = state.get(start_time_key)
            current_time = state.get(current_time_key, time.time())
            
            if not start_time:
                return "no_time_data"
            
            elapsed = current_time - start_time
            return "within_window" if elapsed <= window_duration else "outside_window"
        
        return time_window_check_function
    
    def _create_message_type_function(self, config: Dict[str, Any]) -> Callable:
        """创建消息类型检查函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 消息类型检查函数
        """
        type_mapping = config.get("type_mapping", {
            "human": "human_handler",
            "ai": "ai_handler",
            "system": "system_handler",
            "tool": "tool_handler"
        })
        default_route = config.get("default_route", "default_handler")
        message_index = config.get("message_index", -1)
        
        def message_type_function(state: Dict[str, Any]) -> str:
            messages = state.get("messages", [])
            if not messages:
                return default_route
            
            # 获取指定索引的消息
            msg_index = message_index
            if msg_index < 0:
                msg_index = len(messages) + msg_index
            
            if msg_index < 0 or msg_index >= len(messages):
                return default_route
            
            message = messages[msg_index]
            message_type = getattr(message, 'type', 'unknown')
            
            return type_mapping.get(message_type, default_route)
        
        return message_type_function
    
    def _create_content_analysis_function(self, config: Dict[str, Any]) -> Callable:
        """创建内容分析函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 内容分析函数
        """
        analysis_type = config.get("analysis_type", "language")
        language_mapping = config.get("language_mapping", {
            "zh": "chinese_handler",
            "en": "english_handler",
            "ja": "japanese_handler",
            "unknown": "default_handler"
        })
        format_mapping = config.get("format_mapping", {
            "json": "json_handler",
            "xml": "xml_handler",
            "text": "text_handler",
            "unknown": "default_handler"
        })
        message_index = config.get("message_index", -1)
        
        def content_analysis_function(state: Dict[str, Any]) -> str:
            messages = state.get("messages", [])
            if not messages:
                return "default_handler"
            
            # 获取指定索引的消息
            msg_index = message_index
            if msg_index < 0:
                msg_index = len(messages) + msg_index
            
            if msg_index < 0 or msg_index >= len(messages):
                return "default_handler"
            
            message = messages[msg_index]
            if not hasattr(message, 'content'):
                return "default_handler"
            
            content = str(getattr(message, 'content', ''))
            
            if analysis_type == "language":
                # 简单的语言检测
                if any(ord(char) > 127 for char in content):
                    return language_mapping.get("zh", "default_handler")
                else:
                    return language_mapping.get("en", "default_handler")
            elif analysis_type == "format":
                # 格式检测
                content = content.strip()
                if content.startswith("{") and content.endswith("}"):
                    return format_mapping.get("json", "default_handler")
                elif content.startswith("<") and content.endswith(">"):
                    return format_mapping.get("xml", "default_handler")
                else:
                    return format_mapping.get("text", "default_handler")
            
            return "default_handler"
        
        return content_analysis_function
    
    def _create_urgency_detection_function(self, config: Dict[str, Any]) -> Callable:
        """创建紧急程度检测函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 紧急程度检测函数
        """
        urgency_keywords = config.get("urgency_keywords", ["urgent", "emergency", "asap", "immediately", "紧急", "立即", "马上"])
        high_priority_keywords = config.get("high_priority_keywords", ["high", "priority", "important", "重要", "优先"])
        case_sensitive = config.get("case_sensitive", False)
        
        def urgency_detection_function(state: Dict[str, Any]) -> str:
            messages = state.get("messages", [])
            if not messages:
                return "normal"
            
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                content = str(getattr(last_message, 'content', ''))
                if not case_sensitive:
                    content_lower = content.lower()
                    urgency_keywords_lower = [kw.lower() for kw in urgency_keywords]
                    high_priority_keywords_lower = [kw.lower() for kw in high_priority_keywords]
                else:
                    content_lower = content
                    urgency_keywords_lower = urgency_keywords
                    high_priority_keywords_lower = high_priority_keywords
                
                # 检查紧急关键词
                if any(keyword in content_lower for keyword in urgency_keywords_lower):
                    return "urgent"
                
                # 检查高优先级关键词
                if any(keyword in content_lower for keyword in high_priority_keywords_lower):
                    return "high_priority"
            
            return "normal"
        
        return urgency_detection_function
    
    def _evaluate_state_condition(self, state: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """评估状态条件
        
        Args:
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        state_key = condition.get("state_key")
        operator = condition.get("operator", "==")
        value = condition.get("value")
        
        if not state_key:
            return False
        
        state_value = state.get(state_key)
        return self._evaluate_condition(state_value, operator, value)
    
    def _evaluate_tool_condition(self, state: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """评估工具条件
        
        Args:
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        has_tool_calls = condition.get("has_tool_calls", False)
        
        if has_tool_calls:
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
                    return True
        
        return False
    
    def _evaluate_message_condition(self, state: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """评估消息条件
        
        Args:
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        keywords = condition.get("message_contains", [])
        if not keywords:
            return False
        
        messages = state.get("messages", [])
        if not messages:
            return False
        
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            content = str(getattr(last_message, 'content', '')).lower()
            return any(keyword.lower() in content for keyword in keywords)
        
        return False
    
    def _evaluate_condition(self, left_value: Any, operator: str, right_value: Any) -> bool:
        """评估条件
        
        Args:
            left_value: 左值
            operator: 操作符
            right_value: 右值
            
        Returns:
            bool: 条件是否满足
        """
        try:
            if operator == "==":
                return left_value == right_value
            elif operator == "!=":
                return left_value != right_value
            elif operator == ">":
                return left_value > right_value
            elif operator == ">=":
                return left_value >= right_value
            elif operator == "<":
                return left_value < right_value
            elif operator == "<=":
                return left_value <= right_value
            elif operator == "in":
                return left_value in right_value
            elif operator == "not_in":
                return left_value not in right_value
            else:
                return False
        except Exception:
            return False
    
    def _get_builtin_function(self, name: str) -> Optional[Callable]:
        """获取内置函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 内置函数，如果不存在返回None
        """
        return self._builtin_functions.get(name)
    
    def _load_custom_function(self, module_path: str) -> Optional[Callable]:
        """加载自定义函数
        
        Args:
            module_path: 模块路径
            
        Returns:
            Optional[Callable]: 自定义函数，如果加载失败返回None
        """
        try:
            module = importlib.import_module(module_path)
            
            # 查找路由函数
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and not name.startswith('_'):
                    return obj
            
            logger.warning(f"在模块 {module_path} 中未找到路由函数")
            return None
            
        except Exception as e:
            logger.error(f"加载自定义函数失败 {module_path}: {e}")
            return None
    
    def register_builtin_functions(self, builtin_functions: Dict[str, Callable]) -> None:
        """注册内置函数
        
        Args:
            builtin_functions: 内置函数字典
        """
        self._builtin_functions.update(builtin_functions)
        logger.debug(f"注册 {len(builtin_functions)} 个内置函数")