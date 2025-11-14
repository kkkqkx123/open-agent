"""工作流配置管理器

专注于工作流配置的加载、验证和管理，不涉及执行逻辑
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime
import uuid
import hashlib

from ...infrastructure.config.loader.yaml_loader import IConfigLoader
from ...infrastructure.graph.config import WorkflowConfig
from .interfaces import IWorkflowConfigManager

logger = logging.getLogger(__name__)


class WorkflowConfigManager(IWorkflowConfigManager):
    """工作流配置管理器实现
    
    专注于：
    - 工作流配置加载和解析
    - 配置验证和校验
    - 配置元数据管理
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None):
        """初始化配置管理器
        
        Args:
            config_loader: 配置加载器
        """
        self.config_loader = config_loader
        self._configs: Dict[str, WorkflowConfig] = {}
        self._config_metadata: Dict[str, Dict[str, Any]] = {}
    
    def load_config(self, config_path: str) -> str:
        """加载工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            str: 配置ID
            
        Raises:
            ValueError: 配置文件无效
            RuntimeError: 配置加载失败
        """
        try:
            # 验证文件路径
            if not Path(config_path).exists():
                raise ValueError(f"配置文件不存在: {config_path}")
            
            # 加载配置
            if self.config_loader:
                config_dict = self.config_loader.load(config_path)
                config = WorkflowConfig.from_dict(config_dict)
            else:
                # 简化实现，实际应该使用依赖注入的config_loader
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
                config = WorkflowConfig.from_dict(config_dict)
            
            # 生成配置ID
            config_id = self._generate_config_id(config.name, config_path)
            
            # 存储配置
            self._configs[config_id] = config
            self._config_metadata[config_id] = {
                "config_id": config_id,
                "name": config.name,
                "description": config.description,
                "version": config.version,
                "config_path": config_path,
                "loaded_at": datetime.now().isoformat(),
                "checksum": self._calculate_checksum(config_path)
            }
            
            logger.info(f"工作流配置加载成功: {config_id}")
            return config_id
            
        except Exception as e:
            logger.error(f"加载工作流配置失败: {config_path}, error: {e}")
            raise RuntimeError(f"配置加载失败: {str(e)}")
    
    def get_config(self, config_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            Optional[WorkflowConfig]: 工作流配置
        """
        return self._configs.get(config_id)
    
    def validate_config(self, config: WorkflowConfig) -> bool:
        """验证工作流配置
        
        Args:
            config: 工作流配置
            
        Returns:
            bool: 验证结果
        """
        try:
            # 基本验证
            if not config.name:
                logger.error("工作流名称不能为空")
                return False
            
            if not config.nodes:
                logger.error("工作流必须包含至少一个节点")
                return False
            
            if not config.entry_point:
                logger.error("工作流必须指定入口点")
                return False
            
            # 验证节点引用
            for edge in config.edges:
                if edge.from_node not in config.nodes:
                    logger.error(f"边引用了不存在的节点: {edge.from_node}")
                    return False
                if edge.to_node not in config.nodes:
                    logger.error(f"边引用了不存在的节点: {edge.to_node}")
                    return False
            
            logger.info(f"工作流配置验证通过: {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def get_config_metadata(self, config_id: str) -> Optional[Dict[str, Any]]:
        """获取配置元数据
        
        Args:
            config_id: 配置ID
            
        Returns:
            Optional[Dict[str, Any]]: 配置元数据
        """
        return self._config_metadata.get(config_id)
    
    def list_configs(self) -> List[str]:
        """列出所有已加载的配置
        
        Returns:
            List[str]: 配置ID列表
        """
        return list(self._configs.keys())
    
    def reload_config(self, config_id: str) -> bool:
        """重新加载配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            bool: 重新加载是否成功
        """
        metadata = self._config_metadata.get(config_id)
        if not metadata:
            logger.warning(f"配置不存在: {config_id}")
            return False
        
        config_path = metadata.get("config_path")
        if not config_path or not Path(config_path).exists():
            logger.error(f"配置文件不存在: {config_path}")
            return False
        
        try:
            # 移除旧配置
            del self._configs[config_id]
            del self._config_metadata[config_id]
            
            # 重新加载
            new_config_id = self.load_config(config_path)
            
            logger.info(f"配置重新加载成功: {config_id} -> {new_config_id}")
            return True
            
        except Exception as e:
            logger.error(f"重新加载配置失败: {config_id}, error: {e}")
            return False
    
    def _generate_config_id(self, workflow_name: str, config_path: str) -> str:
        """生成配置ID
        
        Args:
            workflow_name: 工作流名称
            config_path: 配置文件路径
            
        Returns:
            str: 配置ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{workflow_name}_{timestamp}_{unique_id}"
    
    def _calculate_checksum(self, config_path: str) -> str:
        """计算配置文件校验和
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            str: 校验和
        """
        try:
            with open(config_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""