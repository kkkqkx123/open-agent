#!/usr/bin/env python3
"""调试配置系统中的timeout参数问题"""

import os
import sys
import tempfile
import shutil
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.config.config_system import ConfigSystem
from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.config.config_merger import ConfigMerger
from src.infrastructure.config.config_validator import ConfigValidator

def main():
    """主函数"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    configs_dir = Path(temp_dir) / "configs"
    configs_dir.mkdir()
    
    try:
        # 创建provider目录结构
        openai_provider_dir = configs_dir / "llms" / "provider" / "openai"
        openai_provider_dir.mkdir(parents=True)
        
        # 创建provider common配置文件
        openai_common_config = {
            "model_type": "openai",
            "provider": "openai",
            "supports_caching": False,
            "default_parameters": {
                "temperature": 0.7,
                "max_tokens": 200,
                "timeout": 30
            },
            "cache_config": {
                "ttl_seconds": 1800,
                "max_size": 500
            },
            "fallback_config": {
                "enabled": True,
                "max_attempts": 3
            }
        }
        
        with open(openai_provider_dir / "common.yaml", "w") as f:
            yaml.dump(openai_common_config, f)
        
        # 创建具体的provider配置文件
        openai_gpt4_config = {
            "model_name": "gpt-4",
            "api_key": "${AGENT_OPENAI_KEY}",
            "parameters": {
                "temperature": 0.3,  # 覆盖common配置
            },
            "supports_caching": False,  # 覆盖common配置
            "cache_config": {
                "ttl_seconds": 3600  # 部分覆盖common配置
            }
        }
        
        with open(openai_provider_dir / "openai-gpt4.yaml", "w") as f:
            yaml.dump(openai_gpt4_config, f)
        
        # 初始化配置系统
        config_loader = YamlConfigLoader(str(configs_dir))
        config_merger = ConfigMerger()
        config_validator = ConfigValidator()
        
        config_system = ConfigSystem(
            config_loader=config_loader,
            config_merger=config_merger,
            config_validator=config_validator,
            base_path=str(configs_dir),
        )
        
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_openai_key"
        
        # 加载配置
        llm_config = config_system.load_llm_config("openai-gpt4")
        
        # 调试输出
        print("=== 调试配置系统中的timeout参数 ===")
        print(f"model_type: {llm_config.model_type}")
        print(f"model_name: {llm_config.model_name}")
        print(f"provider: {llm_config.provider}")
        print(f"parameters: {llm_config.parameters}")
        print(f"timeout_config: {llm_config.timeout_config}")
        print(f"get_parameter('timeout'): {llm_config.get_parameter('timeout')}")
        print(f"get_parameter('temperature'): {llm_config.get_parameter('temperature')}")
        print(f"get_parameter('max_tokens'): {llm_config.get_parameter('max_tokens')}")
        
        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()