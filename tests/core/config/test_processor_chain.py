"""配置处理器链测试

测试配置处理器链的功能。
"""

import pytest
import tempfile
import yaml
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.config.processor.config_processor_chain import (
    ConfigProcessorChain,
    InheritanceProcessor,
    EnvironmentVariableProcessor,
    ReferenceProcessor
)


class TestConfigProcessorChain:
    """配置处理器链测试类"""
    
    @pytest.fixture
    def processor_chain(self):
        """处理器链实例"""
        return ConfigProcessorChain()
    
    @pytest.fixture
    def mock_processor(self):
        """模拟处理器"""
        processor = Mock()
        processor.process.return_value = {"processed": True}
        return processor
    
    def test_init_processor_chain(self, processor_chain):
        """测试初始化处理器链"""
        assert processor_chain.processors == []
        assert processor_chain.get_processor_count() == 0
        assert processor_chain.get_processor_names() == []
    
    def test_add_processor(self, processor_chain, mock_processor):
        """测试添加处理器"""
        processor_chain.add_processor(mock_processor)
        
        assert len(processor_chain.processors) == 1
        assert processor_chain.processors[0] == mock_processor
        assert processor_chain.get_processor_count() == 1
        assert "Mock" in processor_chain.get_processor_names()[0]
    
    def test_remove_processor(self, processor_chain, mock_processor):
        """测试移除处理器"""
        processor_chain.add_processor(mock_processor)
        
        result = processor_chain.remove_processor(mock_processor)
        
        assert result is True
        assert len(processor_chain.processors) == 0
        
        # 测试移除不存在的处理器
        result = processor_chain.remove_processor(mock_processor)
        assert result is False
    
    def test_clear_processors(self, processor_chain, mock_processor):
        """测试清除所有处理器"""
        processor_chain.add_processor(mock_processor)
        processor_chain.add_processor(mock_processor)
        
        processor_chain.clear_processors()
        
        assert len(processor_chain.processors) == 0
    
    def test_process_empty_chain(self, processor_chain):
        """测试空处理器链处理"""
        config = {"test": "value"}
        result = processor_chain.process(config, "test.yaml")
        
        assert result == config
    
    def test_process_single_processor(self, processor_chain, mock_processor):
        """测试单个处理器处理"""
        config = {"test": "value"}
        processor_chain.add_processor(mock_processor)
        
        result = processor_chain.process(config, "test.yaml")
        
        assert result == {"processed": True}
        mock_processor.process.assert_called_once_with(config, "test.yaml")
    
    def test_process_multiple_processors(self, processor_chain):
        """测试多个处理器处理"""
        # 创建模拟处理器
        processor1 = Mock()
        processor1.process.return_value = {"step1": True}
        
        processor2 = Mock()
        processor2.process.return_value = {"step2": True}
        
        processor_chain.add_processor(processor1)
        processor_chain.add_processor(processor2)
        
        config = {"test": "value"}
        result = processor_chain.process(config, "test.yaml")
        
        assert result == {"step2": True}
        processor1.process.assert_called_once_with(config, "test.yaml")
        processor2.process.assert_called_once_with({"step1": True}, "test.yaml")
    
    def test_process_with_exception(self, processor_chain, mock_processor):
        """测试处理器异常"""
        mock_processor.process.side_effect = Exception("处理器错误")
        processor_chain.add_processor(mock_processor)
        
        config = {"test": "value"}
        
        with pytest.raises(Exception, match="处理器错误"):
            processor_chain.process(config, "test.yaml")


class TestInheritanceProcessor:
    """继承处理器测试类"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """临时配置目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def processor(self):
        """继承处理器实例"""
        return InheritanceProcessor()
    
    def test_process_no_inheritance(self, processor):
        """测试无继承配置处理"""
        config = {"name": "test", "value": "data"}
        result = processor.process(config, "test.yaml")
        
        assert result == config
    
    def test_process_single_inheritance(self, processor, temp_config_dir):
        """测试单一继承处理"""
        # 创建父配置文件
        parent_config = {
            "name": "parent",
            "base_value": "base_data",
            "shared": {
                "common": "parent_common"
            }
        }
        parent_file = temp_config_dir / "parent.yaml"
        with open(parent_file, 'w', encoding='utf-8') as f:
            yaml.dump(parent_config, f)
        
        # 创建子配置
        child_config = {
            "inherits_from": "parent.yaml",
            "name": "child",
            "child_value": "child_data",
            "shared": {
                "specific": "child_specific"
            }
        }
        
        # 处理继承
        result = processor.process(child_config, str(temp_config_dir / "child.yaml"))
        
        # 验证合并结果
        assert result["name"] == "child"  # 子配置覆盖
        assert result["base_value"] == "base_data"  # 继承自父配置
        assert result["child_value"] == "child_data"  # 子配置特有
        assert result["shared"]["common"] == "parent_common"  # 继承
        assert result["shared"]["specific"] == "child_specific"  # 子配置覆盖
        assert "inherits_from" not in result  # 继承字段被移除
    
    def test_process_multiple_inheritance(self, processor, temp_config_dir):
        """测试多重继承处理"""
        # 创建父配置文件
        parent1_config = {"value1": "data1", "shared": "parent1"}
        parent1_file = temp_config_dir / "parent1.yaml"
        with open(parent1_file, 'w', encoding='utf-8') as f:
            yaml.dump(parent1_config, f)
        
        parent2_config = {"value2": "data2", "shared": "parent2"}
        parent2_file = temp_config_dir / "parent2.yaml"
        with open(parent2_file, 'w', encoding='utf-8') as f:
            yaml.dump(parent2_config, f)
        
        # 创建子配置
        child_config = {
            "inherits_from": ["parent1.yaml", "parent2.yaml"],
            "name": "child"
        }
        
        # 处理继承
        result = processor.process(child_config, str(temp_config_dir / "child.yaml"))
        
        # 验证合并结果
        assert result["name"] == "child"
        assert result["value1"] == "data1"
        assert result["value2"] == "data2"
        assert result["shared"] == "parent2"  # 后继承的覆盖
    
    def test_process_circular_inheritance(self, processor, temp_config_dir):
        """测试循环继承检测"""
        # 创建循环继承的配置文件
        config1 = {"inherits_from": "config2.yaml", "name": "config1"}
        config2 = {"inherits_from": "config1.yaml", "name": "config2"}
        
        file1 = temp_config_dir / "config1.yaml"
        file2 = temp_config_dir / "config2.yaml"
        
        with open(file1, 'w', encoding='utf-8') as f:
            yaml.dump(config1, f)
        with open(file2, 'w', encoding='utf-8') as f:
            yaml.dump(config2, f)
        
        # 检测循环继承
        with pytest.raises(ValueError, match="检测到循环继承"):
            processor.process(config1, str(file1))
    
    def test_process_missing_parent(self, processor, temp_config_dir):
        """测试缺失父配置文件"""
        child_config = {"inherits_from": "missing.yaml", "name": "child"}
        
        with pytest.raises(FileNotFoundError, match="继承配置文件不存在"):
            processor.process(child_config, str(temp_config_dir / "child.yaml"))


