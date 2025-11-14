"""配置系统重构验证测试

验证重构后的配置系统是否正常工作。
"""

import pytest
import tempfile
import os
from pathlib import Path

from .config_service_factory import ConfigServiceFactory, create_config_system
from .config_manager import ConfigManager
from .interfaces import IConfigLoader, IConfigInheritanceHandler, IConfigMerger, IConfigValidator
from .loader.yaml_loader import YamlConfigLoader
from .processor.inheritance import ConfigInheritanceHandler
from .processor.merger import ConfigMerger
from .processor.validator import ConfigValidator


class TestConfigServiceFactory:
    """测试配置服务工厂"""
    
    def test_create_config_system(self):
        """测试创建配置系统"""
        config_system = ConfigServiceFactory.create_config_system()
        assert config_system is not None
        
        # 测试加载全局配置
        global_config = config_system.load_global_config()
        assert global_config is not None
    
    def test_create_minimal_config_system(self):
        """测试创建最小配置系统"""
        config_system = ConfigServiceFactory.create_config_system(
            enable_inheritance=False,
            enable_error_recovery=False,
            enable_callback_manager=False
        )
        assert config_system is not None
    
    def test_create_config_loader(self):
        """测试创建配置加载器"""
        loader = ConfigServiceFactory.create_config_loader()
        assert isinstance(loader, IConfigLoader)
        assert isinstance(loader, YamlConfigLoader)
    
    def test_create_config_loader_with_inheritance(self):
        """测试创建带继承的配置加载器"""
        loader = ConfigServiceFactory.create_config_loader(enable_inheritance=True)
        assert isinstance(loader, IConfigLoader)
        assert isinstance(loader, YamlConfigLoader)
    
    def test_create_config_validator(self):
        """测试创建配置验证器"""
        validator = ConfigServiceFactory.create_config_validator()
        assert isinstance(validator, IConfigValidator)
        assert isinstance(validator, ConfigValidator)
    
    def test_create_config_merger(self):
        """测试创建配置合并器"""
        merger = ConfigServiceFactory.create_config_merger()
        assert isinstance(merger, IConfigMerger)
        assert isinstance(merger, ConfigMerger)


class TestConfigManager:
    """测试配置管理器"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "configs")
        os.makedirs(self.config_path, exist_ok=True)
        
        # 创建基本的配置文件
        global_config = """
log_level: INFO
env: test
debug: false
log_outputs:
  - type: console
    level: INFO
    format: text
secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
"""
        with open(os.path.join(self.config_path, "global.yaml"), "w") as f:
            f.write(global_config)
        
        # 创建配置系统
        self.config_system = ConfigServiceFactory.create_config_system(
            base_path=self.config_path
        )
        self.config_manager = ConfigManager(self.config_system)
    
    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_config_with_fallback(self):
        """测试带回退值的配置获取"""
        # 测试存在的配置
        global_config = self.config_manager.get_config_with_fallback(
            "global", "", None
        )
        assert global_config is not None
        assert global_config.env == "test"
        
        # 测试不存在的配置
        fallback_value = {"test": "fallback"}
        result = self.config_manager.get_config_with_fallback(
            "nonexistent", "test", fallback_value
        )
        assert result == fallback_value
    
    def test_get_config_summary(self):
        """测试获取配置摘要"""
        summary = self.config_manager.get_config_summary()
        assert "timestamp" in summary
        assert "config_counts" in summary
        assert "environment" in summary
        assert summary["environment"] == "test"
    
    def test_reload_and_validate(self):
        """测试重新加载和验证"""
        result = self.config_manager.reload_and_validate()
        assert result is not None
        # 由于我们只有基本配置，验证应该通过
        assert result.is_valid or len(result.errors) == 0


class TestCircularDependencyResolution:
    """测试循环依赖解决"""
    
    def test_no_circular_dependency(self):
        """测试没有循环依赖"""
        # 这个测试主要验证我们可以创建所有组件而没有循环依赖错误
        try:
            # 创建继承处理器
            inheritance_handler = ConfigInheritanceHandler()
            
            # 创建配置加载器
            loader = YamlConfigLoader(
                base_path="configs",
                inheritance_handler=inheritance_handler
            )
            
            # 设置继承处理器的加载器引用
            inheritance_handler.config_loader = loader
            
            # 如果没有循环依赖，这些操作应该成功
            assert True
            
        except Exception as e:
            pytest.fail(f"检测到循环依赖: {e}")


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_create_config_system_function(self):
        """测试便捷函数创建配置系统"""
        config_system = create_config_system()
        assert config_system is not None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])