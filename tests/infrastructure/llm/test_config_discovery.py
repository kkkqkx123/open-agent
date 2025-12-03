"""配置发现器测试

测试配置发现器的配置加载和管理功能。
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.infrastructure.llm.config.config_discovery import (
    ConfigDiscovery,
    ConfigInfo
)


class TestConfigDiscovery:
    """配置发现器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.discovery = ConfigDiscovery(self.config_dir)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init_with_default_config_dir(self):
        """测试使用默认配置目录初始化"""
        discovery = ConfigDiscovery()
        assert discovery.config_dir == Path("configs/llms")
    
    def test_init_with_custom_config_dir(self):
        """测试使用自定义配置目录初始化"""
        custom_dir = Path("/custom/config")
        discovery = ConfigDiscovery(custom_dir)
        assert discovery.config_dir == custom_dir
    
    def test_discover_configs_empty_dir(self):
        """测试发现空目录中的配置"""
        configs = self.discovery.discover_configs()
        assert configs == []
    
    def test_discover_configs_with_files(self):
        """测试发现配置文件"""
        # 创建测试配置文件
        config_data = {
            "provider": "openai",
            "models": ["gpt-4", "gpt-3.5-turbo"]
        }
        
        config_file = self.config_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 发现配置
        configs = self.discovery.discover_configs()
        
        assert len(configs) == 1
        assert isinstance(configs[0], ConfigInfo)
        assert configs[0].provider == "openai"
        assert configs[0].models == ["gpt-4", "gpt-3.5-turbo"]
    
    def test_discover_configs_with_provider_filter(self):
        """测试使用提供商过滤器发现配置"""
        # 创建不同提供商的配置文件
        openai_config = {
            "provider": "openai",
            "models": ["gpt-4"]
        }
        gemini_config = {
            "provider": "gemini", 
            "models": ["gemini-pro"]
        }
        
        openai_file = self.config_dir / "openai_config.yaml"
        gemini_file = self.config_dir / "gemini_config.yaml"
        
        with open(openai_file, 'w') as f:
            yaml.dump(openai_config, f)
        with open(gemini_file, 'w') as f:
            yaml.dump(gemini_config, f)
        
        # 只发现OpenAI配置
        configs = self.discovery.discover_configs(provider="openai")
        
        assert len(configs) == 1
        assert configs[0].provider == "openai"
    
    def test_load_provider_config_with_model(self):
        """测试加载指定提供商和模型的配置"""
        # 创建测试配置文件
        config_data = {
            "provider": "openai",
            "models": ["gpt-4"],
            "base_url": "https://api.openai.com/v1",
            "timeout": 30
        }
        
        config_file = self.config_dir / "openai_gpt4.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 加载配置
        config = self.discovery.load_provider_config("openai", "gpt-4")
        
        assert config["provider"] == "openai"
        assert config["base_url"] == "https://api.openai.com/v1"
        assert config["timeout"] == 30
    
    def test_load_provider_config_not_found(self):
        """测试加载不存在的配置"""
        config = self.discovery.load_provider_config("nonexistent", "model")
        
        # 应该返回默认配置
        assert config == {}
    
    def test_load_provider_config_with_env_vars(self):
        """测试加载包含环境变量的配置"""
        # 设置环境变量
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key-value'}):
            config_data = {
                "provider": "openai",
                "models": ["gpt-4"],
                "api_key": "${TEST_API_KEY}"
            }
            
            config_file = self.config_dir / "openai_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)
            
            # 加载配置
            config = self.discovery.load_provider_config("openai", "gpt-4")
            
            assert config["api_key"] == "test-key-value"
    
    def test_load_provider_config_with_inheritance(self):
        """测试配置继承"""
        # 创建基础配置
        base_config = {
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30
        }
        
        base_file = self.config_dir / "base.yaml"
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        
        # 创建继承配置
        child_config = {
            "inherits_from": "base",
            "models": ["gpt-4"],
            "timeout": 60  # 覆盖基础配置
        }
        
        child_file = self.config_dir / "child.yaml"
        with open(child_file, 'w') as f:
            yaml.dump(child_config, f)
        
        # 加载配置
        config = self.discovery.load_provider_config("openai", "gpt-4")
        
        assert config["provider"] == "openai"
        assert config["base_url"] == "https://api.openai.com/v1"
        assert config["timeout"] == 60  # 应该是子配置的值
        assert config["models"] == ["gpt-4"]
    
    def test_get_all_models(self):
        """测试获取提供商的所有模型"""
        # 创建多个配置文件
        config1 = {
            "provider": "openai",
            "models": ["gpt-4", "gpt-3.5-turbo"]
        }
        config2 = {
            "provider": "openai",
            "models": ["gpt-4o"]
        }
        
        file1 = self.config_dir / "config1.yaml"
        file2 = self.config_dir / "config2.yaml"
        
        with open(file1, 'w') as f:
            yaml.dump(config1, f)
        with open(file2, 'w') as f:
            yaml.dump(config2, f)
        
        # 获取所有模型
        models = self.discovery.get_all_models("openai")
        
        assert set(models) == {"gpt-4", "gpt-3.5-turbo", "gpt-4o"}
    
    def test_reload_configs(self):
        """测试重新加载配置"""
        # 创建配置文件
        config_data = {"provider": "openai", "models": ["gpt-4"]}
        config_file = self.config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 加载配置（会缓存）
        config1 = self.discovery.load_provider_config("openai", "gpt-4")
        
        # 修改配置文件
        config_data["timeout"] = 60
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 重新加载前应该返回缓存的配置
        config2 = self.discovery.load_provider_config("openai", "gpt-4")
        assert "timeout" not in config2
        
        # 重新加载配置
        self.discovery.reload_configs()
        
        # 重新加载后应该返回新配置
        config3 = self.discovery.load_provider_config("openai", "gpt-4")
        assert config3["timeout"] == 60
    
    def test_extract_provider_from_path(self):
        """测试从路径提取提供商名称"""
        # 测试provider目录结构
        path = Path("configs/llms/provider/openai/config.yaml")
        provider = self.discovery._extract_provider_from_path(path)
        assert provider == "openai"
        
        # 测试文件名提取
        path = Path("configs/llms/openai_config.yaml")
        provider = self.discovery._extract_provider_from_path(path)
        assert provider == "openai"
    
    def test_resolve_env_vars(self):
        """测试解析环境变量"""
        with patch.dict('os.environ', {'TEST_VAR': 'test-value', 'TEST_VAR2': 'default'}):
            # 测试基本环境变量
            result = self.discovery._resolve_env_var("${TEST_VAR}")
            assert result == "test-value"
            
            # 测试带默认值的环境变量
            result = self.discovery._resolve_env_var("${NONEXISTENT:default}")
            assert result == "default"
            
            # 测试非环境变量字符串
            result = self.discovery._resolve_env_var("normal-string")
            assert result == "normal-string"
    
    def test_merge_configs(self):
        """测试配置合并"""
        base = {
            "a": 1,
            "b": {"x": 10, "y": 20},
            "c": "base"
        }
        
        override = {
            "b": {"y": 30, "z": 40},
            "c": "override",
            "d": "new"
        }
        
        merged = self.discovery._merge_configs(base, override)
        
        assert merged["a"] == 1
        assert merged["b"]["x"] == 10
        assert merged["b"]["y"] == 30
        assert merged["b"]["z"] == 40
        assert merged["c"] == "override"
        assert merged["d"] == "new"


if __name__ == "__main__":
    pytest.main([__file__])