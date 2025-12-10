"""注册表自动更新器

基于发现结果自动更新注册表配置。
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import yaml
from src.services.logger.injection import get_logger
from copy import deepcopy

logger = get_logger(__name__)


class RegistryUpdateResult:
    """注册表更新结果"""
    
    def __init__(self):
        """初始化更新结果"""
        self.success = False
        self.updated_registries = []
        self.errors = []
        self.warnings = []
        self.backup_files = []
    
    def add_success(self, registry_name: str) -> None:
        """添加成功更新的注册表
        
        Args:
            registry_name: 注册表名称
        """
        self.updated_registries.append(registry_name)
        self.success = True
    
    def add_error(self, error: str) -> None:
        """添加错误
        
        Args:
            error: 错误信息
        """
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """添加警告
        
        Args:
            warning: 警告信息
        """
        self.warnings.append(warning)
    
    def add_backup_file(self, backup_file: str) -> None:
        """添加备份文件
        
        Args:
            backup_file: 备份文件路径
        """
        self.backup_files.append(backup_file)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取更新摘要
        
        Returns:
            Dict[str, Any]: 更新摘要
        """
        return {
            "success": self.success,
            "updated_registries": self.updated_registries,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "backup_count": len(self.backup_files)
        }


class RegistryUpdater:
    """注册表自动更新器
    
    基于发现结果自动更新注册表配置。
    """
    
    def __init__(self, base_path: str = "configs"):
        """初始化注册表更新器
        
        Args:
            base_path: 基础路径
        """
        self.base_path = Path(base_path)
        self.logger = get_logger(f"{__name__}.RegistryUpdater")
    
    def update_registries(
        self,
        auto_mode: bool = False,
        preview_only: bool = True,
        backup: bool = True
    ) -> RegistryUpdateResult:
        """更新注册表
        
        Args:
            auto_mode: 自动模式，自动应用所有建议
            preview_only: 仅预览，不实际更新
            backup: 是否创建备份
            
        Returns:
            RegistryUpdateResult: 更新结果
        """
        result = RegistryUpdateResult()
        
        try:
            self.logger.info("开始注册表自动更新")
            
            # 1. 发现配置文件 - 这里需要使用新的配置发现逻辑
            discovery_result = self._discover_configs()
            
            # 2. 加载现有注册表
            existing_registries = self._load_existing_registries()
            
            # 3. 生成更新建议
            suggestions = self._suggest_registry_updates(discovery_result, existing_registries)
            
            # 4. 预览更新
            if preview_only:
                self._preview_updates(suggestions, result)
                return result
            
            # 5. 创建备份
            if backup:
                self._create_backups(existing_registries, result)
            
            # 6. 应用更新
            if auto_mode:
                self._apply_updates(suggestions, existing_registries, result)
            else:
                self._interactive_updates(suggestions, existing_registries, result)
            
            self.logger.info("注册表自动更新完成")
            
        except Exception as e:
            error_msg = f"注册表自动更新失败: {e}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    def update_specific_registry(
        self,
        registry_name: str,
        updates: Dict[str, Any],
        backup: bool = True
    ) -> RegistryUpdateResult:
        """更新特定注册表
        
        Args:
            registry_name: 注册表名称
            updates: 更新内容
            backup: 是否创建备份
            
        Returns:
            RegistryUpdateResult: 更新结果
        """
        result = RegistryUpdateResult()
        
        try:
            self.logger.info(f"开始更新注册表: {registry_name}")
            
            # 构建注册表文件路径
            registry_file = self._get_registry_file_path(registry_name)
            if not registry_file:
                result.add_error(f"未知的注册表类型: {registry_name}")
                return result
            
            # 加载现有注册表
            existing_config = self._load_registry_config(registry_file)
            
            # 创建备份
            if backup:
                self._create_backup(registry_file, result)
            
            # 应用更新
            updated_config = self._apply_registry_updates(existing_config, updates)
            
            # 保存更新后的配置
            self._save_registry_config(registry_file, updated_config)
            
            result.add_success(registry_name)
            self.logger.info(f"注册表更新成功: {registry_name}")
            
        except Exception as e:
            error_msg = f"更新注册表 {registry_name} 失败: {e}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    def _discover_configs(self) -> Dict[str, List[Dict[str, Any]]]:
        """发现配置文件
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 发现结果
        """
        from src.infrastructure.config.config_loader import ConfigLoader
        
        loader = ConfigLoader(base_path=Path(self.base_path))
        config_files = loader.get_config_files(recursive=True)
        
        # 按类型分类配置文件
        result = {
            "workflows": [],
            "tools": [],
            "state_machines": [],
            "unknown": []
        }
        
        for file_path in config_files:
            # 推断配置类型
            config_type = self._infer_config_type(file_path)
            
            config_info = {
                "file_path": file_path,
                "name": Path(file_path).stem
            }
            
            if config_type == "workflow":
                result["workflows"].append(config_info)
            elif config_type == "tool":
                result["tools"].append(config_info)
            elif config_type == "state_machine":
                result["state_machines"].append(config_info)
            else:
                result["unknown"].append(config_info)
        
        return result
    
    def _infer_config_type(self, file_path: str) -> str:
        """推断配置类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 配置类型
        """
        # 检查路径中的关键词
        path_lower = file_path.lower()
        
        # 状态机配置优先级最高
        if "state_machine" in path_lower or any(pattern in path_lower for pattern in [
            "state.*machine", "thinking", "deep.*thinking", "ultra.*thinking"
        ]):
            return "state_machine"
        
        # 工作流配置
        if "workflow" in path_lower or any(pattern in path_lower for pattern in [
            "react", "plan", "collaborative", "thinking", "deep", "ultra"
        ]):
            return "workflow"
        
        # 工具配置
        if "tool" in path_lower or any(pattern in path_lower for pattern in [
            "calculator", "fetch", "weather", "database", "search", "hash"
        ]):
            return "tool"
        
        # 默认为未知
        return "unknown"
    
    def _suggest_registry_updates(
        self,
        discovery_result: Dict[str, List[Dict[str, Any]]],
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
        
        discovered_workflows = set(config["name"] for config in discovery_result["workflows"])
        
        # 新发现的工作流
        new_workflows = discovered_workflows - existing_workflows
        for workflow_name in new_workflows:
            workflow_config = next(config for config in discovery_result["workflows"] if config["name"] == workflow_name)
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
        
        discovered_tools = set(config["name"] for config in discovery_result["tools"])
        
        # 新发现的工具
        new_tools = discovered_tools - existing_tools
        for tool_name in new_tools:
            tool_config = next(config for config in discovery_result["tools"] if config["name"] == tool_name)
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
        
        discovered_state_machines = set(config["name"] for config in discovery_result["state_machines"])
        
        # 新发现的状态机
        new_state_machines = discovered_state_machines - existing_state_machines
        for sm_name in new_state_machines:
            sm_config = next(config for config in discovery_result["state_machines"] if config["name"] == sm_name)
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
    
    def _load_existing_registries(self) -> Dict[str, Dict[str, Any]]:
        """加载现有注册表
        
        Returns:
            Dict[str, Dict[str, Any]]: 现有注册表配置
        """
        registries = {}
        
        # 工作流注册表
        workflow_registry_file = self.base_path / "workflows" / "__registry__.yaml"
        if workflow_registry_file.exists():
            registries["workflows"] = self._load_registry_config(workflow_registry_file)
        
        # 工具注册表
        tool_registry_file = self.base_path / "tools" / "__registry__.yaml"
        if tool_registry_file.exists():
            registries["tools"] = self._load_registry_config(tool_registry_file)
        
        # 状态机注册表
        state_machine_registry_file = self.base_path / "workflows" / "state_machine" / "__registry__.yaml"
        if state_machine_registry_file.exists():
            registries["state_machine"] = self._load_registry_config(state_machine_registry_file)
        
        return registries
    
    def _load_registry_config(self, file_path: Path) -> Dict[str, Any]:
        """加载注册表配置
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            # 使用统一配置管理器加载
            from src.core.config.config_manager import get_default_manager
            config_manager = get_default_manager()
            return config_manager.load_config(str(file_path), module_type="registry") or {}
        except Exception as e:
            self.logger.error(f"加载注册表配置失败: {file_path}, 错误: {e}")
            return {}
    
    def _save_registry_config(self, file_path: Path, config: Dict[str, Any]) -> None:
        """保存注册表配置
        
        Args:
            file_path: 文件路径
            config: 配置数据
        """
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            raise Exception(f"保存注册表配置失败: {file_path}, 错误: {e}")
    
    def _preview_updates(self, suggestions: Dict[str, Any], result: RegistryUpdateResult) -> None:
        """预览更新
        
        Args:
            suggestions: 更新建议
            result: 更新结果
        """
        self.logger.info("=== 注册表更新预览 ===")
        
        for registry_type, updates in suggestions.items():
            self.logger.info(f"\n{registry_type.upper()} 注册表:")
            
            # 新条目
            new_entries = updates.get("new_entries", [])
            if new_entries:
                self.logger.info(f"  新增条目 ({len(new_entries)} 个):")
                for entry in new_entries:
                    self.logger.info(f"    - {entry['name']}: {entry['file_path']}")
            
            # 缺失条目
            missing_entries = updates.get("missing_entries", [])
            if missing_entries:
                self.logger.info(f" 缺失条目 ({len(missing_entries)} 个):")
                for entry in missing_entries:
                    self.logger.info(f"    - {entry['name']}: {entry['reason']}")
        
        result.add_warning("这是预览模式，未实际更新文件")
        result.success = True  # 预览总是成功的
    
    def _create_backups(self, registries: Dict[str, Dict[str, Any]], result: RegistryUpdateResult) -> None:
        """创建备份
        
        Args:
            registries: 注册表配置
            result: 更新结果
        """
        backup_dir = self.base_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = self._get_timestamp()
        
        for registry_name, config in registries.items():
            registry_file = self._get_registry_file_path(registry_name)
            if registry_file and registry_file.exists():
                backup_file = backup_dir / f"{registry_name}_registry_{timestamp}.yaml"
                
                try:
                    self._save_registry_config(backup_file, config)
                    result.add_backup_file(str(backup_file))
                    self.logger.info(f"创建备份: {backup_file}")
                except Exception as e:
                    result.add_warning(f"创建备份失败: {backup_file}, 错误: {e}")
    
    def _create_backup(self, file_path: Path, result: RegistryUpdateResult) -> None:
        """创建单个文件备份
        
        Args:
            file_path: 文件路径
            result: 更新结果
        """
        backup_dir = self.base_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = self._get_timestamp()
        backup_file = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        try:
            config = self._load_registry_config(file_path)
            self._save_registry_config(backup_file, config)
            result.add_backup_file(str(backup_file))
            self.logger.info(f"创建备份: {backup_file}")
        except Exception as e:
            result.add_warning(f"创建备份失败: {backup_file}, 错误: {e}")
    
    def _apply_updates(
        self,
        suggestions: Dict[str, Any],
        existing_registries: Dict[str, Dict[str, Any]],
        result: RegistryUpdateResult
    ) -> None:
        """应用更新
        
        Args:
            suggestions: 更新建议
            existing_registries: 现有注册表
            result: 更新结果
        """
        for registry_name, updates in suggestions.items():
            if registry_name not in existing_registries:
                result.add_warning(f"跳过不存在的注册表: {registry_name}")
                continue
            
            try:
                # 获取注册表文件路径
                registry_file = self._get_registry_file_path(registry_name)
                if not registry_file:
                    result.add_error(f"无法确定注册表文件路径: {registry_name}")
                    continue
                
                # 应用更新
                updated_config = self._apply_registry_updates(existing_registries[registry_name], updates)
                
                # 保存更新后的配置
                self._save_registry_config(registry_file, updated_config)
                
                result.add_success(registry_name)
                self.logger.info(f"注册表更新成功: {registry_name}")
                
            except Exception as e:
                error_msg = f"更新注册表 {registry_name} 失败: {e}"
                self.logger.error(error_msg)
                result.add_error(error_msg)
    
    def _interactive_updates(
        self,
        suggestions: Dict[str, Any],
        existing_registries: Dict[str, Dict[str, Any]],
        result: RegistryUpdateResult
    ) -> None:
        """交互式更新
        
        Args:
            suggestions: 更新建议
            existing_registries: 现有注册表
            result: 更新结果
        """
        self.logger.info("交互式更新模式（暂未实现）")
        result.add_warning("交互式更新模式暂未实现，请使用自动模式")
    
    def _apply_registry_updates(self, config: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """应用注册表更新
        
        Args:
            config: 现有配置
            updates: 更新内容
            
        Returns:
            Dict[str, Any]: 更新后的配置
        """
        updated_config = deepcopy(config)
        
        # 处理新条目
        new_entries = updates.get("new_entries", [])
        for entry in new_entries:
            if "workflow_types" in updated_config:
                workflow_types = updated_config["workflow_types"]
                workflow_types[entry["name"]] = entry["suggested_config"]
            elif "tool_types" in updated_config:
                tool_types = updated_config["tool_types"]
                tool_types[entry["name"]] = entry["suggested_config"]
            elif "config_files" in updated_config:
                config_files = updated_config["config_files"]
                config_files[entry["name"]] = entry["suggested_config"]
        
        return updated_config
    
    def _get_registry_file_path(self, registry_name: str) -> Optional[Path]:
        """获取注册表文件路径
        
        Args:
            registry_name: 注册表名称
            
        Returns:
            Optional[Path]: 文件路径
        """
        if registry_name == "workflows":
            return self.base_path / "workflows" / "__registry__.yaml"
        elif registry_name == "tools":
            return self.base_path / "tools" / "__registry__.yaml"
        elif registry_name == "state_machine":
            return self.base_path / "workflows" / "state_machine" / "__registry__.yaml"
        else:
            return None
    
    def _get_timestamp(self) -> str:
        """获取时间戳
        
        Returns:
            str: 时间戳字符串
        """
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
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
            return "src.core.workflow.patterns.react:ReActWorkflow"
        elif "plan" in name_lower:
            return "src.core.workflow.patterns.plan_execute:PlanExecuteWorkflow"
        elif "collaborative" in name_lower:
            return "src.services.workflow.collaborative:CollaborativeWorkflow"
        elif "thinking" in name_lower:
            return "src.core.workflow.state_machine:StateMachineWorkflow"
        else:
            return "src.core.workflow.base:BaseWorkflow"
    
    def _infer_tool_class_path(self, name: str) -> str:
        """推断工具类路径
        
        Args:
            name: 工具名称
            
        Returns:
            str: 类路径
        """
        name_lower = name.lower()
        
        if "calculator" in name_lower:
            return "src.core.tools.types.builtin.calculator:CalculatorTool"
        elif "fetch" in name_lower or "search" in name_lower:
            return "src.core.tools.types.rest:RestTool"
        elif "weather" in name_lower:
            return "src.core.tools.types.rest:RestTool"
        else:
            return "src.core.tools.types.rest:RestTool"