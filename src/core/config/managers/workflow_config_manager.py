"""工作流配置管理器 - 工作流模块的配置管理

提供工作流特定的配置加载、保存和验证功能。
"""

from typing import Dict, Any, Optional
import logging

from src.interfaces.config import (
    IModuleConfigService,
    IConfigManager,
    ValidationResult
)
from src.interfaces.dependency_injection import get_logger
from src.core.workflow.graph_entities import Graph
from src.core.config.mappers import WorkflowConfigMapper
from src.infrastructure.config.models.base import ConfigData

logger = get_logger(__name__)


class WorkflowConfigManager(IModuleConfigService):
    """工作流配置管理器"""
    
    def __init__(self, 
                 config_manager: IConfigManager):
        """初始化工作流配置管理器
        
        Args:
            config_manager: 统一配置管理器
        """
        self.config_manager = config_manager
        self.mapper = WorkflowConfigMapper()
        
        logger.info("工作流配置管理器初始化完成")
    
    def load_config(self, config_path: str) -> Graph:
        """加载工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Graph: 工作流图实体
        """
        try:
            logger.debug(f"加载工作流配置: {config_path}")
            
            # 加载配置数据
            config_dict = self.config_manager.load_config(config_path, "workflow")
            
            # 转换为配置数据
            config_data = ConfigData(config_dict)
            
            # 转换为图实体
            graph = self.mapper.config_data_to_graph(config_data)
            
            logger.info(f"工作流配置加载成功: {config_path}")
            return graph
            
        except Exception as e:
            logger.error(f"加载工作流配置失败: {config_path}, 错误: {e}")
            raise
    
    def save_config(self, config: Graph, config_path: str) -> None:
        """保存工作流配置
        
        Args:
            config: 工作流图实体
            config_path: 配置文件路径
        """
        try:
            logger.debug(f"保存工作流配置: {config_path}")
            
            # 转换为配置数据
            config_data = self.mapper.graph_to_config_data(config)
            
            # 保存配置数据
            self.config_manager.save_config(config_data.data, config_path)
            
            logger.info(f"工作流配置保存成功: {config_path}")
            
        except Exception as e:
            logger.error(f"保存工作流配置失败: {config_path}, 错误: {e}")
            raise
    
    def validate_config(self, config: Graph) -> ValidationResult:
        """验证工作流配置
        
        Args:
            config: 工作流图实体
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            logger.debug("验证工作流配置")
            
            # 使用图实体验证方法
            validation_result = config.validate_structure()
            
            # 转换为通用验证结果
            result = ValidationResult(
                is_valid=validation_result.is_valid,
                errors=validation_result.errors,
                warnings=validation_result.warnings
            )
            
            logger.info(f"工作流配置验证完成: {'通过' if result.is_valid else '失败'}")
            return result
            
        except Exception as e:
            logger.error(f"验证工作流配置失败: {e}")
            return ValidationResult(is_valid=False, errors=[str(e)], warnings=[])
    
    def create_workflow_from_config(self, config_path: str) -> Graph:
        """从配置文件创建工作流
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Graph: 工作流图实体
        """
        return self.load_config(config_path)
    
    def save_workflow_to_config(self, workflow: Graph, config_path: str) -> None:
        """保存工作流到配置文件
        
        Args:
            workflow: 工作流图实体
            config_path: 配置文件路径
        """
        self.save_config(workflow, config_path)
    
    def validate_workflow_config_file(self, config_path: str) -> ValidationResult:
        """验证工作流配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            # 加载配置
            workflow = self.load_config(config_path)
            
            # 验证配置
            return self.validate_config(workflow)
            
        except Exception as e:
            logger.error(f"验证工作流配置文件失败: {config_path}, 错误: {e}")
            return ValidationResult(is_valid=False, errors=[str(e)], warnings=[])
    
    def get_workflow_template(self, template_name: str) -> Graph:
        """获取工作流模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            Graph: 工作流图实体
        """
        try:
            template_path = f"templates/workflow/{template_name}"
            return self.load_config(template_path)
            
        except Exception as e:
            logger.error(f"获取工作流模板失败: {template_name}, 错误: {e}")
            raise
    
    def save_workflow_template(self, workflow: Graph, template_name: str) -> None:
        """保存工作流模板
        
        Args:
            workflow: 工作流图实体
            template_name: 模板名称
        """
        try:
            template_path = f"templates/workflow/{template_name}"
            self.save_config(workflow, template_path)
            
        except Exception as e:
            logger.error(f"保存工作流模板失败: {template_name}, 错误: {e}")
            raise
    
    def clone_workflow(self, source_config_path: str, target_config_path: str, 
                       name_override: Optional[str] = None, 
                       description_override: Optional[str] = None) -> Graph:
        """克隆工作流
        
        Args:
            source_config_path: 源配置文件路径
            target_config_path: 目标配置文件路径
            name_override: 名称覆盖
            description_override: 描述覆盖
            
        Returns:
            Graph: 克隆的工作流图实体
        """
        try:
            # 加载源工作流
            workflow = self.load_config(source_config_path)
            
            # 应用覆盖
            if name_override:
                workflow.name = name_override
            if description_override:
                workflow.description = description_override
            
            # 保存到目标路径
            self.save_config(workflow, target_config_path)
            
            logger.info(f"工作流克隆成功: {source_config_path} -> {target_config_path}")
            return workflow
            
        except Exception as e:
            logger.error(f"克隆工作流失败: {source_config_path} -> {target_config_path}, 错误: {e}")
            raise
    
    def merge_workflows(self, workflow_configs: list[str], 
                       merged_config_path: str,
                       merged_name: str,
                       merged_description: str = "") -> Graph:
        """合并多个工作流
        
        Args:
            workflow_configs: 工作流配置文件路径列表
            merged_config_path: 合并后的配置文件路径
            merged_name: 合并后的工作流名称
            merged_description: 合并后的工作流描述
            
        Returns:
            Graph: 合并后的工作流图实体
        """
        try:
            if not workflow_configs:
                raise ValueError("工作流配置列表不能为空")
            
            # 加载第一个工作流作为基础
            base_workflow = self.load_config(workflow_configs[0])
            
            # 合并其他工作流
            for config_path in workflow_configs[1:]:
                workflow = self.load_config(config_path)
                
                # 合并节点
                for node_id, node in workflow.nodes.items():
                    if node_id not in base_workflow.nodes:
                        base_workflow.add_node(node)
                
                # 合并边
                for edge in workflow.edges:
                    # 检查边是否已存在
                    edge_exists = any(
                        existing_edge.from_node_id == edge.from_node_id and
                        existing_edge.to_node_id == edge.to_node_id and
                        existing_edge.edge_type == edge.edge_type
                        for existing_edge in base_workflow.edges
                    )
                    if not edge_exists:
                        base_workflow.edges.append(edge)
                
                # 合并状态字段
                for field_name, field in workflow.state.fields.items():
                    if field_name not in base_workflow.state.fields:
                        base_workflow.state.add_field(field)
            
            # 设置合并后的属性
            base_workflow.name = merged_name
            base_workflow.description = merged_description
            
            # 保存合并后的工作流
            self.save_config(base_workflow, merged_config_path)
            
            logger.info(f"工作流合并成功: {len(workflow_configs)}个工作流 -> {merged_config_path}")
            return base_workflow
            
        except Exception as e:
            logger.error(f"合并工作流失败: {e}")
            raise


# 创建默认实例
default_workflow_config_manager: Optional[WorkflowConfigManager] = None


def get_workflow_config_manager(config_manager: IConfigManager) -> WorkflowConfigManager:
    """获取工作流配置管理器实例
    
    Args:
        config_manager: 统一配置管理器
        
    Returns:
        WorkflowConfigManager: 工作流配置管理器实例
    """
    global default_workflow_config_manager
    if default_workflow_config_manager is None:
        default_workflow_config_manager = WorkflowConfigManager(config_manager)
        return default_workflow_config_manager
