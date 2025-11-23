"""工作流选择处理器

负责处理 '#' 触发的工作流选择和自动补全功能
"""

from typing import List, Tuple, Optional, Dict, Any
from .base_command_processor import BaseCommandProcessor
from ...logger import get_tui_silent_logger


class WorkflowSelectorProcessor(BaseCommandProcessor):
    """工作流选择处理器"""
    
    def __init__(self):
        """初始化工作流选择处理器"""
        super().__init__("#")
        self.available_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_cache: List[str] = []
        self._load_default_workflows()
        
        # 更新调试日志记录器
        self.tui_logger = get_tui_silent_logger("workflow_selector_processor")
    
    def _load_default_workflows(self) -> None:
        """加载默认工作流"""
        # 这里可以从配置文件或数据库加载工作流
        # 暂时使用硬编码的示例工作流
        self.available_workflows = {
            "chat": {
                "name": "聊天助手",
                "description": "基础聊天对话工作流",
                "category": "通用"
            },
            "code": {
                "name": "代码生成",
                "description": "代码生成和优化工作流",
                "category": "开发"
            },
            "analysis": {
                "name": "数据分析",
                "description": "数据处理和分析工作流",
                "category": "分析"
            },
            "translation": {
                "name": "文本翻译",
                "description": "多语言翻译工作流",
                "category": "工具"
            },
            "summary": {
                "name": "文档摘要",
                "description": "文档内容摘要工作流",
                "category": "工具"
            },
            "debug": {
                "name": "调试助手",
                "description": "代码调试和问题诊断工作流",
                "category": "开发"
            },
            "review": {
                "name": "代码审查",
                "description": "代码质量审查工作流",
                "category": "开发"
            },
            "test": {
                "name": "测试生成",
                "description": "自动化测试用例生成工作流",
                "category": "开发"
            }
        }
        
        # 更新缓存
        self.workflow_cache = list(self.available_workflows.keys())
        self.workflow_cache.sort()
    
    def is_command(self, input_text: str) -> bool:
        """检查输入是否是工作流选择命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            bool: 是否是工作流选择命令
        """
        result = input_text.startswith("#")
        self.tui_logger.debug_input_handling("is_command", f"Checking if '{input_text}' is a workflow command: {result}")
        return result
    
    def parse_command(self, input_text: str) -> Tuple[str, List[str]]:
        """解析工作流选择命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            Tuple[str, List[str]]: 工作流名称和参数列表
        """
        self.tui_logger.debug_input_handling("parse_command", f"Parsing workflow command: {input_text}")
        command_text = self._remove_trigger_char(input_text)
        result = self._split_command_and_args(command_text)
        self.tui_logger.debug_input_handling("parse_command", f"Parsed workflow command result: {result}")
        return result
    
    def execute_command(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """执行工作流选择命令
        
        Args:
            input_text: 输入文本
            context: 执行上下文
            
        Returns:
            Optional[str]: 执行结果或错误信息
        """
        self.tui_logger.debug_input_handling("execute_command", f"Executing workflow command: {input_text}")
        
        workflow_name, args = self.parse_command(input_text)
        
        if not workflow_name:
            result = self._list_available_workflows()
            self.tui_logger.debug_input_handling("execute_command", f"Listing all workflows, result length: {len(result) if result else 0}")
            return result
        
        # 检查工作流是否存在
        if workflow_name not in self.available_workflows:
            # 尝试模糊匹配
            self.tui_logger.debug_input_handling("execute_command", f"Workflow '{workflow_name}' not found, trying fuzzy match")
            matches = self._find_similar_workflows(workflow_name)
            if matches:
                result = f"未找到工作流 '{workflow_name}'，您是否想要:\n" + \
                       "\n".join([f" #{match}" for match in matches[:5]])
                self.tui_logger.debug_input_handling("execute_command", f"Fuzzy match result: {matches[:5]}")
                return result
            else:
                result = f"未知工作流: {workflow_name}\n可用工作流: {', '.join(self.workflow_cache)}"
                self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
                return result
        
        # 获取工作流信息
        workflow_info = self.available_workflows[workflow_name]
        self.tui_logger.debug_input_handling("execute_command", f"Found workflow: {workflow_name}, info: {workflow_info}")
        
        # 构建结果
        result = f"已选择工作流: {workflow_info['name']} (#{workflow_name})\n"
        result += f"描述: {workflow_info['description']}\n"
        result += f"类别: {workflow_info['category']}"
        
        # 如果有参数，显示参数信息
        if args:
            result += f"\n参数: {' '.join(args)}"
        
        # 返回特殊标识，供上层处理
        final_result = f"SELECT_WORKFLOW:{workflow_name}:{'|'.join(args) if args else ''}"
        self.tui_logger.debug_input_handling("execute_command", f"Final workflow selection result: {final_result}")
        return final_result
    
    def get_suggestions(self, partial_input: str) -> List[str]:
        """获取工作流补全建议
        
        Args:
            partial_input: 部分输入
            
        Returns:
            List[str]: 补全建议列表
        """
        self.tui_logger.debug_input_handling("get_suggestions", f"Getting workflow suggestions for: {partial_input}")
        
        if not self.is_command(partial_input):
            self.tui_logger.debug_input_handling("get_suggestions", "Not a workflow command, returning empty list")
            return []
        
        command_text = self._remove_trigger_char(partial_input)
        
        # 如果没有输入，返回所有工作流
        if not command_text:
            suggestions = [f"#{workflow}" for workflow in self.workflow_cache]
            self.tui_logger.debug_input_handling("get_suggestions", f"Returning all workflows: {len(suggestions)} items")
            return suggestions
        
        # 查找匹配的工作流
        matches = [workflow for workflow in self.workflow_cache
                  if workflow.startswith(command_text)]
        suggestions = [f"#{workflow}" for workflow in matches]
        
        self.tui_logger.debug_input_handling("get_suggestions", f"Returning filtered suggestions: {len(suggestions)} items for prefix '{command_text}'")
        return suggestions
    
    def _list_available_workflows(self) -> str:
        """列出可用工作流
        
        Returns:
            str: 工作流列表
        """
        if not self.available_workflows:
            return "暂无可用工作流"
        
        # 按类别分组
        categories: Dict[str, List[str]] = {}
        for workflow_id, info in self.available_workflows.items():
            category = info.get("category", "其他")
            if category not in categories:
                categories[category] = []
            categories[category].append(f"  #{workflow_id} - {info['name']}: {info['description']}")
        
        # 构建结果
        result = "可用工作流:\n"
        for category, workflows in sorted(categories.items()):
            result += f"\n{category}:\n"
            result += "\n".join(sorted(workflows))
        
        return result
    
    def _find_similar_workflows(self, workflow_name: str, max_results: int = 5) -> List[str]:
        """查找相似的工作流名称
        
        Args:
            workflow_name: 工作流名称
            max_results: 最大结果数量
            
        Returns:
            List[str]: 相似的工作流名称列表
        """
        # 简单的字符串匹配算法
        workflow_name_lower = workflow_name.lower()
        matches = []
        
        for workflow in self.workflow_cache:
            workflow_lower = workflow.lower()
            if workflow_name_lower in workflow_lower or workflow_lower in workflow_name_lower:
                matches.append(workflow)
        
        # 按相似度排序（简单的包含关系）
        matches.sort(key=lambda x: (workflow_name_lower not in x.lower(), len(x)))
        
        return matches[:max_results]
    
    def register_workflow(self, workflow_id: str, name: str, description: str, category: str = "自定义") -> None:
        """注册新的工作流
        
        Args:
            workflow_id: 工作流ID
            name: 工作流名称
            description: 工作流描述
            category: 工作流类别
        """
        self.available_workflows[workflow_id] = {
            "name": name,
            "description": description,
            "category": category
        }
        
        # 更新缓存
        if workflow_id not in self.workflow_cache:
            self.workflow_cache.append(workflow_id)
            self.workflow_cache.sort()
    
    def unregister_workflow(self, workflow_id: str) -> None:
        """注销工作流
        
        Args:
            workflow_id: 工作流ID
        """
        if workflow_id in self.available_workflows:
            del self.available_workflows[workflow_id]
            self.workflow_cache.remove(workflow_id)
    
    def get_command_help(self, command_name: Optional[str] = None) -> str:
        """获取工作流选择命令帮助
        
        Args:
            command_name: 命令名称，None表示显示所有命令
            
        Returns:
            str: 帮助文本
        """
        if command_name:
            if command_name in self.available_workflows:
                info = self.available_workflows[command_name]
                return f"#{command_name}: {info['name']} - {info['description']}"
            else:
                return f"未知工作流: {command_name}"
        
        return """工作流选择命令 (使用 # 触发):
  #workflow_name     - 选择工作流
  #                  - 列出所有可用工作流
  
示例:
  #chat             - 选择聊天助手工作流
  #code             - 选择代码生成工作流
  #analysis         - 选择数据分析工作流
  
使用 Tab 键自动补全工作流名称"""