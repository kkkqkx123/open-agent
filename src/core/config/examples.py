"""
配置系统使用示例
"""

import os
from pathlib import Path
from typing import Dict, Any

from .config_manager import ConfigManager
from .models import ConfigType, LLMConfig, ToolConfig, ToolSetConfig
from .exceptions import ConfigError


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 创建配置管理器
    manager = ConfigManager()
    
    # 加载LLM配置
    try:
        llm_config = manager.load_config("llms/openai/gpt-4.yaml")
        print(f"LLM配置: {llm_config.get('name', 'unknown')}")
        print(f"提供商: {llm_config.get('provider', 'unknown')}")
        print(f"模型: {llm_config.get('model', 'unknown')}")
    except ConfigError as e:
        print(f"加载LLM配置失败: {e}")
    
    # 加载工具配置
    try:
        tool_config = manager.load_config("tools/calculator.yaml")
        print(f"工具配置: {tool_config.get('name', 'unknown')}")
        print(f"工具类型: {tool_config.get('type', 'unknown')}")
    except ConfigError as e:
        print(f"加载工具配置失败: {e}")


def example_config_model():
    """配置模型使用示例"""
    print("\n=== 配置模型使用示例 ===")
    
    manager = ConfigManager()
    
    # 加载LLM配置模型
    try:
        llm_model = manager.load_config_model("llms/openai/gpt-4.yaml", LLMConfig)
        print(f"LLM模型名称: {llm_model.name}")
        print(f"LLM提供商: {llm_model.provider}")
        print(f"LLM模型: {llm_model.model}")
        print(f"温度参数: {llm_model.temperature}")
        print(f"最大token数: {llm_model.max_tokens}")
    except ConfigError as e:
        print(f"加载LLM模型失败: {e}")
    
    # 加载工具配置模型
    try:
        tool_model = manager.load_config_model("tools/calculator.yaml", ToolConfig)
        print(f"工具模型名称: {tool_model.name}")
        print(f"工具类型: {tool_model.type}")
        print(f"工具描述: {tool_model.description}")
        print(f"是否启用: {tool_model.enabled}")
    except ConfigError as e:
        print(f"加载工具模型失败: {e}")


def example_inheritance():
    """配置继承示例"""
    print("\n=== 配置继承示例 ===")
    
    manager = ConfigManager()
    
    # 假设有一个基础配置和继承配置
    try:
        # 加载继承配置
        inherited_config = manager.load_config("llms/openai/gpt-4-inherited.yaml")
        print(f"继承配置名称: {inherited_config.get('name', 'unknown')}")
        
        # 检查继承的字段
        if 'inherits_from' in inherited_config:
            print(f"继承自: {inherited_config['inherits_from']}")
        
        # 显示合并后的配置
        print("合并后的配置字段:")
        for key, value in inherited_config.items():
            if key != 'inherits_from':
                print(f"  {key}: {value}")
                
    except ConfigError as e:
        print(f"处理继承配置失败: {e}")


def example_environment_variables():
    """环境变量解析示例"""
    print("\n=== 环境变量解析示例 ===")
    
    manager = ConfigManager()
    
    # 设置测试环境变量
    os.environ['TEST_API_KEY'] = 'test-key-123'
    os.environ['TEST_TIMEOUT'] = '30'
    
    # 创建测试配置
    test_config = {
        'name': 'test_config',
        'type': 'llm',
        'provider': 'openai',
        'model': 'gpt-4',
        'api_key': '${TEST_API_KEY}',
        'timeout': '${TEST_TIMEOUT:60}',  # 带默认值
        'base_url': '${TEST_BASE_URL:https://api.openai.com}'  # 环境变量不存在时使用默认值
    }
    
    # 处理配置
    processed_config = manager.process_config(test_config)
    
    print("原始配置:")
    for key, value in test_config.items():
        print(f"  {key}: {value}")
    
    print("处理后的配置:")
    for key, value in processed_config.items():
        print(f"  {key}: {value}")
    
    # 清理测试环境变量
    if 'TEST_API_KEY' in os.environ:
        del os.environ['TEST_API_KEY']
    if 'TEST_TIMEOUT' in os.environ:
        del os.environ['TEST_TIMEOUT']


def example_config_registration():
    """配置注册示例"""
    print("\n=== 配置注册示例 ===")
    
    manager = ConfigManager()
    
    # 注册配置
    try:
        manager.register_config("my_llm", "llms/openai/gpt-4.yaml", ConfigType.LLM)
        manager.register_config("my_tool", "tools/calculator.yaml", ConfigType.TOOL)
        manager.register_config("my_tool_set", "tool-sets/development.yaml", ConfigType.TOOL_SET)
        
        print("配置注册成功!")
        
        # 获取已注册的配置
        llm_config = manager.get_registered_config("my_llm")
        if llm_config and isinstance(llm_config, LLMConfig):
            print(f"已注册LLM配置: {llm_config.name}")
        
        # 按类型列出配置
        llm_configs = manager.get_registered_configs_by_type(ConfigType.LLM)
        print(f"LLM配置列表: {llm_configs}")
        
        tool_configs = manager.get_registered_configs_by_type(ConfigType.TOOL)
        print(f"工具配置列表: {tool_configs}")
        
    except ConfigError as e:
        print(f"配置注册失败: {e}")


