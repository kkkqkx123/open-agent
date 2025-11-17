"""配置发现器

扫描指定目录自动发现配置文件，根据文件模式推断配置类型。
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class ConfigDiscoveryResult:
    """配置发现结果"""
    
    def __init__(self):
        """初始化发现结果"""
        self.workflows: List[Dict[str, Any]] = []
        self.tools: List[Dict[str, Any]] = []
        self.state_machines: List[Dict[str, Any]] = []
        self.unknown: List[Dict[str, Any]] = []
    
    def add_workflow(self, file_path: str, config_type: str = "workflow") -> None:
        """添加工作流配置
        
        Args:
            file_path: 文件路径
            config_type: 配置类型
        """
        self.workflows.append({
            "file_path": file_path,
            "config_type": config_type,
            "name": Path(file_path).stem
        })
    
    def add_tool(self, file_path: str, config_type: str = "tool") -> None:
        """添加工具配置
        
        Args:
            file_path: 文件路径
            config_type: 配置类型
        """
        self.tools.append({
            "file_path": file_path,
            "config_type": config_type,
            "name": Path(file_path).stem
        })
    
    def add_state_machine(self, file_path: str, config_type: str = "state_machine") -> None:
        """添加状态机配置
        
        Args:
            file_path: 文件路径
            config_type: 配置类型
        """
        self.state_machines.append({
            "file_path": file_path,
            "config_type": config_type,
            "name": Path(file_path).stem
        })
    
    def add_unknown(self, file_path: str) -> None:
        """添加未知配置
        
        Args:
            file_path: 文件路径
        """
        self.unknown.append({
            "file_path": file_path,
            "name": Path(file_path).stem
        })
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有配置
        
        Returns:
            List[Dict[str, Any]]: 所有配置列表
        """
        return self.workflows + self.tools + self.state_machines + self.unknown
    
    def get_summary(self) -> Dict[str, int]:
        """获取发现摘要
        
        Returns:
            Dict[str, int]: 发现摘要
        """
        return {
            "workflows": len(self.workflows),
            "tools": len(self.tools),
            "state_machines": len(self.state_machines),
            "unknown": len(self.unknown),
            "total": len(self.get_all_configs())
        }