class TestEnvironmentVariableProcessor:
    """环境变量处理器测试类"""
    
    @pytest.fixture
    def processor(self):
        """环境变量处理器实例"""
        return EnvironmentVariableProcessor()
    
    def test_process_no_env_vars(self, processor):
        """测试无环境变量配置处理"""
        config = {"name": "test", "value": "data"}
        result = processor.process(config, "test.yaml")
        
        assert result == config
    
    @patch.dict(os.environ, {'TEST_VAR': 'test_value', 'ANOTHER_VAR': 'another_value'})
    def test_process_simple_env_var(self, processor):
        """测试简单环境变量替换"""
        config = {
            "name": "test",
            "value": "${TEST_VAR}",
            "nested": {
                "env": "${ANOTHER_VAR}"
            }
        }
        
        result = processor.process(config, "test.yaml")
        
        assert result["value"] == "test_value"
        assert result["nested"]["env"] == "another_value"
    
    @patch.dict(os.environ, {'TEST_VAR': 'test_value'})
    def test_process_env_var_with_default(self, processor):
        """测试带默认值的环境变量替换"""
        config = {
            "existing": "${TEST_VAR:default_value}",
            "missing": "${MISSING_VAR:default_value}"
        }
        
        result = processor.process(config, "test.yaml")
        
        assert result["existing"] == "test_value"
        assert result["missing"] == "default_value"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_process_missing_env_var_no_default(self, processor):
        """测试缺失环境变量无默认值"""
        config = {"value": "${MISSING_VAR}"}
        
        result = processor.process(config, "test.yaml")
        
        # 应该保持原样，因为环境变量未定义且无默认值
        assert result["value"] == "${MISSING_VAR}"
    
    def test_process_env_var_in_list(self, processor):
        """测试列表中的环境变量"""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            config = {
                "values": ["${TEST_VAR}", "static_value"]
            }
            
            result = processor.process(config, "test.yaml")
            
            assert result["values"][0] == "test_value"
            assert result["values"][1] == "static_value"


class TestReferenceProcessor:
    """引用处理器测试类"""
    
    @pytest.fixture
    def processor(self):
        """引用处理器实例"""
        return ReferenceProcessor()
    
    def test_process_no_references(self, processor):
        """测试无引用配置处理"""
        config = {"name": "test", "value": "data"}
        result = processor.process(config, "test.yaml")
        
        assert result == config
    
    def test_process_simple_reference(self, processor):
        """测试简单引用处理"""
        config = {
            "name": "test",
            "value": "data",
            "ref_value": "$ref: value"
        }
        
        result = processor.process(config, "test.yaml")
        
        assert result["ref_value"] == "data"
    
    def test_process_nested_reference(self, processor):
        """测试嵌套引用处理"""
        config = {
            "name": "test",
            "nested": {
                "value": "data",
                "ref": "$ref: nested.value"
            }
        }
        
        result = processor.process(config, "test.yaml")
        
        assert result["nested"]["ref"] == "data"
    
    def test_process_reference_in_list(self, processor):
        """测试列表中的引用"""
        config = {
            "name": "test",
            "value": "data",
            "list": ["${TEST_VAR}", "$ref: value"]
        }
        
        result = processor.process(config, "test.yaml")
        
        assert result["list"][1] == "data"
    
    def test_process_missing_reference(self, processor):
        """测试缺失引用路径"""
        config = {
            "name": "test",
            "ref_value": "$ref: missing.path"
        }
        
        with pytest.raises(ValueError, match="引用路径不存在"):
            processor.process(config, "test.yaml")
    
    def test_process_circular_reference(self, processor):
        """测试循环引用检测"""
        config = {
            "name": "test",
            "value": "$ref: ref_value",
            "ref_value": "$ref: value"
        }
        
        # 这应该会导致无限递归，我们需要在实现中处理这种情况
        # 当前的实现可能不会检测循环引用，这是一个改进点
        with pytest.raises(ValueError):
            processor.process(config, "test.yaml")