def example_config_validation():
    """配置验证示例"""
    print("\n=== 配置验证示例 ===")
    
    manager = ConfigManager()
    
    # 测试有效配置
    valid_config = {
        'name': 'test_llm',
        'type': 'llm',
        'provider': 'openai',
        'model': 'gpt-4',
        'temperature': 0.7,
        'max_tokens': 2048
    }
    
    try:
        is_valid = manager.validate_config(valid_config, ConfigType.LLM)
        print(f"配置验证结果: {'有效' if is_valid else '无效'}")
    except ConfigError as e:
        print(f"配置验证失败: {e}")
    
    # 测试无效配置
    invalid_config = {
        'name': 'test_llm',
        'type': 'llm',
        'provider': 'invalid_provider',  # 无效的提供商
        'model': 'gpt-4'
    }
    
    try:
        is_valid = manager.validate_config(invalid_config, ConfigType.LLM)
        print(f"无效配置验证结果: {'有效' if is_valid else '无效'}")
    except ConfigError as e:
        print(f"无效配置验证失败: {e}")


def example_config_listing():
    """配置列表示例"""
    print("\n=== 配置列表示例 ===")
    
    manager = ConfigManager()
    
    # 列出所有配置文件
    all_configs = manager.list_config_files()
    print(f"所有配置文件: {len(all_configs)} 个")
    for config in all_configs[:5]:  # 只显示前5个
        print(f"  {config}")
    
    # 列出特定目录的配置
    llm_configs = manager.list_config_files("llms")
    print(f"LLM配置文件: {len(llm_configs)} 个")
    for config in llm_configs[:3]:
        print(f"  {config}")
    
    # 列出工具配置
    tool_configs = manager.list_config_files("tools")
    print(f"工具配置文件: {len(tool_configs)} 个")
    for config in tool_configs[:3]:
        print(f"  {config}")


def example_config_info():
    """配置信息示例"""
    print("\n=== 配置信息示例 ===")
    
    manager = ConfigManager()
    
    # 获取配置信息
    try:
        config_info = manager.get_config_info("llms/openai/gpt-4.yaml")
        
        print("配置信息:")
        print(f"  路径: {config_info['path']}")
        print(f"  名称: {config_info['name']}")
        print(f"  类型: {config_info['type']}")
        print(f"  存在: {config_info['exists']}")
        
        if 'error' in config_info:
            print(f"  错误: {config_info['error']}")
        
        if 'inherits_from' in config_info:
            print(f"  继承自: {config_info['inherits_from']}")
            
    except ConfigError as e:
        print(f"获取配置信息失败: {e}")


def example_config_export():
    """配置导出示例"""
    print("\n=== 配置导出示例 ===")
    
    manager = ConfigManager()
    
    # 导出配置为JSON
    try:
        output_path = "/tmp/exported_config.json"
        manager.export_config("llms/openai/gpt-4.yaml", output_path, "json")
        print(f"配置已导出到: {output_path}")
        
        # 导出配置为YAML
        output_path = "/tmp/exported_config.yaml"
        manager.export_config("llms/openai/gpt-4.yaml", output_path, "yaml")
        print(f"配置已导出到: {output_path}")
        
    except ConfigError as e:
        print(f"配置导出失败: {e}")


def example_config_template():
    """配置模板示例"""
    print("\n=== 配置模板示例 ===")
    
    manager = ConfigManager()
    
    # 创建LLM配置模板
    try:
        output_path = "/tmp/llm_config_template.yaml"
        manager.create_config_template(ConfigType.LLM, output_path)
        print(f"LLM配置模板已创建: {output_path}")
        
        # 创建工具配置模板
        output_path = "/tmp/tool_config_template.yaml"
        manager.create_config_template(ConfigType.TOOL, output_path)
        print(f"工具配置模板已创建: {output_path}")
        
        # 创建工具集配置模板
        output_path = "/tmp/tool_set_config_template.yaml"
        manager.create_config_template(ConfigType.TOOL_SET, output_path)
        print(f"工具集配置模板已创建: {output_path}")
        
    except ConfigError as e:
        print(f"创建配置模板失败: {e}")


def run_all_examples():
    """运行所有示例"""
    print("开始运行配置系统示例...")
    
    try:
        example_basic_usage()
        example_config_model()
        example_inheritance()
        example_environment_variables()
        example_config_registration()
        example_config_validation()
        example_config_listing()
        example_config_info()
        example_config_export()
        example_config_template()
        
        print("\n=== 所有示例运行完成 ===")
        
    except Exception as e:
        print(f"运行示例时出错: {e}")


if __name__ == "__main__":
    run_all_examples()