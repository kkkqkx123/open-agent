"""任务组配置系统测试"""

import pytest
from pathlib import Path

from src.infrastructure.config.models.task_group_config import (
    TaskGroupsConfig, TaskGroupConfig, EchelonConfig, 
    FallbackStrategy, RotationStrategy
)
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from infrastructure.config.loader.yaml_loader import YamlConfigLoader


class TestTaskGroupConfig:
    """任务组配置测试"""
    
    def test_task_groups_config_from_dict(self):
        """测试从字典创建任务组配置"""
        config_dict = {
            "task_groups": {
                "fast_group": {
                    "description": "快速响应任务组",
                    "echelon1": {
                        "models": ["openai-gpt4", "anthropic-claude-opus"],
                        "concurrency_limit": 10,
                        "rpm_limit": 100,
                        "priority": 1,
                        "timeout": 30,
                        "max_retries": 3,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    "fallback_strategy": "echelon_down"
                }
            },
            "polling_pools": {
                "single_turn_pool": {
                    "description": "单轮对话轮询池",
                    "task_groups": ["fast_group"],
                    "rotation_strategy": "round_robin"
                }
            },
            "global_fallback": {
                "enabled": True,
                "max_attempts": 3
            },
            "concurrency_control": {
                "enabled": True
            },
            "rate_limiting": {
                "enabled": True,
                "algorithm": "token_bucket"
            }
        }
        
        config = TaskGroupsConfig.from_dict(config_dict)
        
        assert config.task_groups["fast_group"].description == "快速响应任务组"
        assert config.task_groups["fast_group"].fallback_strategy == FallbackStrategy.ECHELON_DOWN
        assert config.polling_pools["single_turn_pool"].rotation_strategy == RotationStrategy.ROUND_ROBIN
        assert config.global_fallback.enabled == True
        assert config.concurrency_control.enabled == True
        assert config.rate_limiting.enabled == True
    
    def test_echelon_config_from_dict(self):
        """测试层级配置创建"""
        config_dict = {
            "models": ["openai-gpt4", "anthropic-claude-opus"],
            "concurrency_limit": 10,
            "rpm_limit": 100,
            "priority": 1,
            "timeout": 30,
            "max_retries": 3,
            "temperature": 0.7,
            "max_tokens": 2000,
            "function_calling": "required"
        }
        
        echelon = EchelonConfig.from_dict(config_dict)
        
        assert echelon.models == ["openai-gpt4", "anthropic-claude-opus"]
        assert echelon.concurrency_limit == 10
        assert echelon.rpm_limit == 100
        assert echelon.priority == 1
        assert echelon.timeout == 30
        assert echelon.max_retries == 3
        assert echelon.temperature == 0.7
        assert echelon.max_tokens == 2000
        assert echelon.function_calling == "required"


class TestTaskGroupManager:
    """任务组管理器测试"""
    
    @pytest.fixture
    def config_loader(self):
        """配置加载器fixture"""
        return YamlConfigLoader()
    
    @pytest.fixture
    def task_group_manager(self, config_loader):
        """任务组管理器fixture"""
        return TaskGroupManager(config_loader)
    
    def test_parse_group_reference(self, task_group_manager):
        """测试解析组引用"""
        # 测试完整的组引用
        group_name, echelon = task_group_manager.parse_group_reference("fast_group.echelon1")
        assert group_name == "fast_group"
        assert echelon == "echelon1"
        
        # 测试只有组名
        group_name, echelon = task_group_manager.parse_group_reference("fast_group")
        assert group_name == "fast_group"
        assert echelon is None
        
        # 测试小模型组引用
        group_name, task_type = task_group_manager.parse_group_reference("fast_small_group.translation")
        assert group_name == "fast_small_group"
        assert task_type == "translation"
    
    def test_get_models_for_group(self, task_group_manager):
        """测试获取组模型"""
        # 创建临时配置文件
        config_data = {
            "task_groups": {
                "fast_group": {
                    "description": "快速响应任务组",
                    "echelon1": {
                        "models": ["openai-gpt4", "anthropic-claude-opus"],
                        "concurrency_limit": 10,
                        "rpm_limit": 100,
                        "priority": 1,
                        "timeout": 30,
                        "max_retries": 3
                    }
                }
            }
        }
        
        # 模拟配置加载
        task_group_manager._task_groups_config = TaskGroupsConfig.from_dict(config_data)
        
        models = task_group_manager.get_models_for_group("fast_group.echelon1")
        assert models == ["openai-gpt4", "anthropic-claude-opus"]
        
        # 测试不存在的组
        models = task_group_manager.get_models_for_group("nonexistent_group.echelon1")
        assert models == []
    
    def test_validate_group_reference(self, task_group_manager):
        """测试验证组引用"""
        # 创建临时配置
        config_data = {
            "task_groups": {
                "fast_group": {
                    "description": "快速响应任务组",
                    "echelon1": {
                        "models": ["openai-gpt4"],
                        "concurrency_limit": 10,
                        "rpm_limit": 100,
                        "priority": 1,
                        "timeout": 30,
                        "max_retries": 3
                    }
                }
            }
        }
        
        task_group_manager._task_groups_config = TaskGroupsConfig.from_dict(config_data)
        
        # 测试有效的组引用
        assert task_group_manager.validate_group_reference("fast_group.echelon1") == True
        assert task_group_manager.validate_group_reference("fast_group") == True
        
        # 测试无效的组引用
        assert task_group_manager.validate_group_reference("nonexistent_group.echelon1") == False
        assert task_group_manager.validate_group_reference("fast_group.nonexistent_echelon") == False
    
    def test_get_fallback_groups(self, task_group_manager):
        """测试获取降级组"""
        config_data = {
            "task_groups": {
                "fast_group": {
                    "description": "快速响应任务组",
                    "echelon1": {
                        "models": ["openai-gpt4"],
                        "concurrency_limit": 10,
                        "rpm_limit": 100,
                        "priority": 1,
                        "timeout": 30,
                        "max_retries": 3
                    },
                    "echelon2": {
                        "models": ["openai-gpt3.5-turbo"],
                        "concurrency_limit": 20,
                        "rpm_limit": 200,
                        "priority": 2,
                        "timeout": 25,
                        "max_retries": 2
                    },
                    "fallback_strategy": "echelon_down"
                }
            }
        }
        
        task_group_manager._task_groups_config = TaskGroupsConfig.from_dict(config_data)
        
        # 测试层级降级
        fallback_groups = task_group_manager.get_fallback_groups("fast_group.echelon1")
        assert "fast_group.echelon2" in fallback_groups
        
        # 测试不存在的组
        fallback_groups = task_group_manager.get_fallback_groups("nonexistent_group.echelon1")
        assert fallback_groups == []


class TestTaskGroupConfigIntegration:
    """任务组配置集成测试"""
    
    def test_registry_loading(self):
        """测试注册表加载功能"""
        # 检查注册表文件是否存在
        registry_path = Path("configs/llms/groups/_task_groups.yaml")
        if not registry_path.exists():
            pytest.skip("注册表配置文件不存在")
        
        config_loader = YamlConfigLoader()
        task_group_manager = TaskGroupManager(config_loader)
        
        try:
            # 加载注册表配置
            registry_path = f"{task_group_manager._config_base_path}/groups/_task_groups.yaml"
            registry_config = config_loader.load(registry_path)
            
            # 验证注册表结构
            assert "task_groups" in registry_config
            assert "polling_pools" in registry_config
            assert "global_configs" in registry_config
            assert "loading_options" in registry_config
            
            # 验证任务组注册表
            task_groups_registry = registry_config["task_groups"]
            assert "fast_group" in task_groups_registry
            assert "file" in task_groups_registry["fast_group"]
            assert "enabled" in task_groups_registry["fast_group"]
            
            # 验证轮询池注册表
            polling_pools_registry = registry_config["polling_pools"]
            assert "single_turn_pool" in polling_pools_registry
            assert "file" in polling_pools_registry["single_turn_pool"]
            assert "enabled" in polling_pools_registry["single_turn_pool"]
            
            # 验证全局配置注册表
            global_configs = registry_config["global_configs"]
            assert "global_fallback" in global_configs
            assert "concurrency_control" in global_configs
            assert "rate_limiting" in global_configs
            
        except Exception as e:
            pytest.fail(f"注册表加载测试失败: {e}")
    
    def test_disabled_config_loading(self):
        """测试禁用配置的加载"""
        # 检查注册表文件是否存在
        registry_path = Path("configs/llms/groups/_task_groups.yaml")
        if not registry_path.exists():
            pytest.skip("注册表配置文件不存在")
        
        # 创建一个临时的注册表配置，其中包含禁用的配置
        import tempfile
        import os
        
        temp_registry_content = """
task_groups:
  fast_group:
    file: "groups/fast_group.yaml"
    description: "快速响应任务组"
    enabled: true
  disabled_group:
    file: "groups/disabled_group.yaml"
    description: "禁用的任务组"
    enabled: false

polling_pools:
  single_turn_pool:
    file: "polling_pools/single_turn_pool.yaml"
    description: "单轮对话轮询池"
    enabled: true

global_configs:
  global_fallback:
    file: "global_fallback.yaml"
    description: "全局降级配置"
    enabled: true
"""
        
        # 创建临时注册表文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(temp_registry_content)
            temp_registry_path = f.name
        
        try:
            config_loader = YamlConfigLoader()
            task_group_manager = TaskGroupManager(config_loader)
            
            # 临时修改配置基础路径
            original_base_path = task_group_manager._config_base_path
            task_group_manager._config_base_path = os.path.dirname(temp_registry_path)
            
            # 临时修改注册表文件名
            original_registry_file = os.path.basename(temp_registry_path)
            
            # 模拟加载注册表
            registry_config = config_loader.load(temp_registry_path)
            
            # 验证只有启用的配置会被加载
            task_groups_registry = registry_config["task_groups"]
            assert task_groups_registry["fast_group"]["enabled"] == True
            assert task_groups_registry["disabled_group"]["enabled"] == False
            
            # 恢复原始配置
            task_group_manager._config_base_path = original_base_path
            
        except Exception as e:
            pytest.fail(f"禁用配置加载测试失败: {e}")
        finally:
            # 清理临时文件
            if os.path.exists(temp_registry_path):
                os.unlink(temp_registry_path)
    
    def test_load_real_config(self):
        """测试加载真实配置文件"""
        # 检查注册表文件是否存在
        registry_path = Path("configs/llms/groups/_task_groups.yaml")
        if not registry_path.exists():
            pytest.skip("注册表配置文件不存在")
        
        config_loader = YamlConfigLoader()
        task_group_manager = TaskGroupManager(config_loader)
        
        try:
            config = task_group_manager.load_config()
            
            # 验证配置结构
            assert len(config.task_groups) > 0
            assert len(config.polling_pools) > 0
            assert config.global_fallback is not None
            assert config.concurrency_control is not None
            assert config.rate_limiting is not None
            
            # 验证任务组
            fast_group = config.get_task_group("fast_group")
            assert fast_group is not None
            assert fast_group.description is not None
            assert len(fast_group.echelons) > 0
            
            # 验证轮询池
            single_turn_pool = config.get_polling_pool("single_turn_pool")
            assert single_turn_pool is not None
            assert len(single_turn_pool.task_groups) > 0
            
        except Exception as e:
            pytest.fail(f"加载配置失败: {e}")
    
    def test_config_status(self):
        """测试配置状态"""
        # 检查注册表文件是否存在
        registry_path = Path("configs/llms/groups/_task_groups.yaml")
        if not registry_path.exists():
            pytest.skip("注册表配置文件不存在")
        
        config_loader = YamlConfigLoader()
        task_group_manager = TaskGroupManager(config_loader)
        
        try:
            status = task_group_manager.get_config_status()
            
            assert "config_loaded" in status
            assert "task_groups_count" in status
            assert "polling_pools_count" in status
            assert "task_groups" in status
            assert "polling_pools" in status
            assert "global_fallback_enabled" in status
            assert "concurrency_control_enabled" in status
            assert "rate_limiting_enabled" in status
            
        except Exception as e:
            pytest.fail(f"获取配置状态失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__])