"""状态模板测试

测试状态模板管理功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../src'))

from application.workflow.state_machine.state_templates import (
    StateTemplate, StateTemplateManager, get_global_template_manager, create_state_from_template
)
from src.infrastructure.graph.config import GraphConfig


class TestStateTemplate:
    """测试状态模板"""

    def test_state_template_init(self):
        """测试状态模板初始化"""
        template = StateTemplate(
            name="test_template",
            description="测试模板",
            fields={"field1": "value1", "field2": "value2"},
            inherits_from="base_template",
            metadata={"author": "test"}
        )
        
        assert template.name == "test_template"
        assert template.description == "测试模板"
        assert template.fields == {"field1": "value1", "field2": "value2"}
        assert template.inherits_from == "base_template"
        assert template.metadata == {"author": "test"}

    def test_merge_with_parent(self):
        """测试与父模板合并"""
        parent_template = StateTemplate(
            name="parent",
            description="父模板",
            fields={"parent_field": "parent_value", "shared_field": "parent_shared"},
            metadata={"parent_meta": "value"}
        )
        
        child_template = StateTemplate(
            name="child",
            description="子模板",
            fields={"child_field": "child_value", "shared_field": "child_shared"},
            inherits_from="parent",
            metadata={"child_meta": "value"}
        )
        
        merged = child_template.merge_with_parent(parent_template)
        
        assert merged.name == "child"
        assert merged.description == "子模板"
        # 子模板的字段应该覆盖父模板的同名字段
        assert merged.fields["shared_field"] == "child_shared"
        assert merged.fields["parent_field"] == "parent_value"
        assert merged.fields["child_field"] == "child_value"
        # 元数据应该合并
        assert merged.metadata["parent_meta"] == "value"
        assert merged.metadata["child_meta"] == "value"


class TestStateTemplateManager:
    """测试状态模板管理器"""

    @pytest.fixture
    def manager(self):
        """管理器fixture"""
        return StateTemplateManager()

    def test_manager_init(self, manager):
        """测试管理器初始化"""
        assert isinstance(manager._templates, dict)
        # 检查是否注册了内置模板
        assert len(manager._templates) > 0
        assert "base_state" in manager._templates

    def test_register_template_success(self, manager):
        """测试成功注册模板"""
        template = StateTemplate("test_template", "测试模板")
        manager.register_template(template)
        assert "test_template" in manager._templates
        assert manager._templates["test_template"] == template

    def test_register_template_empty_name(self, manager):
        """测试注册空名称模板"""
        template = StateTemplate("", "测试模板")
        with pytest.raises(ValueError, match="模板名称不能为空"):
            manager.register_template(template)

    def test_get_template(self, manager):
        """测试获取模板"""
        template = StateTemplate("test_template", "测试模板")
        manager.register_template(template)
        
        retrieved = manager.get_template("test_template")
        assert retrieved == template
        
        # 获取不存在的模板应该返回None
        assert manager.get_template("nonexistent") is None

    def test_create_state_from_template(self, manager):
        """测试从模板创建状态"""
        template = StateTemplate(
            name="test_template",
            description="测试模板",
            fields={"field1": "default1", "field2": "default2"}
        )
        manager.register_template(template)
        
        state = manager.create_state_from_template("test_template", {"field2": "overridden"})
        assert state["field1"] == "default1"
        assert state["field2"] == "overridden"

    def test_create_state_from_template_not_found(self, manager):
        """测试从不存在的模板创建状态"""
        with pytest.raises(ValueError, match="状态模板 'nonexistent' 不存在"):
            manager.create_state_from_template("nonexistent")

    def test_create_state_from_config_with_template(self, manager):
        """测试从配置创建状态（使用模板）"""
        template = StateTemplate(
            name="test_template",
            description="测试模板",
            fields={"field1": "default1", "field2": "default2"}
        )
        manager.register_template(template)
        
        # 创建带有模板名称的配置
        config = Mock(spec=GraphConfig)
        config.state_template = "test_template"
        config.state_overrides = {"field2": "config_overridden"}
        
        state = manager.create_state_from_config(config, {"field1": "initial"})
        assert state["field1"] == "initial"  # 初始数据优先
        assert state["field2"] == "config_overridden"  # 配置覆盖

    def test_create_state_from_config_without_template(self, manager):
        """测试从配置创建状态（不使用模板）"""
        config = Mock(spec=GraphConfig)
        config.state_template = None
        
        # 模拟状态模式
        mock_state_schema = Mock()
        mock_field_config = Mock()
        mock_field_config.default = "default_value"
        mock_state_schema.fields = {"test_field": mock_field_config}
        config.state_schema = mock_state_schema
        config.state_overrides = {"override_field": "overridden"}
        
        state = manager.create_state_from_config(config, {"initial_field": "initial"})
        assert state["initial_field"] == "initial"
        assert state["test_field"] == "default_value"
        assert state["override_field"] == "overridden"

    def test_list_templates(self, manager):
        """测试列出模板"""
        template_names = manager.list_templates()
        assert isinstance(template_names, list)
        assert "base_state" in template_names
        assert "workflow_state" in template_names

    def test_get_template_info(self, manager):
        """测试获取模板信息"""
        info = manager.get_template_info("base_state")
        assert info is not None
        assert info["name"] == "base_state"
        assert "messages" in info["fields"]
        assert info["field_count"] > 0

    def test_get_template_info_not_found(self, manager):
        """测试获取不存在的模板信息"""
        info = manager.get_template_info("nonexistent")
        assert info is None

    def test_resolve_template_inheritance(self, manager):
        """测试解析模板继承"""
        parent_template = StateTemplate(
            name="parent",
            description="父模板",
            fields={"parent_field": "parent_value"}
        )
        child_template = StateTemplate(
            name="child",
            description="子模板",
            fields={"child_field": "child_value"},
            inherits_from="parent"
        )
        
        manager.register_template(parent_template)
        manager.register_template(child_template)
        
        resolved = manager._resolve_template_inheritance(child_template)
        assert resolved.fields["parent_field"] == "parent_value"
        assert resolved.fields["child_field"] == "child_value"

    def test_resolve_template_inheritance_missing_parent(self, manager):
        """测试解析模板继承（父模板缺失）"""
        child_template = StateTemplate(
            name="child",
            description="子模板",
            fields={"child_field": "child_value"},
            inherits_from="missing_parent"
        )
        
        # 应该不会抛出异常，而是返回原始模板
        resolved = manager._resolve_template_inheritance(child_template)
        assert resolved == child_template

    def test_validate_template_success(self, manager):
        """测试模板验证成功"""
        template = StateTemplate("test_template", "测试模板")
        errors = manager.validate_template(template)
        assert len(errors) == 0

    def test_validate_template_empty_name(self, manager):
        """测试模板验证（空名称）"""
        template = StateTemplate("", "测试模板")
        errors = manager.validate_template(template)
        assert len(errors) == 1
        assert "模板名称不能为空" in errors[0]

    def test_validate_template_empty_description(self, manager):
        """测试模板验证（空描述）"""
        template = StateTemplate("test_template", "")
        errors = manager.validate_template(template)
        assert len(errors) == 1
        assert "模板描述不能为空" in errors[0]

    def test_validate_template_missing_parent(self, manager):
        """测试模板验证（缺失父模板）"""
        template = StateTemplate("test_template", "测试模板", inherits_from="missing_parent")
        errors = manager.validate_template(template)
        assert len(errors) == 1
        assert "父模板 'missing_parent' 不存在" in errors[0]

    def test_export_import_template(self, manager):
        """测试导出和导入模板"""
        original_template = StateTemplate(
            name="export_test",
            description="导出测试模板",
            fields={"test_field": "test_value"},
            metadata={"author": "tester"}
        )
        
        # 导出模板
        exported_data = manager.export_template("export_test")
        assert exported_data is None  # 模板尚未注册
        
        manager.register_template(original_template)
        exported_data = manager.export_template("export_test")
        assert exported_data is not None
        assert exported_data["name"] == "export_test"
        assert exported_data["fields"]["test_field"] == "test_value"
        
        # 导入模板
        manager._templates.pop("export_test", None)  # 移除原模板
        success = manager.import_template(exported_data)
        assert success is True
        assert "export_test" in manager._templates

    def test_import_template_invalid(self, manager):
        """测试导入无效模板"""
        invalid_data = {"name": "", "description": "无效模板"}
        success = manager.import_template(invalid_data)
        assert success is False


class TestGlobalFunctions:
    """测试全局函数"""

    def test_get_global_template_manager(self):
        """测试获取全局模板管理器"""
        # 重置全局管理器
        with patch('src.application.workflow.state_machine.state_templates._global_template_manager', None):
            manager1 = get_global_template_manager()
            manager2 = get_global_template_manager()
            
            assert manager1 is not None
            assert manager2 is not None
            assert manager1 == manager2

    def test_create_state_from_template_global(self):
        """测试全局创建状态函数"""
        with patch('src.application.workflow.state_machine.state_templates.get_global_template_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.create_state_from_template.return_value = {"test": "state"}
            mock_manager.get_template.return_value = Mock()  # 返回一个非空模板
            mock_get_manager.return_value = mock_manager
            
            result = create_state_from_template("test_template", {"override": "value"})
            
            assert result == {"test": "state"}
            mock_manager.create_state_from_template.assert_called_once_with("test_template", {"override": "value"})