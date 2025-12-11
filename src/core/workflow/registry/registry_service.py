"""工作流注册表服务

统一管理工作流定义、发现和元数据
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.interfaces.dependency_injection import get_logger
import uuid

from src.interfaces.workflow.core import IWorkflow
from src.interfaces.workflow.exceptions import WorkflowError, WorkflowValidationError

logger = get_logger(__name__)


class IWorkflowRegistryService(ABC):
    """工作流注册表服务接口"""
    
    @abstractmethod
    def register_workflow(self, workflow_def: Dict[str, Any]) -> str:
        """注册工作流定义"""
        raise NotImplementedError
    
    @abstractmethod
    def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流定义"""
        raise NotImplementedError
    
    @abstractmethod
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """列出可用工作流"""
        raise NotImplementedError
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[str]:
        """根据名称查找工作流ID"""
        raise NotImplementedError
    
    @abstractmethod
    def find_by_tag(self, tag: str) -> List[str]:
        """根据标签查找工作流ID列表"""
        raise NotImplementedError
    
    @abstractmethod
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> bool:
        """更新工作流定义"""
        raise NotImplementedError
    
    @abstractmethod
    def unregister_workflow(self, workflow_id: str) -> bool:
        """注销工作流"""
        raise NotImplementedError
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        raise NotImplementedError


