"""工作流加载器 - 纯加载功能

只负责配置加载，不包含验证、构建、注册等业务逻辑。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from src.core.config.config_manager import ConfigManager
from src.core.workflow.config.config import GraphConfig
from src.core.workflow.workflow import Workflow

logger = logging.getLogger(__name__)


class IWorkflowLoader(ABC):
    """工作流加载器接口"""
    
    @abstractmethod
    def load_from_file(self, config_path: str) -> Workflow:
        """从文件加载工作流"""
        pass
    
    @abstractmethod
    def load_from_dict(self, config_dict: Dict[str, Any]) -> Workflow:
        """从字典加载工作流"""
        pass
    
    @abstractmethod
    def list_available_workflows(self) -> List[str]:
        """列出可用工作流"""
        pass


class WorkflowLoader(IWorkflowLoader):
    """工作流加载器实现 - 纯加载功能
    
    只负责配置加载，不包含验证、构建、注册等业务逻辑。
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化工作流加载器
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager or ConfigManager()
        logger.debug("工作流加载器初始化完成")
    
    def load_from_file(self, config_path: str) -> Workflow:
        """从文件加载工作流
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Workflow: 工作流实例
            
        Raises:
            WorkflowConfigError: 配置错误
        """
        try:
            # 加载配置数据
            config_data = self.config_manager.load_config(config_path)
            
            # 解析为GraphConfig
            config = GraphConfig.from_dict(config_data)
            
            # 创建工作流实例（不编译图）
            workflow = Workflow(config=config)
            
            logger.info(f"成功从文件加载工作流: {config.name}")
            return workflow
            
        except Exception as e:
            logger.error(f"从文件加载工作流失败: {config_path}, 错误: {e}")
            from core.common.exceptions.workflow import WorkflowConfigError
            raise WorkflowConfigError(f"加载配置文件失败: {e}") from e
    
    def load_from_dict(self, config_dict: Dict[str, Any]) -> Workflow:
        """从字典加载工作流
        
        Args:
            config_dict: 配置字典
            
        Returns:
            Workflow: 工作流实例
            
        Raises:
            WorkflowConfigError: 配置错误
        """
        try:
            # 解析为GraphConfig
            config = GraphConfig.from_dict(config_dict)
            
            # 创建工作流实例（不编译图）
            workflow = Workflow(config=config)
            
            logger.info(f"成功从字典加载工作流: {config.name}")
            return workflow
            
        except Exception as e:
            logger.error(f"从字典加载工作流失败: {e}")
            from core.common.exceptions.workflow import WorkflowConfigError
            raise WorkflowConfigError(f"解析配置字典失败: {e}") from e
    
    def list_available_workflows(self) -> List[str]:
        """列出可用工作流
        
        Returns:
            List[str]: 可用工作流路径列表
        """
        try:
            # 扫描配置文件
            config_dir = Path("configs/workflows")
            if config_dir.exists():
                available_workflows = [
                    str(f) for f in config_dir.glob("*.yaml") 
                    if f.name != "_group.yaml"
                ]
                return available_workflows
            return []
            
        except Exception as e:
            logger.error(f"列出可用工作流失败: {e}")
            return []
    
    def get_workflow_info(self, config_path: str) -> Dict[str, Any]:
        """获取工作流基本信息
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 工作流基本信息
        """
        try:
            # 加载配置
            config_data = self.config_manager.load_config(config_path)
            config = GraphConfig.from_dict(config_data)
            
            # 构建基本信息
            info = {
                "name": config.name,
                "description": config.description,
                "version": getattr(config, 'version', '1.0.0'),
                "file_path": config_path,
                "structure": {
                    "node_count": len(config.nodes),
                    "edge_count": len(config.edges),
                    "entry_point": config.entry_point,
                    "nodes": list(config.nodes.keys()),
                    "has_state_schema": hasattr(config, 'state_schema') and config.state_schema is not None
                }
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取工作流信息失败: {config_path}, 错误: {e}")
            return {
                "name": "unknown",
                "error": str(e),
                "file_path": config_path
            }