class ConfigDiscoverer:
    """配置发现器
    
    扫描指定目录自动发现配置文件，根据文件模式推断配置类型。
    """
    
    def __init__(self, base_path: str = "configs"):
        """初始化配置发现器
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(f"{__name__}.ConfigDiscoverer")
        
        # 文件模式映射
        self.workflow_patterns = [
            r".*workflow.*\.ya?ml$",
            r".*react.*\.ya?ml$",
            r".*plan.*\.ya?ml$",
            r".*collaborative.*\.ya?ml$",
            r".*thinking.*\.ya?ml$",
            r".*deep.*\.ya?ml$",
            r".*ultra.*\.ya?ml$"
        ]
        
        self.tool_patterns = [
            r".*tool.*\.ya?ml$",
            r".*calculator.*\.ya?ml$",
            r".*fetch.*\.ya?ml$",
            r".*weather.*\.ya?ml$",
            r".*database.*\.ya?ml$",
            r".*search.*\.ya?ml$",
            r".*hash.*\.ya?ml$"
        ]
        
        self.state_machine_patterns = [
            r".*state.*machine.*\.ya?ml$",
            r".*thinking.*\.ya?ml$",
            r".*deep.*thinking.*\.ya?ml$",
            r".*ultra.*thinking.*\.ya?ml$"
        ]
        
        # 默认排除模式
        self.default_exclude_patterns = [
            r"^__.*",
            r"^_.*",
            r"^test_.*",
            r".*test.*\.ya?ml$",
            r".*example.*\.ya?ml$"
        ]
    
    def discover_configs(
        self,
        scan_directories: Optional[List[str]] = None,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> ConfigDiscoveryResult:
        """发现配置文件
        
        Args:
            scan_directories: 扫描目录列表
            file_patterns: 文件模式列表
            exclude_patterns: 排除模式列表
            
        Returns:
            ConfigDiscoveryResult: 发现结果
        """
        result = ConfigDiscoveryResult()
        
        # 使用默认扫描目录
        if not scan_directories:
            scan_directories = ["workflows", "tools", "workflows/state_machine"]
        
        # 使用默认文件模式
        if not file_patterns:
            file_patterns = [r".*\.ya?ml$"]
        
        # 使用默认排除模式
        if not exclude_patterns:
            exclude_patterns = self.default_exclude_patterns
        
        # 编译正则表达式
        compiled_file_patterns = [re.compile(pattern) for pattern in file_patterns]
        compiled_exclude_patterns = [re.compile(pattern) for pattern in exclude_patterns]
        compiled_workflow_patterns = [re.compile(pattern) for pattern in self.workflow_patterns]
        compiled_tool_patterns = [re.compile(pattern) for pattern in self.tool_patterns]
        compiled_state_machine_patterns = [re.compile(pattern) for pattern in self.state_machine_patterns]
        
        # 扫描目录
        for scan_dir in scan_directories:
            scan_path = self.base_path / scan_dir
            if not scan_path.exists():
                self.logger.warning(f"扫描目录不存在: {scan_path}")
                continue
            
            self.logger.info(f"扫描目录: {scan_path}")
            
            # 递归扫描文件
            for file_path in scan_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # 检查文件模式
                if not self._matches_patterns(file_path.name, compiled_file_patterns):
                    continue
                
                # 检查排除模式
                if self._matches_patterns(file_path.name, compiled_exclude_patterns):
                    self.logger.debug(f"排除文件: {file_path}")
                    continue
                
                # 获取相对路径
                relative_path = file_path.relative_to(self.base_path)
                relative_path_str = str(relative_path).replace("\\", "/")
                
                # 推断配置类型
                config_type = self._infer_config_type(
                    relative_path_str,
                    compiled_workflow_patterns,
                    compiled_tool_patterns,
                    compiled_state_machine_patterns
                )
                
                # 添加到结果
                if config_type == "workflow":
                    result.add_workflow(relative_path_str)
                elif config_type == "tool":
                    result.add_tool(relative_path_str)
                elif config_type == "state_machine":
                    result.add_state_machine(relative_path_str)
                else:
                    result.add_unknown(relative_path_str)
        
        # 记录发现结果
        summary = result.get_summary()
        self.logger.info(f"配置发现完成: {summary}")
        
        return result
    
    def suggest_registry_updates(
        self,
        discovery_result: ConfigDiscoveryResult,
        existing_registries: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """建议注册表更新
        
        Args:
            discovery_result: 发现结果
            existing_registries: 现有注册表配置
            
        Returns:
            Dict[str, Any]: 更新建议
        """
        if not existing_registries:
            existing_registries = {}
        
        suggestions = {
            "workflows": {
                "new_entries": [],
                "missing_entries": []
            },
            "tools": {
                "new_entries": [],
                "missing_entries": []
            },
            "state_machines": {
                "new_entries": [],
                "missing_entries": []
            }
        }
        
        # 分析工作流配置
        existing_workflows = set()
        if "workflows" in existing_registries:
            workflow_types = existing_registries["workflows"].get("workflow_types", {})
            existing_workflows = set(workflow_types.keys())
        
        discovered_workflows = set(config["name"] for config in discovery_result.workflows)
        
        # 新发现的工作流
        new_workflows = discovered_workflows - existing_workflows
        for workflow_name in new_workflows:
            workflow_config = next(config for config in discovery_result.workflows if config["name"] == workflow_name)
            suggestions["workflows"]["new_entries"].append({
                "name": workflow_name,
                "file_path": workflow_config["file_path"],
                "suggested_config": self._generate_workflow_suggestion(workflow_config)
            })
        
        # 缺失的工作流
        missing_workflows = existing_workflows - discovered_workflows
        for workflow_name in missing_workflows:
            suggestions["workflows"]["missing_entries"].append({
                "name": workflow_name,
                "reason": "配置文件未找到"
            })
        
        # 分析工具配置
        existing_tools = set()
        if "tools" in existing_registries:
            tool_types = existing_registries["tools"].get("tool_types", {})
            existing_tools = set(tool_types.keys())
        
        discovered_tools = set(config["name"] for config in discovery_result.tools)
        
        # 新发现的工具
        new_tools = discovered_tools - existing_tools
        for tool_name in new_tools:
            tool_config = next(config for config in discovery_result.tools if config["name"] == tool_name)
            suggestions["tools"]["new_entries"].append({
                "name": tool_name,
                "file_path": tool_config["file_path"],
                "suggested_config": self._generate_tool_suggestion(tool_config)
            })
        
        # 缺失的工具
        missing_tools = existing_tools - discovered_tools
        for tool_name in missing_tools:
            suggestions["tools"]["missing_entries"].append({
                "name": tool_name,
                "reason": "配置文件未找到"
            })
        
        # 分析状态机配置
        existing_state_machines = set()
        if "state_machine" in existing_registries:
            state_machine_configs = existing_registries["state_machine"].get("config_files", {})
            existing_state_machines = set(state_machine_configs.keys())
        
        discovered_state_machines = set(config["name"] for config in discovery_result.state_machines)
        
        # 新发现的状态机
        new_state_machines = discovered_state_machines - existing_state_machines
        for sm_name in new_state_machines:
            sm_config = next(config for config in discovery_result.state_machines if config["name"] == sm_name)
            suggestions["state_machines"]["new_entries"].append({
                "name": sm_name,
                "file_path": sm_config["file_path"],
                "suggested_config": self._generate_state_machine_suggestion(sm_config)
            })
        
        # 缺失的状态机
        missing_state_machines = existing_state_machines - discovered_state_machines
        for sm_name in missing_state_machines:
            suggestions["state_machines"]["missing_entries"].append({
                "name": sm_name,
                "reason": "配置文件未找到"
            })
        
        return suggestions
    
    def _matches_patterns(self, text: str, patterns: List[re.Pattern]) -> bool:
        """检查文本是否匹配任何模式
        
        Args:
            text: 文本
            patterns: 模式列表
            
        Returns:
            bool: 是否匹配
        """
        return any(pattern.search(text) for pattern in patterns)
    
    def _infer_config_type(
        self,
        file_path: str,
        workflow_patterns: List[re.Pattern],
        tool_patterns: List[re.Pattern],
        state_machine_patterns: List[re.Pattern]
    ) -> str:
        """推断配置类型
        
        Args:
            file_path: 文件路径
            workflow_patterns: 工作流模式
            tool_patterns: 工具模式
            state_machine_patterns: 状态机模式
            
        Returns:
            str: 配置类型
        """
        # 检查路径中的关键词
        path_lower = file_path.lower()
        
        # 状态机配置优先级最高
        if "state_machine" in path_lower or self._matches_patterns(file_path, state_machine_patterns):
            return "state_machine"
        
        # 工作流配置
        if "workflow" in path_lower or self._matches_patterns(file_path, workflow_patterns):
            return "workflow"
        
        # 工具配置
        if "tool" in path_lower or self._matches_patterns(file_path, tool_patterns):
            return "tool"
        
        # 默认为未知
        return "unknown"
    
    def _generate_workflow_suggestion(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """生成工作流配置建议
        
        Args:
            config: 配置信息
            
        Returns:
            Dict[str, Any]: 建议配置
        """
        name = config["name"]
        file_path = config["file_path"]
        
        # 根据名称推断类路径
        class_path = self._infer_workflow_class_path(name)
        
        return {
            "class_path": class_path,
            "description": f"{name} 工作流",
            "enabled": True,
            "config_files": [file_path]
        }
    
    def _generate_tool_suggestion(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """生成工具配置建议
        
        Args:
            config: 配置信息
            
        Returns:
            Dict[str, Any]: 建议配置
        """
        name = config["name"]
        file_path = config["file_path"]
        
        # 根据名称推断类路径
        class_path = self._infer_tool_class_path(name)
        
        return {
            "class_path": class_path,
            "description": f"{name} 工具",
            "enabled": True,
            "config_files": [file_path]
        }
    
    def _generate_state_machine_suggestion(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """生成状态机配置建议
        
        Args:
            config: 配置信息
            
        Returns:
            Dict[str, Any]: 建议配置
        """
        name = config["name"]
        file_path = config["file_path"]
        
        return {
            "file_path": file_path,
            "description": f"{name} 状态机工作流",
            "enabled": True
        }
    
    def _infer_workflow_class_path(self, name: str) -> str:
        """推断工作流类路径
        
        Args:
            name: 工作流名称
            
        Returns:
            str: 类路径
        """
        name_lower = name.lower()
        
        if "react" in name_lower:
            return "src.application.workflow.factory:ReActWorkflow"
        elif "plan" in name_lower:
            return "src.application.workflow.factory:PlanExecuteWorkflow"
        elif "collaborative" in name_lower:
            return "src.application.workflow.collaborative:CollaborativeWorkflow"
        elif "thinking" in name_lower:
            return "src.application.workflow.state_machine.state_machine_workflow:StateMachineWorkflow"
        else:
            return "src.application.workflow.factory:BaseWorkflow"
    
    def _infer_tool_class_path(self, name: str) -> str:
        """推断工具类路径
        
        Args:
            name: 工具名称
            
        Returns:
            str: 类路径
        """
        name_lower = name.lower()
        
        if "calculator" in name_lower:
            return "src.domain.tools.types.rest_tool:SyncRestTool"
        elif "fetch" in name_lower or "search" in name_lower:
            return "src.domain.tools.types.rest_tool:RestTool"
        elif "weather" in name_lower:
            return "src.domain.tools.types.rest_tool:RestTool"
        else:
            return "src.domain.tools.types.rest_tool:RestTool"