class WorkflowDefinition:
    """工作流定义数据模型"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str,
        version: str,
        config_id: str,
        config_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.version = version
        self.config_id = config_id
        self.config_path = config_path
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class WorkflowRegistryService(IWorkflowRegistryService):
    """工作流注册表服务实现
    
    专注于：
    - 工作流定义注册和管理
    - 工作流发现和查询
    - 元数据统一管理
    """
    
    def __init__(self):
        """初始化工作流注册表"""
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._name_index: Dict[str, str] = {}  # name -> workflow_id
        self._tag_index: Dict[str, List[str]] = {}  # tag -> [workflow_ids]
        
        logger.info("WorkflowRegistryService初始化完成")
    
    def register_workflow(self, workflow_def: Dict[str, Any]) -> str:
        """注册工作流定义
        
        Args:
            workflow_def: 工作流定义字典
            
        Returns:
            str: 工作流ID
        """
        try:
            # 验证必要字段
            required_fields = ["name", "description", "version", "config_id", "config_path"]
            for field in required_fields:
                if field not in workflow_def:
                    raise WorkflowValidationError(f"缺少必要字段: {field}")
            
            # 生成工作流ID（如果未提供）
            workflow_id = workflow_def.get("workflow_id")
            if not workflow_id:
                workflow_id = self._generate_workflow_id(workflow_def["name"])
            
            # 创建工作流定义
            definition = WorkflowDefinition(
                workflow_id=workflow_id,
                name=workflow_def["name"],
                description=workflow_def["description"],
                version=workflow_def["version"],
                config_id=workflow_def["config_id"],
                config_path=workflow_def["config_path"],
                metadata=workflow_def.get("metadata", {})
            )
            
            # 检查名称冲突
            if definition.name in self._name_index and self._name_index[definition.name] != workflow_id:
                logger.warning(f"工作流名称冲突: {definition.name}")
                # 可以选择覆盖或抛出异常
                # raise WorkflowValidationError(f"工作流名称已存在: {definition.name}")
            
            # 注册到存储
            self._workflows[workflow_id] = definition
            self._name_index[definition.name] = workflow_id
            
            # 更新标签索引
            tags = definition.metadata.get("tags", [])
            for tag in tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                if workflow_id not in self._tag_index[tag]:
                    self._tag_index[tag].append(workflow_id)
            
            logger.info(f"工作流注册成功: {workflow_id} - {definition.name}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"工作流注册失败: {e}")
            raise WorkflowError(f"工作流注册失败: {str(e)}")
    
    def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流定义
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[Dict[str, Any]]: 工作流定义
        """
        definition = self._workflows.get(workflow_id)
        if not definition:
            return None
        
        return {
            "workflow_id": definition.workflow_id,
            "name": definition.name,
            "description": definition.description,
            "version": definition.version,
            "config_id": definition.config_id,
            "config_path": definition.config_path,
            "metadata": definition.metadata,
            "created_at": definition.created_at.isoformat(),
            "updated_at": definition.updated_at.isoformat()
        }
    
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """列出可用工作流
        
        Returns:
            List[Dict[str, Any]]: 工作流定义列表
        """
        return [
            {
                "workflow_id": definition.workflow_id,
                "name": definition.name,
                "description": definition.description,
                "version": definition.version,
                "tags": definition.metadata.get("tags", []),
                "created_at": definition.created_at.isoformat(),
                "updated_at": definition.updated_at.isoformat()
            }
            for definition in self._workflows.values()
        ]
    
    def find_by_name(self, name: str) -> Optional[str]:
        """根据名称查找工作流ID
        
        Args:
            name: 工作流名称
            
        Returns:
            Optional[str]: 工作流ID
        """
        return self._name_index.get(name)
    
    def find_by_tag(self, tag: str) -> List[str]:
        """根据标签查找工作流ID列表
        
        Args:
            tag: 标签
            
        Returns:
            List[str]: 工作流ID列表
        """
        return self._tag_index.get(tag, [])
    
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> bool:
        """更新工作流定义
        
        Args:
            workflow_id: 工作流ID
            updates: 更新内容
            
        Returns:
            bool: 更新是否成功
        """
        definition = self._workflows.get(workflow_id)
        if not definition:
            logger.warning(f"工作流不存在: {workflow_id}")
            return False
        
        try:
            # 更新允许的字段
            updatable_fields = ["description", "version", "metadata"]
            for field in updatable_fields:
                if field in updates:
                    setattr(definition, field, updates[field])
            
            definition.updated_at = datetime.now()
            
            # 如果名称发生变化，更新名称索引
            if "name" in updates and updates["name"] != definition.name:
                # 移除旧名称索引
                if definition.name in self._name_index:
                    del self._name_index[definition.name]
                
                # 添加新名称索引
                definition.name = updates["name"]
                self._name_index[definition.name] = workflow_id
            
            # 更新标签索引
            if "metadata" in updates and "tags" in updates["metadata"]:
                # 移除旧标签索引
                old_tags = definition.metadata.get("tags", [])
                for tag in old_tags:
                    if tag in self._tag_index and workflow_id in self._tag_index[tag]:
                        self._tag_index[tag].remove(workflow_id)
                
                # 添加新标签索引
                new_tags = updates["metadata"]["tags"]
                for tag in new_tags:
                    if tag not in self._tag_index:
                        self._tag_index[tag] = []
                    if workflow_id not in self._tag_index[tag]:
                        self._tag_index[tag].append(workflow_id)
                
                definition.metadata["tags"] = new_tags
            
            logger.info(f"工作流更新成功: {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"工作流更新失败: {workflow_id}, error: {e}")
            return False
    
    def unregister_workflow(self, workflow_id: str) -> bool:
        """注销工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 注销是否成功
        """
        definition = self._workflows.get(workflow_id)
        if not definition:
            logger.warning(f"工作流不存在: {workflow_id}")
            return False
        
        try:
            # 从名称索引移除
            if definition.name in self._name_index:
                del self._name_index[definition.name]
            
            # 从标签索引移除
            tags = definition.metadata.get("tags", [])
            for tag in tags:
                if tag in self._tag_index and workflow_id in self._tag_index[tag]:
                    self._tag_index[tag].remove(workflow_id)
            
            # 从主存储移除
            del self._workflows[workflow_id]
            
            logger.info(f"工作流注销成功: {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"工作流注销失败: {workflow_id}, error: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "total_workflows": len(self._workflows),
            "total_tags": len(self._tag_index),
            "tag_distribution": {tag: len(ids) for tag, ids in self._tag_index.items()},
            "recent_workflows": [
                {
                    "workflow_id": definition.workflow_id,
                    "name": definition.name,
                    "created_at": definition.created_at.isoformat()
                }
                for definition in sorted(
                    self._workflows.values(),
                    key=lambda x: x.created_at,
                    reverse=True
                )[:5]
            ]
        }
    
    def _generate_workflow_id(self, name: str) -> str:
        """生成工作流ID
        
        Args:
            name: 工作流名称
            
        Returns:
            str: 工作流ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{name}_{timestamp}_{unique_id}"